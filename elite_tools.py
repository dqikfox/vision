"""
elite_tools.py — Smart tool execution, caching, batching, safety
=================================================================
Parallel execution, result caching, tool analytics, execution safety.
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolResult:
    """Standard tool execution result."""

    tool: str
    args: dict[str, object]
    result: str
    duration_ms: float
    success: bool
    error: str | None = None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    cache_hit: bool = False


class ToolCache:
    """Cache tool results with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        # hash -> (result, expiry_time)
        self.cache: dict[str, tuple[str, float]] = {}
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _key(self, tool: str, args: Mapping[str, object]) -> str:
        """Generate cache key from tool + args."""
        content = f"{tool}:{json.dumps(args, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, tool: str, args: Mapping[str, object]) -> str | None:
        """Retrieve cached result if valid."""
        key = self._key(tool, args)
        if key in self.cache:
            result, expiry = self.cache[key]
            if datetime.now().timestamp() < expiry:
                self.hits += 1
                return result
            del self.cache[key]
        self.misses += 1
        return None

    def set(self, tool: str, args: Mapping[str, object], result: str) -> None:
        """Cache result with TTL."""
        key = self._key(tool, args)
        expiry = datetime.now().timestamp() + self.ttl_seconds
        self.cache[key] = (result, expiry)

    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()

    def stats(self) -> dict[str, object]:
        """Cache hit/miss statistics."""
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 3) if total > 0 else 0.0,
            "size": len(self.cache),
        }


class SafeToolExecutor:
    """Execute tools with safety checks and batching."""

    def __init__(self, cache: ToolCache | None = None):
        self.cache = cache or ToolCache()
        # tool -> durations
        self.analytics: dict[str, list[float]] = defaultdict(list)
        self.max_parallel = 5
        self.semaphore = asyncio.Semaphore(self.max_parallel)
        self.blocked_tools: set[str] = set()

    async def execute(
        self,
        tool: str,
        args: Mapping[str, object],
        executor_fn: Callable[[str, Mapping[str, object]], Awaitable[str]],
        cacheable: bool = True,
        timeout_seconds: float = 30.0,
    ) -> ToolResult:
        """Execute tool with safety and caching."""
        if tool in self.blocked_tools:
            return ToolResult(
                tool=tool,
                args=dict(args),
                result="",
                duration_ms=0,
                success=False,
                error=f"Tool {tool} is blocked",
            )

        if cacheable:
            cached = self.cache.get(tool, args)
            if cached:
                return ToolResult(
                    tool=tool,
                    args=dict(args),
                    result=cached,
                    duration_ms=0,
                    success=True,
                    cache_hit=True,
                )

        async with self.semaphore:
            start = time.monotonic()
            try:
                result = await asyncio.wait_for(
                    executor_fn(tool, args),
                    timeout=timeout_seconds,
                )
                duration_ms = (time.monotonic() - start) * 1000
                if cacheable:
                    self.cache.set(tool, args, result)
                self.analytics[tool].append(duration_ms)
                return ToolResult(
                    tool=tool,
                    args=dict(args),
                    result=result,
                    duration_ms=duration_ms,
                    success=True,
                )
            except TimeoutError:
                return ToolResult(
                    tool=tool,
                    args=dict(args),
                    result="",
                    duration_ms=(time.monotonic() - start) * 1000,
                    success=False,
                    error=f"Timeout after {timeout_seconds}s",
                )
            except (
                OSError,
                ValueError,
                RuntimeError,
                TypeError,
                KeyError,
            ) as e:
                return ToolResult(
                    tool=tool,
                    args=dict(args),
                    result="",
                    duration_ms=(time.monotonic() - start) * 1000,
                    success=False,
                    error=str(e)[:200],
                )

    async def batch_execute(
        self,
        tools: Sequence[tuple[str, Mapping[str, object]]],
        executor_fn: Callable[[str, Mapping[str, object]], Awaitable[str]],
        fail_fast: bool = False,
    ) -> list[ToolResult]:
        """Execute multiple tools in parallel where safe."""
        read_only = {
            "read_screen",
            "screenshot",
            "screenshot_region",
            "ocr_region",
            "get_color",
            "get_active_window",
            "get_system_info",
            "find_files",
        }

        parallel_batch = [(t, a) for t, a in tools if t in read_only]
        sequential_batch = [(t, a) for t, a in tools if t not in read_only]

        results: list[ToolResult] = []

        if parallel_batch:
            tasks = [self.execute(t, a, executor_fn, cacheable=True) for t, a in parallel_batch]
            parallel_results = await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )
            for i, batch_result in enumerate(parallel_results):
                if isinstance(batch_result, BaseException):
                    tool, args = parallel_batch[i]
                    results.append(
                        ToolResult(
                            tool=tool,
                            args=dict(args),
                            result="",
                            duration_ms=0,
                            success=False,
                            error=str(batch_result)[:200],
                        )
                    )
                else:
                    assert isinstance(batch_result, ToolResult)
                    results.append(batch_result)

        for tool, args in sequential_batch:
            result = await self.execute(
                tool,
                args,
                executor_fn,
                cacheable=False,
            )
            results.append(result)
            if fail_fast and not result.success:
                break

        return results

    def block_tool(self, tool: str) -> None:
        """Block a tool from execution."""
        self.blocked_tools.add(tool)

    def unblock_tool(self, tool: str) -> None:
        """Unblock a tool."""
        self.blocked_tools.discard(tool)

    def analytics_summary(self) -> dict[str, object]:
        """Tool execution analytics."""
        return {
            "cache": self.cache.stats(),
            "tools": {
                tool: {
                    "executions": len(d),
                    "avg_duration_ms": round(sum(d) / len(d), 2),
                    "min_ms": round(min(d), 2),
                    "max_ms": round(max(d), 2),
                }
                for tool, d in self.analytics.items()
                if d
            },
            "blocked": list(self.blocked_tools),
        }


# Global tool executor
tool_executor = SafeToolExecutor()
