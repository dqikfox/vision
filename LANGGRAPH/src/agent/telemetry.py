from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator


logger = logging.getLogger(__name__)


def is_env_truthy(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def langsmith_enabled() -> bool:
    return is_env_truthy("LANGSMITH_TRACING") and bool(os.getenv("LANGSMITH_API_KEY"))


@contextmanager
def trace_span(name: str, metadata: dict[str, Any] | None = None) -> Iterator[None]:
    """Best-effort tracing wrapper that works with or without LangSmith installed."""
    if not langsmith_enabled():
        yield None
        return
    try:
        from langsmith import trace
    except ImportError:
        logger.info("LangSmith tracing requested but langsmith is not installed")
        yield None
        return

    with trace(name=name, metadata=metadata or {}):
        yield None
