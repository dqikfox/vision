"""vision_log_rotation.py — Rotating file handler setup for Vision logs.

Replaces unbounded chat_events.log growth with a RotatingFileHandler capped
at 10 MB per file, keeping the last 5 rotated files (50 MB total cap).

Usage (called once at startup in live_chat_app.py):
    from vision_log_rotation import configure_rotating_log
    configure_rotating_log()
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

LOG_PATH = Path(__file__).parent / "chat_events.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
BACKUP_COUNT = 5               # keep last 5 rotated files (~50 MB total)
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def configure_rotating_log(
    log_path: Path = LOG_PATH,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
    level: int = logging.INFO,
) -> logging.Handler:
    """Attach a RotatingFileHandler to the root logger.

    Safe to call multiple times — skips setup if a RotatingFileHandler
    targeting the same path is already registered.

    Returns the handler (new or existing).
    """
    root = logging.getLogger()
    for handler in root.handlers:
        if (
            isinstance(handler, logging.handlers.RotatingFileHandler)
            and Path(handler.baseFilename).resolve() == log_path.resolve()
        ):
            return handler

    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    handler.setLevel(level)
    root.addHandler(handler)
    root.setLevel(min(root.level or logging.WARNING, level))
    return handler
