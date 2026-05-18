from __future__ import annotations

import json
import logging
import os
import re
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)
_LOCK_REGISTRY_GUARD = threading.Lock()
_FILE_LOCKS: dict[Path, threading.RLock] = {}


def _get_file_lock(path: Path) -> threading.RLock:
    with _LOCK_REGISTRY_GUARD:
        lock = _FILE_LOCKS.get(path)
        if lock is None:
            lock = threading.RLock()
            _FILE_LOCKS[path] = lock
        return lock


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
    """Durable JSON memory store with namespace support.

    Access is serialized per backing file within the current process to avoid
    lost updates from concurrent load-modify-save sequences.
    """

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
        self._memory_lock = _get_file_lock(self.memory_file)
        self._summary_lock = _get_file_lock(self.summary_file)
        self._self_lock = _get_file_lock(self.self_file)

    def _sanitize(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value) or "default"

    def _read_json_file(self, path: Path, default: dict[str, Any], lock: threading.RLock) -> dict[str, Any]:
        with lock:
            if not path.exists():
                return default
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to read JSON from %s: %s", path, exc)
                return default

            if not isinstance(data, dict):
                logger.warning("Expected JSON object in %s but received %s", path, type(data).__name__)
                return default
            return data

    def _write_json_file(self, path: Path, payload: object, lock: threading.RLock) -> None:
        with lock:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def load(self) -> dict[str, MemoryRecord]:
        data = self._read_json_file(self.memory_file, {}, self._memory_lock)
        records: dict[str, MemoryRecord] = {}
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, dict):
                records[key] = MemoryRecord(**value)
        return records

    def save(self, memories: dict[str, MemoryRecord]) -> None:
        serializable = {key: asdict(value) for key, value in memories.items()}
        self._write_json_file(self.memory_file, serializable, self._memory_lock)

    def upsert(self, key: str, value: str, source: str = "user") -> MemoryRecord:
        with self._memory_lock:
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
        self._write_json_file(self.summary_file, asdict(summary), self._summary_lock)

    def load_session_summary(self) -> SessionSummary | None:
        data = self._read_json_file(self.summary_file, {}, self._summary_lock)
        if not data:
            return None
        return SessionSummary(
            summary=str(data.get("summary", "")),
            last_user_message=str(data.get("last_user_message", "")),
            last_agent_response=str(data.get("last_agent_response", "")),
            updated_at=str(data.get("updated_at", "")),
        )

    def save_self_state(self, self_state: SelfState) -> None:
        self._write_json_file(self.self_file, asdict(self_state), self._self_lock)

    def load_self_state(self) -> SelfState:
        data = self._read_json_file(self.self_file, {}, self._self_lock)
        if data:
            return SelfState(
                identity=str(data.get("identity", "")),
                capabilities=[str(item) for item in data.get("capabilities", []) if isinstance(item, str)],
                limitations=[str(item) for item in data.get("limitations", []) if isinstance(item, str)],
                operating_principles=[
                    str(item) for item in data.get("operating_principles", []) if isinstance(item, str)
                ],
                updated_at=str(data.get("updated_at", "")),
            )
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
    has_self_keyword = bool(re.search(r"\bself\b", lowered))
    if lowered.startswith("remember "):
        return "store_memory"
    if "what do you know" in lowered or "recall" in lowered:
        return "recall_memory"
    if "who are you" in lowered or has_self_keyword:
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
