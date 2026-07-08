"""
elite_goals.py — Autonomous Goal Management for Vision
========================================================
Enables the system to set, pursue, and complete goals autonomously.

Key Capabilities:
  1. GOAL HIERARCHY     — Decompose high-level goals into actionable sub-goals
  2. PLANNING ENGINE    — Generate and execute multi-step plans
  3. PROGRESS TRACKING — Monitor goal completion and adapt plans
  4. INTENTION STACK   — Manage active intentions and context switching
  5. ACHIEVEMENT SYSTEM — Learn from completed goals to improve future planning

Architecture
------------
  GoalManager
    ├─ GoalGraph        ← hierarchical goal decomposition
    ├─ PlanEngine       ← plan generation and execution
    ├─ ProgressTracker  ← completion monitoring
    ├─ IntentionStack   ← active context management
    └─ AchievementLog   ← learning from successes/failures
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

GOALS_DATA_DIR = Path(__file__).parent / ".brain" / "goals"
MAX_ACTIVE_GOALS = 5
MAX_GOAL_DEPTH = 4
PLAN_TIMEOUT_SECONDS = 300
INTENTION_STACK_SIZE = 10


class GoalStatus(Enum):
    """Goal lifecycle states."""

    PENDING = auto()
    ACTIVE = auto()
    BLOCKED = auto()
    COMPLETED = auto()
    FAILED = auto()
    ABANDONED = auto()


class GoalPriority(Enum):
    """Priority levels for goal scheduling."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


@dataclass
class Goal:
    """Represents a single goal with metadata."""

    uid: str
    description: str
    status: GoalStatus
    priority: GoalPriority
    created_at: float
    deadline: float | None = None
    parent_uid: str | None = None
    subgoal_uids: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    estimated_effort: int = 1  # in arbitrary units
    actual_effort: int = 0
    completion_criteria: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    outcome: str | None = None
    learnings: list[str] = field(default_factory=list)


@dataclass
class PlanStep:
    """A single step in a plan."""

    uid: str
    description: str
    tool: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: GoalStatus = GoalStatus.PENDING
    result: str | None = None
    duration_ms: float = 0.0


@dataclass
class Plan:
    """A plan to achieve a goal."""

    uid: str
    goal_uid: str
    steps: list[PlanStep]
    created_at: float
    started_at: float | None = None
    completed_at: float | None = None
    success_rate: float = 1.0  # estimated based on similar past plans


class GoalGraph:
    """
    Manages hierarchical goal relationships and persistence.
    """

    def __init__(self, data_dir: Path = GOALS_DATA_DIR) -> None:
        self.data_dir = data_dir
        self.goals: dict[str, Goal] = {}
        self._load()

    def _load(self) -> None:
        """Load goals from disk."""
        goals_file = self.data_dir / "goals.json"
        if not goals_file.exists():
            return
        try:
            data = json.loads(goals_file.read_text(encoding="utf-8"))
            for g in data:
                self.goals[g["uid"]] = Goal(
                    uid=g["uid"],
                    description=g["description"],
                    status=GoalStatus[g["status"]],
                    priority=GoalPriority[g["priority"]],
                    created_at=g["created_at"],
                    deadline=g.get("deadline"),
                    parent_uid=g.get("parent_uid"),
                    subgoal_uids=g.get("subgoal_uids", []),
                    required_tools=g.get("required_tools", []),
                    estimated_effort=g.get("estimated_effort", 1),
                    actual_effort=g.get("actual_effort", 0),
                    completion_criteria=g.get("completion_criteria", []),
                    context=g.get("context", {}),
                    outcome=g.get("outcome"),
                    learnings=g.get("learnings", []),
                )
            logger.info("GoalGraph loaded %d goals", len(self.goals))
        except Exception as exc:
            logger.warning("GoalGraph load error: %s", exc)

    def save(self) -> None:
        """Persist goals to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = []
        for g in self.goals.values():
            data.append(
                {
                    "uid": g.uid,
                    "description": g.description,
                    "status": g.status.name,
                    "priority": g.priority.name,
                    "created_at": g.created_at,
                    "deadline": g.deadline,
                    "parent_uid": g.parent_uid,
                    "subgoal_uids": g.subgoal_uids,
                    "required_tools": g.required_tools,
                    "estimated_effort": g.estimated_effort,
                    "actual_effort": g.actual_effort,
                    "completion_criteria": g.completion_criteria,
                    "context": g.context,
                    "outcome": g.outcome,
                    "learnings": g.learnings,
                }
            )
        goals_file = self.data_dir / "goals.json"
        goals_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def create_goal(
        self,
        description: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
        parent_uid: str | None = None,
        deadline: float | None = None,
        required_tools: list[str] | None = None,
        completion_criteria: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Goal:
        """Create a new goal."""
        uid = f"goal_{int(time.time() * 1000)}_{hash(description) % 10000}"
        goal = Goal(
            uid=uid,
            description=description,
            status=GoalStatus.PENDING,
            priority=priority,
            created_at=time.time(),
            deadline=deadline,
            parent_uid=parent_uid,
            required_tools=required_tools or [],
            completion_criteria=completion_criteria or [],
            context=context or {},
        )
        self.goals[uid] = goal
        if parent_uid and parent_uid in self.goals:
            self.goals[parent_uid].subgoal_uids.append(uid)
        self.save()
        return goal

    def get_active_goals(self) -> list[Goal]:
        """Get all currently active goals."""
        return [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]

    def get_pending_goals(self) -> list[Goal]:
        """Get pending goals sorted by priority."""
        pending = [g for g in self.goals.values() if g.status == GoalStatus.PENDING]
        return sorted(pending, key=lambda g: g.priority.value, reverse=True)

    def get_goal_tree(self, root_uid: str) -> dict[str, Any]:
        """Get hierarchical view of a goal and its subgoals."""
        if root_uid not in self.goals:
            return {}
        goal = self.goals[root_uid]
        return {
            "uid": goal.uid,
            "description": goal.description,
            "status": goal.status.name,
            "priority": goal.priority.name,
            "subgoals": [self.get_goal_tree(uid) for uid in goal.subgoal_uids],
        }

    def update_status(self, uid: str, status: GoalStatus) -> None:
        """Update goal status and propagate to parent if needed."""
        if uid not in self.goals:
            return
        self.goals[uid].status = status
        if status in (GoalStatus.COMPLETED, GoalStatus.FAILED):
            self.goals[uid].outcome = status.name.lower()
            # Check if parent should be updated
            parent_uid = self.goals[uid].parent_uid
            if parent_uid and parent_uid in self.goals:
                self._check_parent_completion(parent_uid)
        self.save()

    def _check_parent_completion(self, parent_uid: str) -> None:
        """Check if all subgoals are done and update parent status."""
        parent = self.goals[parent_uid]
        if not parent.subgoal_uids:
            return
        subgoals = [self.goals.get(uid) for uid in parent.subgoal_uids]
        subgoals = [g for g in subgoals if g]
        if all(g.status == GoalStatus.COMPLETED for g in subgoals):
            parent.status = GoalStatus.COMPLETED
            parent.outcome = "All subgoals completed"
        elif any(g.status == GoalStatus.FAILED for g in subgoals):
            parent.status = GoalStatus.FAILED
            parent.outcome = "One or more subgoals failed"

    def update_temporal_priorities(self) -> None:
        """Scan pending goals and escalate priority if deadlines are near."""
        now = time.time()
        updated = False
        for goal in self.goals.values():
            if goal.status == GoalStatus.PENDING and goal.deadline:
                time_remaining = goal.deadline - now
                if time_remaining <= 0:
                    goal.status = GoalStatus.FAILED
                    goal.outcome = "Failed: Missed deadline"
                    logger.warning(f"Goal {goal.uid} failed: deadline passed")
                    updated = True
                elif time_remaining <= 300: # 5 minutes
                    if goal.priority.value < GoalPriority.CRITICAL.value:
                        goal.priority = GoalPriority.CRITICAL
                        logger.info(f"Escalated priority of goal {goal.uid} to CRITICAL (deadline in {time_remaining:.0f}s)")
                        updated = True
                elif time_remaining <= 1800: # 30 minutes
                    if goal.priority.value < GoalPriority.HIGH.value:
                        goal.priority = GoalPriority.HIGH
                        logger.info(f"Escalated priority of goal {goal.uid} to HIGH (deadline in {time_remaining:.0f}s)")
                        updated = True
        if updated:
            self.save()


class PlanEngine:
    """
    Generates and executes plans to achieve goals.
    """

    def __init__(self, goal_graph: GoalGraph) -> None:
        self.goal_graph = goal_graph
        self.plans: dict[str, Plan] = {}
        self._llm_fn: Callable | None = None
        self._tool_executor: Callable | None = None

    def set_llm(self, fn: Callable) -> None:
        """Wire in LLM function for plan generation."""
        self._llm_fn = fn

    def set_tool_executor(self, fn: Callable) -> None:
        """Wire in tool execution function."""
        self._tool_executor = fn

    async def generate_plan(self, goal: Goal, use_htn: bool = True) -> Plan | None:
        """Generate a plan to achieve the goal using LLM, with optional HTN decomposition."""
        if self._llm_fn is None:
            return None

        try:
            if use_htn:
                steps = await self.htn_decompose(goal)
            else:
                prompt = self._build_planning_prompt(goal)
                response = await self._llm_fn(prompt, max_tokens=800)
                steps = self._parse_plan_steps(response, goal.uid)

            if steps:
                plan = Plan(
                    uid=f"plan_{int(time.time() * 1000)}",
                    goal_uid=goal.uid,
                    steps=steps,
                    created_at=time.time(),
                )
                self.plans[plan.uid] = plan
                return plan
        except Exception as exc:
            logger.error("Plan generation failed: %s", exc)
        return None

    async def htn_decompose(self, goal: Goal) -> list[PlanStep]:
        """Decompose a compound goal into a network of sub-tasks using HTN planning."""
        if self._llm_fn is None:
            return []

        prompt = self._build_htn_prompt(goal)
        try:
            response = await self._llm_fn(prompt, max_tokens=1000)
            json_str = response.strip()
            if "```" in json_str:
                import re
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", json_str, re.DOTALL | re.IGNORECASE)
                if match:
                    json_str = match.group(1)
            
            data = json.loads(json_str)
            steps = []
            if isinstance(data, list):
                for item in data:
                    uid = item.get("uid") or f"step_{goal.uid}_{len(steps)+1}"
                    steps.append(PlanStep(
                        uid=uid,
                        description=item.get("description", ""),
                        tool=item.get("tool"),
                        tool_args=item.get("tool_args") or {},
                        depends_on=item.get("depends_on") or [],
                    ))
                logger.info(f"HTN decomposed goal {goal.uid} into {len(steps)} steps")
                return steps
        except Exception as exc:
            logger.warning(f"HTN decomposition failed: {exc}, falling back to standard planner")
        
        # Fallback to standard linear planner
        prompt = self._build_planning_prompt(goal)
        response = await self._llm_fn(prompt, max_tokens=800)
        return self._parse_plan_steps(response, goal.uid)

    def _build_htn_prompt(self, goal: Goal) -> str:
        """Build the HTN planning prompt for the LLM."""
        tools_str = ", ".join(goal.required_tools) if goal.required_tools else "any available tools"
        criteria_str = (
            "\n".join(f"- {c}" for c in goal.completion_criteria) if goal.completion_criteria else "- Goal is achieved"
        )
        return f"""You are an HTN (Hierarchical Task Network) planner.
Decompose the following high-level compound task into a network of sub-tasks and primitive operators.

High-Level Goal: {goal.description}
Completion Criteria:
{criteria_str}

Available Tools (Primitive Operators): {tools_str}

Decompose this compound task recursively. For each step in the decomposition, specify:
1. Step UID (e.g., step_1, step_2)
2. Description of the task/action
3. Tool to use (if primitive, e.g. "screenshot", "run_command", or null if compound/no tool)
4. Dependencies (list of step UIDs that MUST be completed before this step can run)

Output the plan in raw JSON format matching this schema:
[
  {{
    "uid": "step_1",
    "description": "Analyze screen state",
    "tool": "screenshot",
    "tool_args": {{}},
    "depends_on": []
  }},
  {{
    "uid": "step_2",
    "description": "Formulate next keyboard inputs",
    "tool": null,
    "tool_args": {{}},
    "depends_on": ["step_1"]
  }}
]

Provide ONLY the valid JSON array and nothing else.
JSON Plan:"""

    def _build_planning_prompt(self, goal: Goal) -> str:
        """Build prompt for plan generation."""
        tools_str = ", ".join(goal.required_tools) if goal.required_tools else "any available tools"
        criteria_str = (
            "\n".join(f"- {c}" for c in goal.completion_criteria) if goal.completion_criteria else "- Goal is achieved"
        )

        return f"""You are a planning assistant. Create a step-by-step plan to achieve this goal.

Goal: {goal.description}

Completion Criteria:
{criteria_str}

Available Tools: {tools_str}

Provide your plan as a numbered list. Each step should be clear and actionable.
If a step requires a tool, specify it in parentheses after the step.

Example format:
1. Analyze the current state (tool: read_screen)
2. Navigate to the target application (tool: click)
3. Execute the main action (tool: type_text)
4. Verify the result (tool: screenshot)

Your plan:"""

    def _parse_plan_steps(self, response: str, goal_uid: str) -> list[PlanStep]:
        """Parse LLM response into plan steps."""
        steps = []
        lines = response.strip().split("\n")
        step_num = 0

        for line in lines:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue

            # Extract step number and content
            parts = line.split(".", 1)
            if len(parts) != 2:
                continue

            content = parts[1].strip()
            if not content:
                continue

            # Extract tool if specified
            tool = None
            tool_args = {}
            if "(tool:" in content.lower():
                import re

                match = re.search(r"\(tool:\s*(\w+)\)", content, re.IGNORECASE)
                if match:
                    tool = match.group(1)
                    content = re.sub(r"\(tool:\s*\w+\)", "", content, flags=re.IGNORECASE).strip()

            step_num += 1
            step = PlanStep(
                uid=f"step_{goal_uid}_{step_num}",
                description=content,
                tool=tool,
                tool_args=tool_args,
            )
            steps.append(step)

        return steps

    async def execute_plan(self, plan: Plan) -> bool:
        """Execute a plan step by step."""
        plan.started_at = time.time()
        goal = self.goal_graph.goals.get(plan.goal_uid)
        if goal:
            self.goal_graph.update_status(goal.uid, GoalStatus.ACTIVE)

        try:
            for step in plan.steps:
                if step.status == GoalStatus.COMPLETED:
                    continue

                step.status = GoalStatus.ACTIVE
                start_time = time.time()

                if step.tool and self._tool_executor:
                    try:
                        result = await self._tool_executor(step.tool, step.tool_args)
                        step.result = str(result)
                        step.status = GoalStatus.COMPLETED
                    except Exception as exc:
                        step.result = f"Error: {exc}"
                        step.status = GoalStatus.FAILED
                        logger.error("Step execution failed: %s", exc)
                        return False
                else:
                    # No tool needed, mark as completed
                    step.status = GoalStatus.COMPLETED

                step.duration_ms = (time.time() - start_time) * 1000

                if goal:
                    goal.actual_effort += 1

            plan.completed_at = time.time()
            if goal:
                self.goal_graph.update_status(goal.uid, GoalStatus.COMPLETED)
            return True

        except Exception as exc:
            logger.error("Plan execution failed: %s", exc)
            if goal:
                self.goal_graph.update_status(goal.uid, GoalStatus.FAILED)
            return False


class IntentionStack:
    """
    Manages the stack of active intentions for context switching.
    """

    def __init__(self, max_size: int = INTENTION_STACK_SIZE) -> None:
        self.stack: deque[dict[str, Any]] = deque(maxlen=max_size)
        self.current_intention: dict[str, Any] | None = None

    def push(self, intention_type: str, data: dict[str, Any]) -> None:
        """Push current context onto stack and set new intention."""
        if self.current_intention:
            self.stack.append(self.current_intention)
        self.current_intention = {
            "type": intention_type,
            "data": data,
            "timestamp": time.time(),
        }

    def pop(self) -> dict[str, Any] | None:
        """Return to previous intention."""
        previous = self.current_intention
        if self.stack:
            self.current_intention = self.stack.pop()
        else:
            self.current_intention = None
        return previous

    def peek(self) -> dict[str, Any] | None:
        """View current intention without changing stack."""
        return self.current_intention

    def get_context_summary(self) -> str:
        """Get summary of current intention stack for LLM context."""
        if not self.current_intention:
            return "No active intention."

        summary = f"Current: {self.current_intention['type']}"
        if self.stack:
            summary += f" | Stack depth: {len(self.stack)}"
        return summary


class GoalManager:
    """
    Main facade for autonomous goal management.
    Integrates all components into a cohesive system.
    """

    def __init__(self) -> None:
        self.graph = GoalGraph()
        self.planner = PlanEngine(self.graph)
        self.intentions = IntentionStack()
        self._running = False
        self._task: asyncio.Task | None = None

    def set_llm(self, fn: Callable) -> None:
        """Wire in LLM function."""
        self.planner.set_llm(fn)

    def set_tool_executor(self, fn: Callable) -> None:
        """Wire in tool executor."""
        self.planner.set_tool_executor(fn)

    async def create_goal(
        self,
        description: str,
        priority: str = "MEDIUM",
        auto_decompose: bool = True,
    ) -> Goal:
        """Create a new goal with optional automatic decomposition."""
        priority_enum = GoalPriority[priority.upper()]
        goal = self.graph.create_goal(
            description=description,
            priority=priority_enum,
        )

        if auto_decompose and self.planner._llm_fn:
            await self._decompose_goal(goal)

        return goal

    async def _decompose_goal(self, goal: Goal) -> None:
        """Automatically decompose a goal into subgoals using LLM."""
        if self.planner._llm_fn is None:
            return

        prompt = f"""Break down this goal into 2-5 concrete sub-goals:

Goal: {goal.description}

Provide each sub-goal on a new line starting with a dash (-).
Make each sub-goal specific and actionable.

Sub-goals:"""

        try:
            response = await self.planner._llm_fn(prompt, max_tokens=300)
            lines = response.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    subgoal_desc = line[1:].strip()
                    if subgoal_desc:
                        self.graph.create_goal(
                            description=subgoal_desc,
                            priority=goal.priority,
                            parent_uid=goal.uid,
                        )
        except Exception as exc:
            logger.warning("Goal decomposition failed: %s", exc)

    async def pursue_goal(self, goal_uid: str) -> bool:
        """Actively pursue a goal by generating and executing a plan."""
        if goal_uid not in self.graph.goals:
            return False

        goal = self.graph.goals[goal_uid]
        self.intentions.push("pursue_goal", {"goal_uid": goal_uid, "description": goal.description})

        # Generate plan
        plan = await self.planner.generate_plan(goal)
        if not plan:
            self.intentions.pop()
            return False

        # Execute plan
        success = await self.planner.execute_plan(plan)
        self.intentions.pop()
        return success

    async def pursue_next_pending(self) -> str | None:
        """Pursue the highest priority pending goal."""
        pending = self.graph.get_pending_goals()
        if not pending:
            return None

        next_goal = pending[0]
        success = await self.pursue_goal(next_goal.uid)
        return next_goal.uid if success else None

    def get_status(self) -> dict[str, Any]:
        """Get current goal management status."""
        return {
            "total_goals": len(self.graph.goals),
            "active": len(self.graph.get_active_goals()),
            "pending": len(self.graph.get_pending_goals()),
            "intention_stack_depth": len(self.intentions.stack),
            "current_intention": self.intentions.get_context_summary(),
        }

    def start_autonomous_loop(self) -> None:
        """Start background autonomous goal pursuit."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._autonomous_loop())
        logger.info("GoalManager autonomous loop started")

    def stop_autonomous_loop(self) -> None:
        """Stop background autonomous goal pursuit."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("GoalManager autonomous loop stopped")

    async def _autonomous_loop(self) -> None:
        """Background loop for autonomous goal pursuit."""
        while self._running:
            try:
                # Temporal Reasoning
                self.graph.update_temporal_priorities()

                # Check for pending goals
                pending = self.graph.get_pending_goals()
                active = self.graph.get_active_goals()

                # Pursue goals if we have capacity
                if pending and len(active) < MAX_ACTIVE_GOALS:
                    await self.pursue_next_pending()

                # Wait before next iteration
                await asyncio.sleep(5.0)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Autonomous loop error: %s", exc)
                await asyncio.sleep(10.0)


# ── Singleton Instance ───────────────────────────────────────────────────────

_goal_manager: GoalManager | None = None


def get_goal_manager() -> GoalManager:
    """Get or create the singleton GoalManager instance."""
    global _goal_manager
    if _goal_manager is None:
        _goal_manager = GoalManager()
    return _goal_manager
