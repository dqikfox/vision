"""
elite_patterns.py — Reusable abstractions, helper functions, common patterns
============================================================================
Reduces boilerplate, improves consistency, encapsulates best practices.
"""

import asyncio
import functools
import logging
from typing import TypeVar, Callable, Any, Optional, List, Dict
from dataclasses import dataclass
from contextlib import asynccontextmanager

T = TypeVar("T")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Async Utilities
# ──────────────────────────────────────────────────────────────────────────────

def async_cached(ttl_seconds: int = 300):
    """Decorator: cache async function results with TTL."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        cache: Dict[str, tuple[Any, float]] = {}

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            import time
            key = f"{fn.__name__}:{args}:{kwargs}"
            if key in cache:
                result, expiry = cache[key]
                if time.time() < expiry:
                    return result
            result = await fn(*args, **kwargs)
            cache[key] = (result, time.time() + ttl_seconds)
            return result

        return wrapper
    return decorator

def async_retry(max_attempts: int = 3, backoff_base: float = 0.5):
    """Decorator: retry async function with exponential backoff."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            import random
            for attempt in range(max_attempts):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    if attempt >= max_attempts - 1:
                        raise
                    delay = backoff_base * (2 ** attempt) * (0.5 + random.random())
                    logger.debug(f"Retry {attempt + 1}/{max_attempts} after {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

def requires_keys(*env_vars: str):
    """Decorator: validate required environment variables."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            import os
            missing = [k for k in env_vars if not os.environ.get(k)]
            if missing:
                raise ValueError(f"Missing required env vars: {', '.join(missing)}")
            return await fn(*args, **kwargs)
        return wrapper
    return decorator

@asynccontextmanager
async def async_timer(name: str, logger_fn: Optional[Callable] = None):
    """Context manager: measure async code block duration."""
    import time
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - start) * 1000
        if logger_fn:
            logger_fn(f"{name}: {elapsed_ms:.1f}ms")
        else:
            logger.info(f"{name}: {elapsed_ms:.1f}ms")

# ──────────────────────────────────────────────────────────────────────────────
# Data Validation
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    """Result of validation check."""
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        self.errors = self.errors or []
        self.warnings = self.warnings or []

    def is_clean(self) -> bool:
        """True if valid with no warnings."""
        return self.valid and not self.warnings

class Validator:
    """Chainable validation builder."""

    def __init__(self, value: Any, name: str = "value"):
        self.value = value
        self.name = name
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def not_none(self) -> "Validator":
        if self.value is None:
            self.errors.append(f"{self.name} cannot be None")
        return self

    def not_empty(self) -> "Validator":
        if isinstance(self.value, (str, list, dict)) and not self.value:
            self.errors.append(f"{self.name} cannot be empty")
        return self

    def in_range(self, min_val: float, max_val: float) -> "Validator":
        if not (min_val <= self.value <= max_val):
            self.errors.append(f"{self.name} must be between {min_val} and {max_val}")
        return self

    def matches_pattern(self, pattern: str) -> "Validator":
        import re
        if not re.match(pattern, str(self.value)):
            self.errors.append(f"{self.name} does not match pattern {pattern}")
        return self

    def is_type(self, *types) -> "Validator":
        if not isinstance(self.value, types):
            self.errors.append(f"{self.name} must be one of {types}")
        return self

    def result(self) -> ValidationResult:
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
        )

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

class ConfigLoader:
    """Load and validate configuration from environment or files."""

    @staticmethod
    def from_env(key: str, default: Any = None, required: bool = False) -> Any:
        """Load config value from environment."""
        import os
        val = os.environ.get(key, default)
        if required and val is None:
            raise ValueError(f"Required config {key} not found")
        return val

    @staticmethod
    def from_json_file(path: str) -> Dict[str, Any]:
        """Load config from JSON file."""
        import json
        from pathlib import Path
        file = Path(path)
        if not file.exists():
            return {}
        return json.loads(file.read_text())

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────

def setup_structured_logging(name: str, level: str = "INFO") -> logging.Logger:
    """Configure structured logging with JSON output."""
    import logging.config
    import json

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_obj = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    return logger

# ──────────────────────────────────────────────────────────────────────────────
# Result Type (monadic error handling)
# ──────────────────────────────────────────────────────────────────────────────

class Result:
    """Monadic Result type for safe error handling."""

    def __init__(self, value: Optional[T] = None, error: Optional[str] = None):
        self.value = value
        self.error = error
        self.is_ok = error is None

    @staticmethod
    def ok(value: T) -> "Result[T]":
        return Result(value=value)

    @staticmethod
    def err(error: str) -> "Result":
        return Result(error=error)

    def map(self, fn: Callable[[T], Any]) -> "Result":
        if self.is_ok:
            try:
                return Result.ok(fn(self.value))
            except Exception as e:
                return Result.err(str(e))
        return self

    def or_else(self, default: T) -> T:
        return self.value if self.is_ok else default

    def unwrap(self) -> T:
        if not self.is_ok:
            raise ValueError(f"Called unwrap on error: {self.error}")
        return self.value

    def __repr__(self) -> str:
        if self.is_ok:
            return f"Ok({self.value!r})"
        return f"Err({self.error!r})"
