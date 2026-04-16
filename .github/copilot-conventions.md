# Vision Code Quality & Copilot Conventions

> **Goal**: Make GitHub Copilot smarter and more aligned with Vision's architecture, coding standards, and best practices.

---

## 1. Code Quality Standards

### Type Hints
- **REQUIRED** for all public functions and async functions
- Use `Optional[T]` instead of `T | None` for compatibility
- Annotate complex return types: `Dict[str, List[float]]`

```python
# ✅ GOOD
async def execute_tool(name: str, args: Dict[str, Any]) -> ToolResult:
    ...

# ❌ BAD
async def execute_tool(name, args):
    ...
```

### Docstrings
- Use triple-quoted docstrings for all public modules, classes, functions
- Include **purpose**, **parameters**, **returns**, **examples** (where non-obvious)
- Follow Google-style docstrings

```python
# ✅ GOOD
def adjust_vad_threshold(new_threshold: int) -> None:
    """Adjust VAD detection threshold.

    Args:
        new_threshold: RMS level threshold (higher = less sensitive).

    Returns:
        None

    Note:
        Values above 1000 are conservative; below 300 are aggressive.
    """
    ...

# ❌ BAD
def adjust_vad_threshold(new_threshold):
    # adjust threshold
    ...
```

### Async/Await Patterns
- Prefer `await asyncio.sleep()` over `time.sleep()`
- Use `asyncio.gather()` for parallel execution of independent tasks
- Always use `return_exceptions=True` in `gather()` to prevent one failure from blocking others
- Use `asyncio.TimeoutError` handling explicitly

```python
# ✅ GOOD
results = await asyncio.gather(
    exec_tool("click", args1),
    exec_tool("type_text", args2),
    return_exceptions=True,
)

# ❌ BAD
await asyncio.sleep(1)  # OK for delays
for task in tasks:
    result = await task  # Sequential, slow
```

### Error Handling
- Use custom exception types (inherit from `Exception`)
- Provide context in error messages: include input, expected behavior, actual result
- Log before raising: `logger.error(...)` then `raise CustomError(...)`

```python
# ✅ GOOD
try:
    result = await exec_tool(name, args)
except asyncio.TimeoutError:
    logger.error(f"Tool {name} timed out after {timeout}s")
    raise ToolExecutionError(f"Timeout: {name}") from None

# ❌ BAD
try:
    result = await exec_tool(name, args)
except Exception:
    raise  # No context
```

### Security
- **NEVER hardcode secrets**. Use environment variables or keyring
- Validate all inputs: file paths, URLs, JSON
- Sanitize logs before writing: use `elite_safety.sanitize_for_logging()`
- Use `elite_safety.InputValidator` for user-provided paths and URLs

```python
# ✅ GOOD
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")

path = InputValidator.sanitize_file_path(user_path, base_dir="/allowed")
if not path:
    raise ValueError("Invalid path")

# ❌ BAD
api_key = "sk-proj-123456..."  # Hardcoded!
path = user_path  # Trusting user input
```

---

## 2. Module Organization & Imports

### File Structure
```
c:\project\vision\
├── live_chat_app.py          # Main backend entry point
├── live_chat_ui.html          # Main UI (primary)
├── elite_*.py                 # Elite modules (resilience, metrics, tools, etc.)
├── architecture.md            # System design docs
├── setup.md                   # Installation & setup
└── .github/
    ├── copilot-instructions.md    # Copilot repo guidance
    ├── agents/                    # Specialized agents
    └── skills/                    # Reusable skills
```

### Import Order
1. Built-in modules (`asyncio`, `json`, `os`)
2. Third-party (`fastapi`, `numpy`, `httpx`)
3. Local project (`elite_*`, `live_chat_app`)
4. Conditionally-imported modules at end

```python
# ✅ GOOD
import asyncio
import json
import os
from pathlib import Path
from typing import Optional, Dict, List

import httpx
import numpy as np
from fastapi import FastAPI

from elite_metrics import metrics
from elite_safety import InputValidator
import live_chat_app as app

# ❌ BAD (mixed order, relative imports)
from elite_metrics import metrics
import os
from typing import Optional
import asyncio
from .live_chat_app import some_func
```

---

## 3. Naming Conventions

### Variables & Functions
- Use `snake_case` for variables and functions
- Use `UPPER_CASE` for constants
- Prefix private/internal with `_`

```python
# ✅ GOOD
MAX_RETRIES = 3
async def execute_tool(name: str) -> str:
    _internal_state = {}
    return result

# ❌ BAD
MaxRetries = 3
async def ExecuteTool(name):
    InternalState = {}
```

### Classes
- Use `PascalCase`
- Descriptive names: `CircuitBreaker`, not `CB`

```python
# ✅ GOOD
class CircuitBreaker:
    def __init__(self, name: str): ...

# ❌ BAD
class CircuitBreakerImpl:
    def __init__(self, nm): ...
```

### Booleans
- Prefix with `is_`, `has_`, `can_`, `should_`

```python
# ✅ GOOD
is_healthy = status == "ok"
has_cache_hit = key in cache
can_execute = not is_blocked

# ❌ BAD
healthy = status == "ok"
cached = key in cache
```

---

## 4. Comments & Documentation

### When to Comment
- **Complex logic**: Explain *why*, not *what*
- **Non-obvious decisions**: Design trade-offs
- **Workarounds**: Known issues, platform quirks
- **Performance notes**: Why we choose X over Y

```python
# ✅ GOOD
# VAD thresholds tuned for desktop/laptop environments with moderate ambient noise
# Higher RMS_THRESH reduces false-positives in noisy offices
RMS_THRESH = 500

# Collect streamed tokens before passing to TTS to batch them into natural chunks
# Improves speech quality and reduces perceived latency (3-5 words per chunk = ~400ms)
collected.append(chunk)

# ❌ BAD
# Increment counter
counter += 1

# Loop over items
for item in items:
    ...
```

### Code Sections
Use section dividers for readability:

```python
# ── Configuration ──────────────────────────────────────────────────────────────
DEFAULTS = {...}

# ── Core Logic ─────────────────────────────────────────────────────────────────
async def main():
    ...

# ── Utilities ──────────────────────────────────────────────────────────────────
def helper():
    ...
```

---

## 5. Testing & Quality Checks

### Test Structure
- Follow the repo's current pytest layout: tests may live at the repo root
  (`test_vision.py`, `test_tools.py`, `conftest.py`) rather than a dedicated `tests/` folder
- Use the existing repo test entrypoints first (`python test_tools.py`, `python test_vision.py`)
- Name new pytest-style tests `test_<area>.py` or `test_<function>_<scenario>.py` to match the current repo mix

```python
# ✅ test_elite_tools.py
import pytest
from elite_tools import SafeToolExecutor

@pytest.mark.asyncio
async def test_execute_with_timeout():
    executor = SafeToolExecutor()
    # Test implementation
    assert result.success == False
```

### Quality Gates (CI/CD)
- **Type checking**: `mypy --strict`
- **Linting**: `pylint` (min score 8.0)
- **Formatting**: `ruff format` with 120-character line length
- **Security**: `bandit` (no high/critical issues)
- **Test coverage**: `pytest --cov` (min 80%)

### Pre-commit Hooks
```bash
# .git/hooks/pre-commit
ruff format .
mypy elite_*.py
pylint elite_*.py
pytest --cov=elite_
```

---

## 6. Performance & Optimization

### Async Best Practices
- Never block the event loop: use `run_in_executor()` for CPU-bound work
- Batch independent operations with `gather()`
- Use timeouts to prevent hangs: `asyncio.wait_for(..., timeout=30)`

```python
# ✅ GOOD
result = await asyncio.wait_for(
    fetch_from_api(url),
    timeout=10.0,
)

# ❌ BAD (may hang forever)
result = await fetch_from_api(url)
```

### Caching
- Use `@async_cached(ttl_seconds=300)` from `elite_patterns`
- Only cache deterministic, side-effect-free operations
- Include cache statistics in `elite_metrics`

```python
# ✅ GOOD
@async_cached(ttl_seconds=600)
async def fetch_provider_models(provider: str) -> List[str]:
    # Expensive, but static per provider
    return await api.list_models(provider)

# ❌ BAD
@async_cached(ttl_seconds=300)
async def get_user_settings(user_id: str) -> Dict:
    # User settings change frequently; low TTL doesn't help
    return db.fetch_user(user_id)
```

### Memory Management
- Use `deque(maxlen=X)` for fixed-size buffers (auto-eviction)
- Clear large caches periodically: `cache.clear()`
- Monitor with `elite_metrics.set_gauge("memory_usage_mb", ...)`

---

## 7. Logging & Observability

### Structured Logging
- Use `logger.info(msg, extra={...})` with structured context
- Log at decision points: state changes, errors, external API calls

```python
# ✅ GOOD
logger.info(
    "tool_executed",
    extra={
        "tool": "click",
        "args": args,
        "duration_ms": elapsed,
        "success": True,
    }
)

# ❌ BAD
print(f"Clicked at {x}, {y}")  # Lost in logs, hard to analyze
```

### Log Levels
- `DEBUG`: Verbose internal state (only in debug mode)
- `INFO`: State transitions, external API calls, tool execution
- `WARNING`: Recoverable issues (circuit breaker opening, retry)
- `ERROR`: tool failures, provider errors
- `CRITICAL`: System shutdown required

---

## 8. Copilot Optimization Tips

### Provide Context
- Keep `.github/copilot-instructions.md` updated
- Add examples of idiomatic code in recent commits
- Document project-specific idioms (e.g., "always use `broadcast()` for state changes")

### Use Skills & Agents
- Invoke `/vision-runtime-ops` for debugging runtime issues
- Use `@Vision Maintainer` agent for protocol/WebSocket changes
- Reference `.github/agents/vision-maintainer.agent.md` in PRs

### Leverage Type Hints
- Type hints enable Copilot to infer intent
- Use dataclasses with field annotations for clarity
- Annotate dependencies: `from typing import Optional, List, Dict`

### Train Copilot
- After merged code, Copilot learns patterns
- Reference `chat_events.log` for recurring patterns needing improvement
- Create snippets for common patterns (see `.github/snippets/`)

---

## 9. Refactoring Checklist

Before submitting code:
- [ ] Type hints on all public functions
- [ ] Docstrings on modules, classes, public functions
- [ ] No hardcoded secrets (use `elite_safety.validate_no_hardcoded_secrets()`)
- [ ] No blocking calls in async functions
- [ ] Error handling with context
- [ ] Tests added for new functionality
- [ ] Repo checks pass (`python -m py_compile`, `python test_tools.py`, `python test_vision.py`, plus any targeted lint/type checks in use)
- [ ] Logging at decision points
- [ ] Performance impact assessed (especially LLM calls, tool execution)

---

## 10. Common Patterns (Copy-Paste Friendly)

### Safe Function Execution with Retry
```python
from elite_patterns import async_retry

@async_retry(max_attempts=3, backoff_base=0.5)
async def fetch_with_retry(url: str) -> str:
    """Fetch URL with automatic retry and exponential backoff."""
    return await http_client.get(url).text()
```

### Measuring Latency
```python
from elite_patterns import async_timer

async def some_operation():
    async with async_timer("operation_name"):
        await expensive_task()
    # Automatically logged: "operation_name: 123.4ms"
```

### Tool Execution with Safety
```python
from elite_tools import tool_executor

result = await tool_executor.execute(
    tool="click",
    args={"x": 100, "y": 200},
    executor_fn=exec_tool,
    cacheable=True,
    timeout_seconds=30.0,
)
assert result.success
print(f"Duration: {result.duration_ms}ms, Cache hit: {result.cache_hit}")
```

### Code Health Assessment
```python
from elite_safety import assess_code_health

code = open("my_module.py").read()
health = assess_code_health(code, is_async=True)
print(f"Health score: {health.score:.0%}")
print(f"Issues: {health.issues}")
```

---

## 11. Git Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`
- **scope**: `elite-tools`, `voice`, `providers`, `memory`, etc.
- **subject**: Imperative, no period

```
feat(elite-tools): add parallel tool execution with fallback

Implement SafeToolExecutor.batch_execute() to allow safe
concurrent execution of read-only tools (screenshot, read_screen)
while running state-changing tools sequentially.

Closes #42
```

---

**Last Updated**: April 10, 2026
**Revision**: 1.0 (Beta)
