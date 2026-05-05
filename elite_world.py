"""
elite_world.py — World Model for Vision
========================================
Maintains a structured understanding of the environment, system state,
and ongoing situations to enable context-aware decision making.

Key Capabilities:
  1. ENTITY TRACKING    — Monitor objects, windows, files, processes
  2. STATE INFERENCE    — Derive high-level state from observations
  3. PREDICTION ENGINE  — Anticipate future states and needs
  4. SPATIAL MEMORY     — Remember locations and layouts
  5. CAUSAL MODEL       — Understand cause-effect relationships

Architecture
------------
  WorldModel
    ├─ EntityRegistry   ← tracks known entities and their states
    ├─ StateInference   ← derives meaning from observations
    ├─ PredictionEngine ← anticipates future states
    ├─ SpatialMemory    ← remembers physical/digital spaces
    └─ CausalModel      ← learns cause-effect patterns
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

WORLD_DATA_DIR = Path(__file__).parent / ".brain" / "world"
MAX_ENTITIES = 1000
MAX_OBSERVATIONS = 500
PREDICTION_HORIZON_SECONDS = 60
SPATIAL_MEMORY_SIZE = 100


class EntityType(Enum):
    """Types of entities that can be tracked."""

    WINDOW = auto()
    PROCESS = auto()
    FILE = auto()
    APPLICATION = auto()
    DEVICE = auto()
    CONCEPT = auto()
    TASK = auto()


class EntityState(Enum):
    """Possible states for an entity."""

    UNKNOWN = auto()
    ACTIVE = auto()
    INACTIVE = auto()
    BUSY = auto()
    ERROR = auto()
    COMPLETED = auto()


@dataclass
class Entity:
    """Represents a tracked entity in the world."""

    uid: str
    name: str
    entity_type: EntityType
    state: EntityState
    created_at: float
    last_seen: float
    attributes: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, list[str]] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    location: tuple[float, float] | None = None  # x, y for spatial memory


@dataclass
class Observation:
    """A single observation about the world."""

    uid: str
    timestamp: float
    source: str  # e.g., "screenshot", "tool_result", "user_input"
    content: str
    entities_involved: list[str] = field(default_factory=list)
    inferred_facts: list[str] = field(default_factory=list)


@dataclass
class Situation:
    """A higher-level situation composed of multiple observations."""

    uid: str
    description: str
    start_time: float
    end_time: float | None = None
    observations: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Prediction:
    """A prediction about future world state."""

    uid: str
    description: str
    confidence: float
    predicted_at: float
    expected_by: float
    trigger_observation: str | None = None
    fulfilled: bool | None = None
    fulfilled_at: float | None = None


class EntityRegistry:
    """
    Tracks all known entities in the world.
    """

    def __init__(self, data_dir: Path = WORLD_DATA_DIR) -> None:
        self.data_dir = data_dir
        self.entities: dict[str, Entity] = {}
        self._load()

    def _load(self) -> None:
        """Load entities from disk."""
        entities_file = self.data_dir / "entities.json"
        if not entities_file.exists():
            return
        try:
            data = json.loads(entities_file.read_text(encoding="utf-8"))
            for e in data:
                self.entities[e["uid"]] = Entity(
                    uid=e["uid"],
                    name=e["name"],
                    entity_type=EntityType[e["type"]],
                    state=EntityState[e["state"]],
                    created_at=e["created_at"],
                    last_seen=e["last_seen"],
                    attributes=e.get("attributes", {}),
                    relationships=e.get("relationships", {}),
                    history=e.get("history", []),
                    location=tuple(e["location"]) if e.get("location") else None,
                )
            logger.info("EntityRegistry loaded %d entities", len(self.entities))
        except Exception as exc:
            logger.warning("EntityRegistry load error: %s", exc)

    def save(self) -> None:
        """Persist entities to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = []
        for e in self.entities.values():
            data.append(
                {
                    "uid": e.uid,
                    "name": e.name,
                    "type": e.entity_type.name,
                    "state": e.state.name,
                    "created_at": e.created_at,
                    "last_seen": e.last_seen,
                    "attributes": e.attributes,
                    "relationships": e.relationships,
                    "history": e.history[-20:],  # Keep last 20 history entries
                    "location": list(e.location) if e.location else None,
                }
            )
        entities_file = self.data_dir / "entities.json"
        entities_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def register(
        self,
        name: str,
        entity_type: EntityType,
        state: EntityState = EntityState.UNKNOWN,
        attributes: dict[str, Any] | None = None,
    ) -> Entity:
        """Register a new entity or update existing."""
        # Check if entity with same name/type exists
        for entity in self.entities.values():
            if entity.name == name and entity.entity_type == entity_type:
                entity.last_seen = time.time()
                if attributes:
                    entity.attributes.update(attributes)
                return entity

        # Create new entity
        uid = f"entity_{entity_type.name.lower()}_{int(time.time() * 1000)}_{hash(name) % 10000}"
        entity = Entity(
            uid=uid,
            name=name,
            entity_type=entity_type,
            state=state,
            created_at=time.time(),
            last_seen=time.time(),
            attributes=attributes or {},
        )
        self.entities[uid] = entity
        self._evict_if_needed()
        self.save()
        return entity

    def update_state(self, uid: str, state: EntityState, context: str | None = None) -> None:
        """Update entity state and record in history."""
        if uid not in self.entities:
            return
        entity = self.entities[uid]
        old_state = entity.state
        entity.state = state
        entity.last_seen = time.time()
        entity.history.append(
            {
                "timestamp": time.time(),
                "from_state": old_state.name,
                "to_state": state.name,
                "context": context,
            }
        )
        self.save()

    def get_by_type(self, entity_type: EntityType) -> list[Entity]:
        """Get all entities of a specific type."""
        return [e for e in self.entities.values() if e.entity_type == entity_type]

    def get_active(self) -> list[Entity]:
        """Get all currently active entities."""
        return [e for e in self.entities.values() if e.state == EntityState.ACTIVE]

    def _evict_if_needed(self) -> None:
        """Remove oldest entities if over limit."""
        if len(self.entities) <= MAX_ENTITIES:
            return
        # Sort by last_seen, remove oldest
        sorted_entities = sorted(self.entities.values(), key=lambda e: e.last_seen)
        to_remove = len(self.entities) - MAX_ENTITIES
        for entity in sorted_entities[:to_remove]:
            del self.entities[entity.uid]


class ObservationBuffer:
    """
    Rolling buffer of recent observations.
    """

    def __init__(self, max_size: int = MAX_OBSERVATIONS) -> None:
        self.max_size = max_size
        self.observations: deque[Observation] = deque(maxlen=max_size)
        self._llm_fn: Callable | None = None

    def set_llm(self, fn: Callable) -> None:
        """Wire in LLM for inference."""
        self._llm_fn = fn

    def add(
        self,
        content: str,
        source: str,
        entities_involved: list[str] | None = None,
    ) -> Observation:
        """Add a new observation."""
        obs = Observation(
            uid=f"obs_{int(time.time() * 1000)}_{hash(content) % 10000}",
            timestamp=time.time(),
            source=source,
            content=content,
            entities_involved=entities_involved or [],
        )
        self.observations.append(obs)
        return obs

    def get_recent(self, count: int = 10) -> list[Observation]:
        """Get most recent observations."""
        return list(self.observations)[-count:]

    def get_since(self, timestamp: float) -> list[Observation]:
        """Get observations since a specific time."""
        return [o for o in self.observations if o.timestamp >= timestamp]

    async def infer_facts(self, observation: Observation) -> list[str]:
        """Use LLM to extract facts from observation."""
        if self._llm_fn is None:
            return []

        prompt = f"""Extract 1-3 key facts from this observation:

Observation: {observation.content}
Source: {observation.source}

List each fact on a new line starting with a dash (-).
Be concise and specific.

Facts:"""

        try:
            response = await self._llm_fn(prompt, max_tokens=150)
            facts = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    facts.append(line[1:].strip())
            return facts
        except Exception as exc:
            logger.warning("Fact inference failed: %s", exc)
            return []


class StateInference:
    """
    Infers high-level state from observations and entities.
    """

    def __init__(self, registry: EntityRegistry, buffer: ObservationBuffer) -> None:
        self.registry = registry
        self.buffer = buffer
        self._llm_fn: Callable | None = None
        self.current_situation: Situation | None = None

    def set_llm(self, fn: Callable) -> None:
        """Wire in LLM for inference."""
        self._llm_fn = fn
        self.buffer.set_llm(fn)

    async def infer_current_situation(self) -> Situation | None:
        """Infer the current situation from recent observations."""
        if self._llm_fn is None:
            return None

        recent_obs = self.buffer.get_recent(5)
        if not recent_obs:
            return None

        obs_text = "\n".join(f"- {o.content}" for o in recent_obs)
        active_entities = self.registry.get_active()
        entity_text = ", ".join(e.name for e in active_entities[:10])

        prompt = f"""Based on these recent observations and active entities, describe the current situation in 1-2 sentences.

Recent observations:
{obs_text}

Active entities: {entity_text}

Current situation:"""

        try:
            response = await self._llm_fn(prompt, max_tokens=100)
            situation = Situation(
                uid=f"sit_{int(time.time() * 1000)}",
                description=response.strip(),
                start_time=recent_obs[0].timestamp,
                observations=[o.uid for o in recent_obs],
                entities=[e.uid for e in active_entities],
            )
            self.current_situation = situation
            return situation
        except Exception as exc:
            logger.warning("Situation inference failed: %s", exc)
            return None

    async def detect_anomalies(self) -> list[str]:
        """Detect unusual patterns or anomalies."""
        if self._llm_fn is None:
            return []

        recent_obs = self.buffer.get_recent(20)
        if len(recent_obs) < 5:
            return []

        obs_text = "\n".join(f"- {o.content}" for o in recent_obs)

        prompt = f"""Analyze these observations for any anomalies, errors, or unusual patterns:

{obs_text}

If you detect any anomalies, list them. If everything looks normal, reply "No anomalies detected."

Anomalies:"""

        try:
            response = await self._llm_fn(prompt, max_tokens=150)
            if "no anomalies" in response.lower():
                return []
            return [line.strip("- *") for line in response.strip().split("\n") if line.strip()]
        except Exception as exc:
            logger.warning("Anomaly detection failed: %s", exc)
            return []


class PredictionEngine:
    """
    Predicts future world states based on patterns.
    """

    def __init__(self, buffer: ObservationBuffer) -> None:
        self.buffer = buffer
        self.predictions: dict[str, Prediction] = {}
        self._llm_fn: Callable | None = None
        self._pattern_history: list[dict[str, Any]] = []

    def set_llm(self, fn: Callable) -> None:
        """Wire in LLM for prediction."""
        self._llm_fn = fn

    async def generate_prediction(self, context: str | None = None) -> Prediction | None:
        """Generate a prediction about future state."""
        if self._llm_fn is None:
            return None

        recent_obs = self.buffer.get_recent(10)
        if not recent_obs:
            return None

        obs_text = "\n".join(f"- {o.content}" for o in recent_obs)
        context_str = f"\nContext: {context}\n" if context else ""

        prompt = f"""Based on these recent observations, predict what will likely happen in the next minute:

{obs_text}
{context_str}

Provide your prediction in this format:
Prediction: [what you predict]
Confidence: [high/medium/low]

Prediction:"""

        try:
            response = await self._llm_fn(prompt, max_tokens=100)

            # Parse prediction and confidence
            pred_match = response.lower().find("prediction:")
            conf_match = response.lower().find("confidence:")

            if pred_match >= 0:
                prediction_text = response[pred_match + 11 : conf_match if conf_match > 0 else None].strip()
                confidence_str = response[conf_match + 11 :].strip() if conf_match > 0 else "medium"

                confidence_map = {"high": 0.8, "medium": 0.5, "low": 0.3}
                confidence = confidence_map.get(confidence_str.lower().split()[0], 0.5)

                prediction = Prediction(
                    uid=f"pred_{int(time.time() * 1000)}",
                    description=prediction_text,
                    confidence=confidence,
                    predicted_at=time.time(),
                    expected_by=time.time() + PREDICTION_HORIZON_SECONDS,
                )
                self.predictions[prediction.uid] = prediction
                return prediction
        except Exception as exc:
            logger.warning("Prediction generation failed: %s", exc)
        return None

    def check_predictions(self) -> list[tuple[Prediction, bool]]:
        """Check which predictions have been fulfilled or failed."""
        results = []
        now = time.time()

        for pred in self.predictions.values():
            if pred.fulfilled is not None:
                continue

            if now > pred.expected_by:
                # Prediction expired, mark as failed
                pred.fulfilled = False
                pred.fulfilled_at = now
                results.append((pred, False))

        return results


class SpatialMemory:
    """
    Remembers spatial layouts and locations.
    """

    def __init__(self) -> None:
        self.locations: dict[str, tuple[float, float]] = {}
        self.layouts: dict[str, dict[str, Any]] = {}

    def record_location(self, name: str, x: float, y: float) -> None:
        """Record a named location."""
        self.locations[name] = (x, y)

    def get_location(self, name: str) -> tuple[float, float] | None:
        """Get coordinates for a named location."""
        return self.locations.get(name)

    def record_layout(self, name: str, layout: dict[str, Any]) -> None:
        """Record a spatial layout (e.g., desktop organization)."""
        self.layouts[name] = {
            "recorded_at": time.time(),
            "layout": layout,
        }

    def find_nearest(self, x: float, y: float, max_distance: float = 100.0) -> list[tuple[str, float]]:
        """Find named locations near coordinates."""
        distances = []
        for name, (lx, ly) in self.locations.items():
            dist = ((x - lx) ** 2 + (y - ly) ** 2) ** 0.5
            if dist <= max_distance:
                distances.append((name, dist))
        return sorted(distances, key=lambda x: x[1])


class WorldModel:
    """
    Main facade for world modeling.
    Integrates all components into a cohesive understanding.
    """

    def __init__(self) -> None:
        self.registry = EntityRegistry()
        self.buffer = ObservationBuffer()
        self.inference = StateInference(self.registry, self.buffer)
        self.predictions = PredictionEngine(self.buffer)
        self.spatial = SpatialMemory()
        self.current_situation: Situation | None = None
        self._running = False
        self._task: asyncio.Task | None = None

    def set_llm(self, fn: Callable) -> None:
        """Wire in LLM function."""
        self.inference.set_llm(fn)
        self.predictions.set_llm(fn)

    async def observe(
        self,
        content: str,
        source: str,
        entities_involved: list[str] | None = None,
    ) -> Observation:
        """Add a new observation to the world model."""
        obs = self.buffer.add(content, source, entities_involved)

        # Infer facts asynchronously
        if self.inference._llm_fn:
            facts = await self.buffer.infer_facts(obs)
            obs.inferred_facts = facts

        return obs

    def register_entity(
        self,
        name: str,
        entity_type: EntityType,
        state: EntityState = EntityState.UNKNOWN,
        attributes: dict[str, Any] | None = None,
    ) -> Entity:
        """Register an entity in the world."""
        return self.registry.register(name, entity_type, state, attributes)

    def update_entity_state(
        self,
        uid: str,
        state: EntityState,
        context: str | None = None,
    ) -> None:
        """Update an entity's state."""
        self.registry.update_state(uid, state, context)

    async def get_situation_summary(self) -> str:
        """Get a summary of the current situation."""
        situation = await self.inference.infer_current_situation()
        if situation:
            return situation.description

        # Fallback to basic summary
        active = self.registry.get_active()
        recent = self.buffer.get_recent(3)
        return f"{len(active)} active entities, {len(recent)} recent observations"

    async def generate_prediction(self, context: str | None = None) -> Prediction | None:
        """Generate a prediction about future state."""
        return await self.predictions.generate_prediction(context)

    def start_background_updates(self) -> None:
        """Start background world model updates."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info("WorldModel background updates started")

    def stop_background_updates(self) -> None:
        """Stop background updates."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("WorldModel background updates stopped")

    async def _update_loop(self) -> None:
        """Background loop for world model maintenance."""
        while self._running:
            try:
                # Update situation inference
                await self.inference.infer_current_situation()

                # Check predictions
                self.predictions.check_predictions()

                # Detect anomalies
                anomalies = await self.inference.detect_anomalies()
                if anomalies:
                    logger.warning("Anomalies detected: %s", anomalies)

                await asyncio.sleep(10.0)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("WorldModel update error: %s", exc)
                await asyncio.sleep(30.0)

    def get_status(self) -> dict[str, Any]:
        """Get current world model status."""
        return {
            "entities": len(self.registry.entities),
            "active_entities": len(self.registry.get_active()),
            "observations": len(self.buffer.observations),
            "predictions": len(self.predictions.predictions),
            "locations": len(self.spatial.locations),
            "current_situation": self.current_situation.description if self.current_situation else None,
        }


# ── Singleton Instance ───────────────────────────────────────────────────────

_world_model: WorldModel | None = None


def get_world_model() -> WorldModel:
    """Get or create the singleton WorldModel instance."""
    global _world_model
    if _world_model is None:
        _world_model = WorldModel()
    return _world_model
