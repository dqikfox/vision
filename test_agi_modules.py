"""
test_agi_modules.py — Test suite for AGI cognitive modules
===========================================================
Tests for elite_goals.py and elite_world.py
"""

import tempfile
import time
from pathlib import Path

import pytest

from elite_goals import (
    GoalGraph,
    GoalManager,
    GoalPriority,
    GoalStatus,
    PlanEngine,
    get_goal_manager,
)
from elite_world import (
    EntityRegistry,
    EntityState,
    EntityType,
    ObservationBuffer,
    SpatialMemory,
    WorldModel,
    get_world_model,
)

# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def goal_graph(temp_data_dir):
    return GoalGraph(data_dir=temp_data_dir)


@pytest.fixture
def entity_registry(temp_data_dir):
    return EntityRegistry(data_dir=temp_data_dir)


@pytest.fixture
def observation_buffer():
    return ObservationBuffer(max_size=100)


@pytest.fixture
def spatial_memory():
    return SpatialMemory()


# ── Goal Management Tests ─────────────────────────────────────────────────────


class TestGoalGraph:
    def test_create_goal(self, goal_graph):
        goal = goal_graph.create_goal(
            description="Test goal",
            priority=GoalPriority.HIGH,
        )
        assert goal.description == "Test goal"
        assert goal.priority == GoalPriority.HIGH
        assert goal.status == GoalStatus.PENDING
        assert goal.uid in goal_graph.goals

    def test_goal_hierarchy(self, goal_graph):
        parent = goal_graph.create_goal("Parent goal", GoalPriority.HIGH)
        child = goal_graph.create_goal(
            "Child goal",
            GoalPriority.MEDIUM,
            parent_uid=parent.uid,
        )
        assert child.parent_uid == parent.uid
        assert child.uid in parent.subgoal_uids

    def test_goal_status_update(self, goal_graph):
        goal = goal_graph.create_goal("Test goal")
        goal_graph.update_status(goal.uid, GoalStatus.ACTIVE)
        assert goal_graph.goals[goal.uid].status == GoalStatus.ACTIVE

    def test_parent_completion(self, goal_graph):
        parent = goal_graph.create_goal("Parent")
        child1 = goal_graph.create_goal("Child 1", parent_uid=parent.uid)
        child2 = goal_graph.create_goal("Child 2", parent_uid=parent.uid)

        goal_graph.update_status(child1.uid, GoalStatus.COMPLETED)
        assert goal_graph.goals[parent.uid].status == GoalStatus.PENDING

        goal_graph.update_status(child2.uid, GoalStatus.COMPLETED)
        assert goal_graph.goals[parent.uid].status == GoalStatus.COMPLETED

    def test_persistence(self, goal_graph, temp_data_dir):
        goal = goal_graph.create_goal("Persistent goal", GoalPriority.CRITICAL)
        goal_graph.save()

        # Create new graph instance
        new_graph = GoalGraph(data_dir=temp_data_dir)
        assert len(new_graph.goals) == 1
        assert new_graph.goals[goal.uid].description == "Persistent goal"
        assert new_graph.goals[goal.uid].priority == GoalPriority.CRITICAL


class TestPlanEngine:
    def test_parse_plan_steps(self, goal_graph):
        engine = PlanEngine(goal_graph)

        response = """1. First step (tool: click)
2. Second step
3. Third step (tool: type_text)"""

        steps = engine._parse_plan_steps(response, "test_goal")
        assert len(steps) == 3
        assert steps[0].description == "First step"
        assert steps[0].tool == "click"
        assert steps[1].tool is None
        assert steps[2].tool == "type_text"


class TestGoalManager:
    @pytest.mark.asyncio
    async def test_create_goal(self):
        manager = GoalManager()
        goal = await manager.create_goal("Test goal", "MEDIUM", auto_decompose=False)
        assert goal.description == "Test goal"
        assert goal.priority == GoalPriority.MEDIUM

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting status with fresh manager."""
        # Use fresh manager to avoid singleton state
        manager = GoalManager()
        goal = await manager.create_goal("Goal 1", "HIGH", auto_decompose=False)
        await manager.create_goal("Goal 2", "LOW", auto_decompose=False)

        status = manager.get_status()
        assert status["total_goals"] == 2
        assert status["pending"] == 2
        assert status["active"] == 0


# ── World Model Tests ─────────────────────────────────────────────────────────


class TestEntityRegistry:
    def test_register_entity(self, entity_registry):
        entity = entity_registry.register(
            name="Chrome",
            entity_type=EntityType.APPLICATION,
            state=EntityState.ACTIVE,
        )
        assert entity.name == "Chrome"
        assert entity.entity_type == EntityType.APPLICATION
        assert entity.state == EntityState.ACTIVE

    def test_update_state(self, entity_registry):
        entity = entity_registry.register("TestApp", EntityType.APPLICATION)
        entity_registry.update_state(entity.uid, EntityState.BUSY, "Processing...")

        updated = entity_registry.entities[entity.uid]
        assert updated.state == EntityState.BUSY
        assert len(updated.history) == 1
        assert updated.history[0]["context"] == "Processing..."

    def test_get_by_type(self, entity_registry):
        entity_registry.register("Chrome", EntityType.APPLICATION)
        entity_registry.register("Firefox", EntityType.APPLICATION)
        entity_registry.register("Document", EntityType.FILE)

        apps = entity_registry.get_by_type(EntityType.APPLICATION)
        assert len(apps) == 2

    def test_persistence(self, entity_registry, temp_data_dir):
        entity = entity_registry.register("Persistent", EntityType.CONCEPT)
        entity_registry.save()

        new_registry = EntityRegistry(data_dir=temp_data_dir)
        assert len(new_registry.entities) == 1
        assert new_registry.entities[entity.uid].name == "Persistent"


class TestObservationBuffer:
    def test_add_observation(self, observation_buffer):
        obs = observation_buffer.add(
            content="Screen shows desktop",
            source="screenshot",
        )
        assert obs.content == "Screen shows desktop"
        assert obs.source == "screenshot"
        assert len(observation_buffer.observations) == 1

    def test_get_recent(self, observation_buffer):
        for i in range(15):
            observation_buffer.add(f"Observation {i}", "test")

        recent = observation_buffer.get_recent(5)
        assert len(recent) == 5
        assert recent[-1].content == "Observation 14"


class TestSpatialMemory:
    def test_record_location(self, spatial_memory):
        spatial_memory.record_location("chrome_icon", 100.0, 200.0)
        loc = spatial_memory.get_location("chrome_icon")
        assert loc == (100.0, 200.0)

    def test_find_nearest(self, spatial_memory):
        spatial_memory.record_location("a", 0.0, 0.0)
        spatial_memory.record_location("b", 50.0, 0.0)
        spatial_memory.record_location("c", 200.0, 0.0)

        nearest = spatial_memory.find_nearest(45.0, 0.0, max_distance=100.0)
        assert len(nearest) == 2
        assert nearest[0][0] == "b"  # Closest


class TestWorldModel:
    @pytest.mark.asyncio
    async def test_observe(self):
        world = WorldModel()
        obs = await world.observe("Screen captured", "screenshot")
        assert obs.content == "Screen captured"
        assert len(world.buffer.observations) == 1

    @pytest.mark.asyncio
    async def test_register_entity(self):
        world = WorldModel()
        entity = world.register_entity("Chrome", EntityType.APPLICATION)
        assert entity.name == "Chrome"
        assert len(world.registry.entities) == 1

    def test_get_status(self):
        world = WorldModel()
        status = world.get_status()
        assert "entities" in status
        assert "observations" in status
        assert "predictions" in status


# ── Integration Tests ─────────────────────────────────────────────────────────


class TestAGIIntegration:
    @pytest.mark.asyncio
    async def test_goal_world_integration(self):
        """Test that goals can be created and world observations made."""
        goal_mgr = GoalManager()
        world_mdl = WorldModel()

        # Create a goal
        goal = await goal_mgr.create_goal("Test integration", "MEDIUM", auto_decompose=False)

        # Make an observation
        obs = await world_mdl.observe("Integration test running", "test")

        assert goal.uid is not None
        assert obs.uid is not None

    @pytest.mark.asyncio
    async def test_full_cognitive_cycle(self):
        """Test a full cycle of goal creation, observation, and status check."""
        goal_mgr = get_goal_manager()
        world_mdl = get_world_model()

        # Create goals
        await goal_mgr.create_goal("Goal A", "HIGH", auto_decompose=False)
        await goal_mgr.create_goal("Goal B", "LOW", auto_decompose=False)

        # Make observations
        await world_mdl.observe("State A", "test")
        await world_mdl.observe("State B", "test")

        # Check statuses
        goal_status = goal_mgr.get_status()
        world_status = world_mdl.get_status()

        assert goal_status["total_goals"] >= 2
        assert world_status["observations"] >= 2


# ── Performance Tests ──────────────────────────────────────────────────────────


class TestPerformance:
    @pytest.mark.asyncio
    async def test_goal_creation_performance(self):
        """Test that goal creation is fast."""
        manager = GoalManager()

        start = time.perf_counter()
        for i in range(100):
            await manager.create_goal(f"Goal {i}", "MEDIUM", auto_decompose=False)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0  # Should complete in under 5 seconds

    def test_entity_registration_performance(self, entity_registry):
        """Test that entity registration is fast."""
        start = time.perf_counter()
        for i in range(1000):
            entity_registry.register(f"Entity {i}", EntityType.CONCEPT)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0  # Should complete in under 5 seconds (relaxed for CI)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
