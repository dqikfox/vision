from __future__ import annotations

import os
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


def append_topic_note(topic: str, content: str) -> Path:
    root = resolve_openharness_memory_root()
    index = ensure_topic_index(root)
    topic_file = root / f"{topic}.md"
    if not topic_file.exists():
        index.write_text(index.read_text(encoding="utf-8") + f"- [{topic}]({topic}.md)\n", encoding="utf-8")
    topic_file.write_text(content, encoding="utf-8")
    return topic_file
