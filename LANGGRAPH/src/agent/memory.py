from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class MemoryRecord:
    key: str
    value: str
    source: str
    updated_at: str


@dataclass
class SessionSummary:
    summary: str
    last_user_message: str
    last_agent_response: str
    updated_at: str


@dataclass
class SelfState:
    identity: str
    capabilities: list[str]
    limitations: list[str]
    operating_principles: list[str]
    updated_at: str


class FileMemoryStore:
    """Durable JSON memory store with namespace support."""

    def __init__(self, root: str | None = None, namespace: str = "default") -> None:
        env_root = os.getenv("AGENT_MEMORY_DIR")
        default_root = Path.home() / ".openharness" / "data" / "memory" / "langgraph-agent"
        self.root = Path(root or env_root or default_root)
        self.namespace = self._sanitize(namespace)
        self.base_dir = self.root / self.namespace
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.base_dir / "memory.json"
        self.summary_file = self.base_dir / "session.json"
        self.self_file = self.base_dir / "self.json"

    def _sanitize(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value) or "default"

    def load(self) -> dict[str, MemoryRecord]:
        if not self.memory_file.exists():
            return {}
        data = json.loads(self.memory_file.read_text(encoding="utf-8"))
        return {key: MemoryRecord(**value) for key, value in data.items()}

    def save(self, memories: dict[str, MemoryRecord]) -> None:
        serializable = {key: asdict(value) for key, value in memories.items()}
        self.memory_file.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")

    def upsert(self, key: str, value: str, source: str = "user") -> MemoryRecord:
        memories = self.load()
        record = MemoryRecord(key=key, value=value, source=source, updated_at=datetime.now(UTC).isoformat())
        memories[key] = record
        self.save(memories)
        return record

    def get(self, key: str) -> MemoryRecord | None:
        return self.load().get(key)

    def list_records(self) -> list[MemoryRecord]:
        return sorted(self.load().values(), key=lambda item: item.key)

    def save_session_summary(self, summary: SessionSummary) -> None:
        self.summary_file.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

    def load_session_summary(self) -> SessionSummary | None:
        if not self.summary_file.exists():
            return None
        return SessionSummary(**json.loads(self.summary_file.read_text(encoding="utf-8")))

    def save_self_state(self, self_state: SelfState) -> None:
        self.self_file.write_text(json.dumps(asdict(self_state), indent=2), encoding="utf-8")

    def load_self_state(self) -> SelfState:
        if self.self_file.exists():
            return SelfState(**json.loads(self.self_file.read_text(encoding="utf-8")))
        default = SelfState(
            identity="Memory-enabled LangGraph assistant",
            capabilities=[
                "retain simple long-term memory",
                "summarize recent interaction state",
                "reflect on goals, understanding, and limits",
            ],
            limitations=[
                "no hidden private consciousness",
                "reasoning quality depends on provided context",
                "memory retrieval is exact-match, not semantic vector search",
            ],
            operating_principles=[
                "be explicit about uncertainty",
                "store durable facts only when instructed or inferred safely",
                "separate self-state, user memory, and session state",
            ],
            updated_at=datetime.now(UTC).isoformat(),
        )
        self.save_self_state(default)
        return default


def extract_memory_updates(message: str) -> dict[str, str]:
    prefix = "remember "
    normalized = message.strip()
    if not normalized.lower().startswith(prefix):
        return {}
    payload = normalized[len(prefix):]
    if "=" not in payload:
        return {}
    key, value = payload.split("=", 1)
    key = key.strip().lower().replace(" ", "_")
    value = value.strip()
    if not key or not value:
        return {}
    return {key: value}


def infer_intent(message: str) -> str:
    lowered = message.lower()
    if lowered.startswith("remember "):
        return "store_memory"
    if "what do you know" in lowered or "recall" in lowered:
        return "recall_memory"
    if "who are you" in lowered or "self" in lowered:
        return "self_reflection"
    return "general_response"


def assess_comprehension(message: str, updates: dict[str, str]) -> str:
    if updates:
        return "The message contains an explicit durable-memory instruction."
    if "?" in message:
        return "The message appears to request information or explanation."
    return "The message appears to be a general statement or prompt."


def build_reasoning_outline(intent: str, memory_count: int, self_identity: str) -> list[str]:
    return [
        f"Detected intent: {intent}",
        f"Loaded {memory_count} durable memory records",
        f"Applied self-model: {self_identity}",
    ]


def render_memory_context(store: FileMemoryStore) -> str:
    records = store.list_records()
    if not records:
        return "No long-term memory stored yet."
    return "\n".join(f"- {record.key}: {record.value}" for record in records)
