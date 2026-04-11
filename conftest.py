"""
conftest.py — Pytest configuration and fixtures for Vision tests
================================================================
Shared fixtures for async tests, mocks, and integration setup.
"""

import asyncio
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Event Loop Management
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ──────────────────────────────────────────────────────────────────────────────
# Temporary Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_project_dir() -> Generator[Path, None, None]:
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def tmp_config_file(tmp_project_dir: Path) -> Path:
    """Create temporary config file."""
    config_file = tmp_project_dir / "config.json"
    config_file.write_text("{}")
    return config_file


# ──────────────────────────────────────────────────────────────────────────────
# Mock Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    class MockResponse:
        def __init__(self, status_code: int = 200, text: str = "{}") -> None:
            self.status_code = status_code
            self.text = text

        async def json(self) -> Any:
            import json as _json
            return _json.loads(self.text)

    class MockClient:
        async def get(self, url: str, **kwargs: Any) -> MockResponse:
            return MockResponse()

        async def post(self, url: str, **kwargs: Any) -> MockResponse:
            return MockResponse()

    return MockClient()


@pytest.fixture
def mock_llm_response():
    """Mock LLM streaming response."""
    class MockChoice:
        def __init__(self):
            self.delta = type('obj', (object,), {
                'content': 'Test response',
                'tool_calls': None,
            })()
            self.finish_reason = "stop"

    class MockStreamChunk:
        def __init__(self):
            self.choices = [MockChoice()]

    async def mock_stream():
        yield MockStreamChunk()
        yield MockStreamChunk()

    return mock_stream()


# ──────────────────────────────────────────────────────────────────────────────
# Logging Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def caplog_with_json(caplog):
    """Capture and parse JSON logs."""
    class JsonLogCapture:
        def __init__(self, caplog):
            self.caplog = caplog

        def get_records(self) -> list:
            """Parse captured log records."""
            records = []
            for record in self.caplog.records:
                records.append({
                    "level": record.levelname,
                    "message": record.getMessage(),
                })
            return records

    return JsonLogCapture(caplog)


# ──────────────────────────────────────────────────────────────────────────────
# Integration Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
async def elite_metrics_clean():
    """Fresh metrics collector for each test."""
    from elite_metrics import MetricsCollector
    return MetricsCollector()


@pytest.fixture
async def elite_tool_executor_clean():
    """Fresh tool executor for each test."""
    from elite_tools import SafeToolExecutor, ToolCache
    return SafeToolExecutor(cache=ToolCache())


@pytest.fixture
def monkeypatch_env(monkeypatch):
    """Monkeypatch environment variables."""
    def patch_env(key: str, value: str):
        monkeypatch.setenv(key, value)
    return patch_env


# ──────────────────────────────────────────────────────────────────────────────
# Marker-based Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def slow_test_warning(request):
    """Warn if slow tests run in quick test suite."""
    if "slow" in request.keywords:
        print("\n[SLOW TEST] This test may take several seconds - conftest.py:158")


# ──────────────────────────────────────────────────────────────────────────────
# Performance Monitoring
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def benchmark_async():
    """Benchmark async function performance."""
    import time

    class AsyncBenchmark:
        async def __call__(self, fn, *args, **kwargs):
            start = time.monotonic()
            result = await fn(*args, **kwargs)
            elapsed = time.monotonic() - start
            return {
                "result": result,
                "elapsed_ms": elapsed * 1000,
            }

    return AsyncBenchmark()


# ──────────────────────────────────────────────────────────────────────────────
# Cleanup & Teardown
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def cleanup_tasks():
    """Clean up dangling async tasks after each test."""
    yield

    # Cancel all pending tasks
    pending = asyncio.all_tasks(asyncio.get_event_loop())
    for task in pending:
        task.cancel()
