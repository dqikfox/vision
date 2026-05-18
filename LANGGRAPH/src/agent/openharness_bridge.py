from __future__ import annotations

import os
import re
from pathlib import Path


def resolve_openharness_memory_root() -> Path:
    configured = os.getenv("OPENHARNESS_MEMORY_DIR")
    if configured:
        return Path(configured)
    return Path.home() / ".openharness" / "data" / "memory"


def ensure_topic_index(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    index = root / "MEMORY.md"
    if not index.exists():
        index.write_text("# Memory Index\n\n", encoding="utf-8")
    return index


def _sanitize_topic(topic: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", topic.strip())
    normalized = normalized.strip("-_")
    if not normalized:
        raise ValueError("Topic must contain at least one alphanumeric character")
    return normalized


def append_topic_note(topic: str, content: str) -> Path:
    root = resolve_openharness_memory_root()
    index = ensure_topic_index(root)
    safe_topic = _sanitize_topic(topic)
    topic_file = root / f"{safe_topic}.md"
    if not topic_file.exists():
        index.write_text(index.read_text(encoding="utf-8") + f"- [{safe_topic}]({safe_topic}.md)\n", encoding="utf-8")
    with topic_file.open("a", encoding="utf-8") as handle:
        if topic_file.exists() and topic_file.stat().st_size > 0:
            handle.write("\n")
        handle.write(content)
    return topic_file
