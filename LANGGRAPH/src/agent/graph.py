"""Self-aware, retrieval-enabled LangGraph agent scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from agent.api_catalog import render_api_catalog
from agent.memory import (
    FileMemoryStore,
    SelfState,
    SessionSummary,
    assess_comprehension,
    build_reasoning_outline,
    extract_memory_updates,
    infer_intent,
    render_memory_context,
)
from agent.openharness_bridge import append_topic_note
from agent.owt_bridge import OwtUnavailableError, add_recall_fact, add_topic_memory, search_recall
from agent.retrieval import render_retrieval_results, retrieve_relevant_memories
from agent.telemetry import trace_span


class Context(TypedDict, total=False):
    user_id: str
    enable_memory: bool
    memory_namespace: str
    self_awareness: bool
    mirror_to_openharness: bool
    use_open_orchestrator_memory: bool
    open_orchestrator_repo_root: str


@dataclass
class State:
    message: str = ""
    response: str = ""
    memory_context: str = ""
    retrieved_context: str = ""
    memory_updates: dict[str, str] = field(default_factory=dict)
    intent: str = ""
    comprehension: str = ""
    reasoning_outline: list[str] = field(default_factory=list)
    self_state: dict[str, Any] = field(default_factory=dict)
    session_summary: str = ""


async def call_model(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    context = runtime.context or {}
    namespace = context.get("memory_namespace") or context.get("user_id") or "default"

    with trace_span("agent_call", {"namespace": namespace}):
        store = FileMemoryStore(namespace=namespace)
        updates = extract_memory_updates(state.message)
        intent = infer_intent(state.message)

        if context.get("enable_memory", True):
            for key, value in updates.items():
                store.upsert(key, value, source=context.get("user_id", "anonymous"))
                if context.get("mirror_to_openharness", True):
                    append_topic_note(f"langgraph-{namespace}-{key}", f"# {key}\n\n- value: {value}\n- source: {context.get('user_id', 'anonymous')}\n")
                if context.get("use_open_orchestrator_memory"):
                    try:
                        add_topic_memory(
                            name=f"{namespace} {key}",
                            fact=f"{key}: {value}",
                            repo_root=context.get("open_orchestrator_repo_root"),
                        )
                        add_recall_fact(
                            content=f"{key}: {value}",
                            category="agent-memory",
                            worktree=namespace,
                            source=context.get("user_id", "anonymous"),
                        )
                    except OwtUnavailableError:
                        pass

        self_state = store.load_self_state() if context.get("self_awareness", True) else SelfState(
            identity="Self-awareness disabled",
            capabilities=[],
            limitations=[],
            operating_principles=[],
            updated_at=datetime.now(UTC).isoformat(),
        )
        memory_context = render_memory_context(store) if context.get("enable_memory", True) else "Memory disabled."
        retrieved = retrieve_relevant_memories(store, state.message)
        retrieved_context = render_retrieval_results(retrieved)
        if context.get("use_open_orchestrator_memory"):
            try:
                owt_results = search_recall(state.message)
                if owt_results:
                    retrieved_context += "\nOWT recall:\n" + "\n".join(
                        f"- {item.content} [{item.worktree}/{item.category}]" for item in owt_results
                    )
            except OwtUnavailableError:
                pass
        comprehension = assess_comprehension(state.message, updates)
        reasoning_outline = build_reasoning_outline(intent, len(store.list_records()), self_state.identity)
        reasoning_outline.append(f"Retrieved {len(retrieved)} relevant memory matches")

        if "api" in state.message.lower() and ("catalog" in state.message.lower() or "tool" in state.message.lower()):
            response = "Verified no-auth API catalog:\n" + render_api_catalog()
        elif intent == "self_reflection":
            response = (
                f"Identity: {self_state.identity}\n"
                f"Capabilities: {', '.join(self_state.capabilities) or 'none'}\n"
                f"Limitations: {', '.join(self_state.limitations) or 'none'}\n"
                f"Principles: {', '.join(self_state.operating_principles) or 'none'}"
            )
        elif updates:
            remembered = ", ".join(f"{key}={value}" for key, value in updates.items())
            response = (
                f"Stored memory: {remembered}.\n"
                f"Relevant memory:\n{retrieved_context}\n"
                f"Known memory:\n{memory_context}"
            )
        else:
            response = (
                f"You said: {state.message}\n"
                f"Understanding: {comprehension}\n"
                f"Relevant memory:\n{retrieved_context}\n"
                f"Known memory:\n{memory_context}"
            )

        summary = SessionSummary(
            summary=f"Intent={intent}; updates={len(updates)}; memory_records={len(store.list_records())}; retrieved={len(retrieved)}",
            last_user_message=state.message,
            last_agent_response=response,
            updated_at=datetime.now(UTC).isoformat(),
        )
        store.save_session_summary(summary)

        return {
            "response": response,
            "memory_context": memory_context,
            "retrieved_context": retrieved_context,
            "memory_updates": updates,
            "intent": intent,
            "comprehension": comprehension,
            "reasoning_outline": reasoning_outline,
            "self_state": self_state.__dict__,
            "session_summary": summary.summary,
        }


graph = (
    StateGraph(State, context_schema=Context)
    .add_node(call_model)
    .add_edge("__start__", "call_model")
    .compile(name="Self Aware Retrieval Agent")
)
