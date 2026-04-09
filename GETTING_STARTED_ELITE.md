# Elite Improvements — Getting Started Guide

**Goal**: Understand and use Vision's new elite quality framework in your daily development.

---

## 5-Minute Overview

Vision now has **6 new elite modules** that handle resilience, metrics, safety, and code quality. Instead of reinventing these in every function, **reuse these:**

| Problem | Elite Module | Solution |
|---------|--------------|----------|
| Provider keeps failing | `elite_resilience` | `CircuitBreaker` auto-fallback |
| Can't track performance | `elite_metrics` | `metrics.record_latency()` |
| Tool hangs forever | `elite_tools` | `tool_executor.execute(..., timeout=30)` |
| Context window too large | `elite_memory` | `EliteMemory` auto-trim |
| Repeating code patterns | `elite_patterns` | `@async_cached`, `@async_retry` |
| Security vulnerabilities | `elite_safety` | `scan_for_secrets()`, `InputValidator` |

---

## Best Practices Cookbook

### 1. Use Circuit Breaker for Providers

**Problem**: OpenAI API is down, entire system fails.

**Solution**:
```python
from elite_resilience import CircuitBreaker

breaker = CircuitBreaker("openai")  # Auto-tracks health

# Try calling OpenAI
try:
    result = await breaker.call(
        openai.chat.completions.create,
        model="gpt-4",
        messages=[...],
    )
except Exception:
    # Circuit is OPEN — try fallback
    result = await anthropic.messages.create(...)
```

**When to use**: Anytime calling external providers (LLMs, APIs, databases).

---

### 2. Cache Expensive Results

**Problem**: Fetching available models every 5 seconds = 12 API calls/min.

**Solution**:
```python
from elite_patterns import async_cached

@async_cached(ttl_seconds=3600)  # Cache for 1 hour
async def fetch_available_models(provider: str) -> List[str]:
    return await api.list_models(provider)

# First call: real API
models = await fetch_available_models("openai")  # 500ms

# Second call: cached
models = await fetch_available_models("openai")  # 1ms (instant)
```

**When to use**: Static data, metadata, rarely-changing config.

---

### 3. Retry with Backoff

**Problem**: Network glitch causes request to fail on first try.

**Solution**:
```python
from elite_patterns import async_retry

@async_retry(max_attempts=3, backoff_base=0.5)
async def robust_llm_call(text: str) -> str:
    """Auto-retries 3 times with exponential backoff (0.5s, 1s, 2s)."""
    return await llm.complete(text)

# Automatically retries; fails only after 3 attempts
result = await robust_llm_call("What is AI?")
```

**When to use**: Network calls, timeouts, transient failures.

---

### 4. Track Performance

**Problem**: "Why is the response so slow?" — No visibility.

**Solution**:
```python
from elite_metrics import metrics
import time

start = time.monotonic()
result = await expensive_operation()
elapsed_ms = (time.monotonic() - start) * 1000

metrics.record_latency("expensive_op", elapsed_ms)

# Later, check metrics
snapshot = metrics.snapshot()
print(snapshot["latencies"]["expensive_op"])
# {"name": "expensive_op", "count": 42, "p95": 1500, "max": 3000}
```

**When to use**: All external API calls, complex operations.

---

### 5. Validate User Input

**Problem**: User provides `../../etc/passwd` as file path → security breach.

**Solution**:
```python
from elite_safety import InputValidator

# Prevent path traversal
safe_path = InputValidator.sanitize_file_path(
    user_provided_path,
    base_dir="/allowed_folder"
)
if not safe_path:
    raise ValueError("Invalid path")

# Validate URLs (prevent SSRF)
if InputValidator.validate_url(user_url):
    result = await http.get(user_url)
else:
    raise ValueError("Invalid URL")
```

**When to use**: Any user-provided file path, URL, shell command.

---

### 6. Parallel Tool Execution

**Problem**: Taking screenshots of 3 regions sequentially = 3 seconds.

**Solution**:
```python
from elite_tools import tool_executor

# Run 3 screenshots in parallel (safe: all read-only)
results = await tool_executor.batch_execute([
    ("screenshot", {}),
    ("screenshot_region", {"region": "top"}),
    ("screenshot_region", {"region": "bottom"}),
], executor_fn)

# All 3 done in ~1 second (parallel) instead of 3 seconds (serial)
```

**When to use**: Multiple independent read-only tools.

---

### 7. Detect Code Problems Early

**Problem**: "I hardcoded my API key!" — After pushing to GitHub.

**Solution**:
```python
from elite_safety import assess_code_health, validate_no_hardcoded_secrets

code = open("my_module.py").read()

# Scan for secrets
if not validate_no_hardcoded_secrets(code, raise_on_finding=True):
    raise ValueError("Remove secrets before committing!")

# Full health check
health = assess_code_health(code, is_async=True)
print(f"Code health: {health.score:.0%}")
for issue in health.issues:
    print(f"  ⚠️ {issue}")
```

**When to use**: Before committing, in CI/CD.

---

### 8. Structured Error Handling

**Problem**: Exception loses context, hard to debug.

**Solution**:
```python
from elite_patterns import Result
import logging

logger = logging.getLogger(__name__)

try:
    result = await risky_operation()
    return Result.ok(value=result)
except TimeoutError as e:
    logger.error(f"Operation timed out after 5s", exc_info=True)
    return Result.err(f"Timeout: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return Result.err(f"Failed: {e}")

# Usage
result = await safe_operation()
if result.is_ok:
    value = result.value
else:
    print(f"Error: {result.error}")
```

**When to use**: All async operations, external API calls.

---

### 9. Manage Conversation Context

**Problem**: After 100 messages, context window exceeds LLM limits.

**Solution**:
```python
from elite_memory import EliteMemory

memory = EliteMemory(max_tokens=8000)  # Auto-trim to 8k tokens

# Add messages
memory.add_message("user", "What's your name?")
memory.add_message("assistant", "I'm Vision...")

# Get optimized context for LLM
context = memory.get_context()
# Returns exactly what fits in 8000 tokens

# Search history
results = memory.search("earlier discussion")
```

**When to use**: Multi-turn conversations.

---

### 10. Measure Everything

**Problem**: "Which provider is slowest?" — No data.

**Solution**:
```python
from elite_metrics import metrics

# Log LLM calls
metrics.llm_request_stats(
    provider="openai",
    model="gpt-4",
    tokens=150,
    latency_ms=1200,
)

# Get summary for dashboard
summary = metrics.summary()
print(summary["top_latencies"])
# See which tools/providers are slowest
```

**When to use**: Anytime you want insights.

---

## Type Hints Reference

Vision enforces type hints! Here's quick reference:

```python
# ✅ GOOD
async def execute(name: str, args: Dict[str, Any]) -> ToolResult:
    ...

# ❌ BAD (will fail mypy)
async def execute(name, args):
    ...

# Common types
from typing import Optional, List, Dict, Set, Tuple, Callable, Any

api_key: Optional[str] = os.environ.get("KEY")
models: List[str] = ["gpt-4", "gpt-3.5"]
config: Dict[str, Any] = {"timeout": 30, "retries": 3}
responses: Set[str] = {"streaming", "batched"}
pair: Tuple[str, int] = ("name", 42)
callback: Callable[[str], str] = lambda x: x.upper()

# Async generators
async def stream_tokens() -> AsyncGenerator[str, None]:
    for token in tokens:
        yield token
```

---

## Docstring Template

```python
def my_function(param1: str, param2: int) -> Dict[str, Any]:
    """One-line summary of what this does.

    Longer explanation if needed. Explain the *why*, not the *what*.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Dictionary with keys "result" and "status".

    Raises:
        ValueError: If param2 is negative.

    Example:
        >>> result = my_function("hello", 42)
        >>> print(result["status"])
        "ok"
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")
    return {"result": param1 * param2, "status": "ok"}
```

---

## Testing Template

Create `tests/test_my_module.py`:

```python
import pytest
from my_module import my_function

@pytest.mark.asyncio
async def test_my_function_success():
    """Test happy path."""
    result = await my_function("hello", 42)
    assert result["status"] == "ok"
    assert "hello" in result["result"]

@pytest.mark.asyncio
async def test_my_function_invalid_input():
    """Test error handling."""
    with pytest.raises(ValueError, match="non-negative"):
        await my_function("hello", -1)

def test_sync_function():
    """Test sync functions too."""
    assert sync_helper(5) == 10
```

Run: `pytest tests/ -v`

---

## Command Cheatsheet

```bash
# Format code
black .
isort .

# Type check
mypy elite_*.py --strict

# Lint
pylint elite_*.py

# Security scan
bandit elite_*.py

# Run tests with coverage
pytest tests/ --cov=elite_ --cov-report=html

# Run just one test
pytest tests/test_my_module.py::test_my_function -v

# Run with async output
pytest tests/ -v -s

# Check what would be changed
black . --check --diff
isort . --check-only --diff
```

---

## Copilot Tips

### 1. Ask for Type Hints
> "Add type hints and docstrings to this function"

### 2. Ask for Refactoring
> "Refactor this to use elite_patterns decorators"

### 3. Use Skills
> "/vision-runtime-ops Can you help me verify the stack is running?"

### 4. Reference Conventions
> "Review this against .github/copilot-conventions.md"

### 5. Leverage Agents
> "@Vision Maintainer Is this WebSocket change safe?"

---

## Troubleshooting

### Q: mypy says "error: Function is missing return type annotation"
**A**: Add return type:
```python
# Before
async def fetch_models(provider):
    ...

# After
async def fetch_models(provider: str) -> List[str]:
    ...
```

### Q: "Hardcoded secret detected"
**A**: Use environment variable:
```python
# Before
api_key = "sk-1234567890"

# After
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Set OPENAI_API_KEY environment variable")
```

### Q: Tool execution hangs
**A**: Use timeout:
```python
result = await tool_executor.execute(
    ...,
    timeout_seconds=10.0,  # Add this
)
```

### Q: Tests are slow
**A**: Run in parallel or use fixtures:
```bash
pytest -n auto  # Parallel (requires pytest-xdist)
```

---

## Next Steps

1. **Read** `.github/copilot-conventions.md` — Full style guide
2. **Run** `pip install -e ".[dev]"` — Set up development env
3. **Check** `pyproject.toml` — Understand tool config
4. **Try** `/vision-runtime-ops` skill in Copilot — See it in action
5. **Write** a small test in `tests/` — Verify pytest works
6. **Review** `ELITE_ENHANCEMENTS.md` — Deep dive on all features

---

## Support

- 📝 **Conventions**: `.github/copilot-conventions.md`
- 📚 **Full Docs**: `ELITE_ENHANCEMENTS.md`
- 💬 **Copilot Skills**: Use `/skill-name` in Copilot chat
- 🤖 **Agents**: Use `@agent-name` for specialized help
- 🔍 **Errors**: Check `chat_events.log` for debugging

---

**Happy coding! 🚀**
