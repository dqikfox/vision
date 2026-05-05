from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any


def langsmith_enabled() -> bool:
    return bool(os.getenv("LANGSMITH_TRACING")) and bool(os.getenv("LANGSMITH_API_KEY"))


@contextmanager
def trace_span(name: str, metadata: dict[str, Any] | None = None):
    """Best-effort tracing wrapper that works with or without LangSmith installed."""
    if not langsmith_enabled():
        yield None
        return
    try:
        from langsmith import trace  # type: ignore

        with trace(name=name, metadata=metadata or {}):
            yield None
    except Exception:
        yield None
