"""
elite_tools.py — Smart tool execution, caching, batching, safety
=================================================================
Parallel execution, result caching, tool analytics, execution safety.
"""

import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional


@dataclass
class ToolResult:
    """Standard tool execution result."""
    tool: str
    args: dict
    result: str
    duration_ms: float
    success: bool
    error: Optional[str] = None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    cache_hit: bool = False

class ToolCache:
    """Cache tool results with TTL."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: dict[str, tuple[str, float]] = {}  # hash → (result, expiry_time)
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def _key(self, tool: str, args: dict) -> str:
        """Generate cache key from tool + args."""
        content = f"{tool}:{json.dumps(args, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, tool: str, args: dict) -> Optional[str]:
        """Retrieve cached result if valid."""
        key = self._key(tool, args)
        if key in self.cache:
            result, expiry = self.cache[key]
            if datetime.now().timestamp() < expiry:
                self.hits += 1
                return result
            else:
                del self.cache[key]
        self.misses += 1
        return None
    
    def set(self, tool: str, args: dict, result: str):
        """Cache result with TTL."""
        key = self._key(tool, args)
        expiry = datetime.now().timestamp() + self.ttl_seconds
        self.cache[key] = (result, expiry)
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
    
    def stats(self) -> dict:
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
    
    def __init__(self, cache: ToolCache = None):
        self.cache = cache or ToolCache()
        self.analytics: dict[str, list[float]] = defaultdict(list)  # tool → durations
        self.max_parallel = 5
        self.semaphore = asyncio.Semaphore(self.max_parallel)
        self.blocked_tools = set()
    
    async def execute(
        self,
        tool: str,
        args: dict,
        executor_fn: Callable,
        cacheable: bool = True,
        timeout_seconds: float = 30.0,
    ) -> ToolResult:
        """Execute tool with safety and caching."""
        
        # Safety check
        if tool in self.blocked_tools:
            return ToolResult(
                tool=tool,
                args=args,
                result="",
                duration_ms=0,
                success=False,
                error=f"Tool {tool} is blocked",
            )
        
        # Cache check
        if cacheable:
            cached = self.cache.get(tool, args)
            if cached:
                return ToolResult(
                    tool=tool,
                    args=args,
                    result=cached,
                    duration_ms=0,
                    success=True,
                    cache_hit=True,
                )
        
        # Execute with rate limiting
        async with self.semaphore:
            import time
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
                    args=args,
                    result=result,
                    duration_ms=duration_ms,
                    success=True,
                )
            except asyncio.TimeoutError:
                return ToolResult(
                    tool=tool,
                    args=args,
                    result="",
                    duration_ms=(time.monotonic() - start) * 1000,
                    success=False,
                    error=f"Timeout after {timeout_seconds}s",
                )
            except Exception as e:
                return ToolResult(
                    tool=tool,
                    args=args,
                    result="",
                    duration_ms=(time.monotonic() - start) * 1000,
                    success=False,
                    error=str(e)[:200],
                )
    
    async def batch_execute(
        self,
        tools: list[tuple[str, dict]],
        executor_fn: Callable,
        fail_fast: bool = False,
    ) -> list[ToolResult]:
        """Execute multiple tools in parallel (where safe)."""
        # Read-only tools can run in parallel; state-changing tools run sequentially
        read_only = {"read_screen", "screenshot", "screenshot_region", "ocr_region",
                     "get_color", "get_active_window", "get_system_info", "find_files"}
        
        parallel_batch = []
        sequential_batch = []
        
        for tool, args in tools:
            if tool in read_only:
                parallel_batch.append((tool, args))
            else:
                sequential_batch.append((tool, args))
        
        results = []
        
        # Execute parallel batch
        if parallel_batch:
            parallel_tasks = [
                self.execute(tool, args, executor_fn)
                for tool, args in parallel_batch
            ]
            results.extend(await asyncio.gather(*parallel_tasks, return_exceptions=True))
        
        # Execute sequential batch
        for tool, args in sequential_batch:
            result = await self.execute(tool, args, executor_fn)
            results.append(result)
            if fail_fast and not result.success:
                break
        
        return results
    
    def block_tool(self, tool: str):
        """Block a tool from execution."""
        self.blocked_tools.add(tool)
    
    def unblock_tool(self, tool: str):
        """Unblock a tool."""
        self.blocked_tools.discard(tool)
    
    def analytics_summary(self) -> dict:
        """Tool execution analytics."""
        return {
            "cache": self.cache.stats(),
            "tools": {
                tool: {
                    "executions": len(durations),
                    "avg_duration_ms": round(sum(durations) / len(durations), 2),
                    "min_ms": round(min(durations), 2),
                    "max_ms": round(max(durations), 2),
                }
                for tool, durations in self.analytics.items()
                if durations
            },
            "blocked": list(self.blocked_tools),
        }

# Global tool executor
tool_executor = SafeToolExecutor()
