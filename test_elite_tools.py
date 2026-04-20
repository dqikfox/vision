"""Unit tests for elite_tools.py."""

import asyncio
from collections.abc import Mapping

import pytest

from elite_tools import SafeToolExecutor, ToolCache


@pytest.mark.asyncio
async def test_execute_handles_unexpected_exceptions() -> None:
    """Unexpected executor errors are converted to failed ToolResults."""
    executor = SafeToolExecutor(cache=ToolCache())

    async def bad_executor(_tool: str, _args: Mapping[str, object]) -> str:
        raise TypeError("boom")

    result = await executor.execute("read_screen", {}, bad_executor)

    assert result.success is False
    assert result.error == "boom"


@pytest.mark.asyncio
async def test_batch_execute_does_not_cache_sequential_tools() -> None:
    """Non-read-only tools in a batch should execute every time."""
    executor = SafeToolExecutor(cache=ToolCache())
    call_count = 0

    async def fake_executor(_tool: str, _args: Mapping[str, object]) -> str:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0)
        return f"run-{call_count}"

    tools: list[tuple[str, Mapping[str, object]]] = [
        ("click", {"x": 10, "y": 10}),
        ("click", {"x": 10, "y": 10}),
    ]

    results = await executor.batch_execute(tools, fake_executor)

    assert call_count == 2
    assert [r.result for r in results] == ["run-1", "run-2"]
    assert all(r.cache_hit is False for r in results)


@pytest.mark.asyncio
async def test_execute_caches_read_only_calls_when_enabled() -> None:
    """Direct execute should return cache hits for identical read calls."""
    executor = SafeToolExecutor(cache=ToolCache())
    call_count = 0

    async def fake_executor(_tool: str, _args: Mapping[str, object]) -> str:
        nonlocal call_count
        call_count += 1
        return "screen-data"

    first = await executor.execute(
        "read_screen",
        {"region": "full"},
        fake_executor,
        cacheable=True,
    )
    second = await executor.execute(
        "read_screen",
        {"region": "full"},
        fake_executor,
        cacheable=True,
    )

    assert first.success is True
    assert second.success is True
    assert second.cache_hit is True
    assert call_count == 1
