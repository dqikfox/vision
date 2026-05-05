from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class OwtMemoryHit:
    content: str
    category: str
    worktree: str
    source: str | None


class OwtUnavailableError(RuntimeError):
    pass


def _import_owt() -> tuple[Any, Any, Any, Any]:
    try:
        from open_orchestrator.core.memory import MemoryManager
        from open_orchestrator.core.memory_store import MemoryStore
        from open_orchestrator.models.memory import MemoryLayer, MemoryType

        return MemoryManager, MemoryStore, MemoryLayer, MemoryType
    except Exception as exc:
        raise OwtUnavailableError("Open Orchestrator is not importable") from exc


def add_topic_memory(name: str, fact: str, repo_root: str | None = None) -> str:
    MemoryManager, _, _, MemoryType = _import_owt()
    manager = MemoryManager(Path(repo_root) if repo_root else None)
    manager.ensure_dirs()
    memory_type = manager.classify_fact(fact)
    filename = manager.slugify(name)
    from open_orchestrator.models.memory import TopicFile

    topic = TopicFile(
        name=name,
        description=fact[:100],
        memory_type=memory_type if memory_type else MemoryType.REFERENCE,
        body=fact,
        filename=filename,
    )
    path = manager.write_topic(topic)
    return str(path)


def add_recall_fact(content: str, category: str = "general", worktree: str = "global", source: str | None = None) -> None:
    _, MemoryStore, MemoryLayer, MemoryType = _import_owt()
    store = MemoryStore()
    try:
        store.add_fact(
            content=content,
            kind=MemoryType.REFERENCE,
            category=category,
            worktree=worktree,
            layer=MemoryLayer.L2_TOPIC,
            source=source,
        )
    finally:
        store.close()


def search_recall(query: str, limit: int = 5) -> list[OwtMemoryHit]:
    _, MemoryStore, _, _ = _import_owt()
    store = MemoryStore()
    try:
        if not hasattr(store, "search_facts"):
            return []
        results = store.search_facts(query, limit=limit)
        return [
            OwtMemoryHit(
                content=result.fact.content,
                category=result.fact.category,
                worktree=result.fact.worktree,
                source=result.fact.source,
            )
            for result in results
        ]
    finally:
        store.close()
