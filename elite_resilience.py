"""
elite_resilience.py — Provider resilience & circuit breaker patterns
====================================================================
Intelligent fallback chains, retry logic with exponential backoff, provider health monitoring.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing; reject requests
    HALF_OPEN = "half_open"  # Testing; allow single request

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5           # Failures before opening
    success_threshold: int = 2           # Successes to close (from half-open)
    timeout_seconds: float = 60.0        # Time before half-open retry
    
@dataclass
class ProviderHealth:
    provider: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_response_time_ms: float = 0.0
    total_requests: int = 0
    total_errors: int = 0
    error_rate: float = 0.0
    
class CircuitBreaker(Generic[T]):
    """Intelligent circuit breaker for provider resilience."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.health = ProviderHealth(provider=name)
        self._lock = asyncio.Lock()
    
    async def call(self, fn: Callable, *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.health.state == CircuitState.OPEN:
                if time.time() - self.health.last_failure_time > self.config.timeout_seconds:
                    self.health.state = CircuitState.HALF_OPEN
                    self.health.success_count = 0
                else:
                    raise Exception(f"[circuit] {self.name} is OPEN (backoff)")
        
        start = time.monotonic()
        try:
            result = await fn(*args, **kwargs)
            await self._record_success(time.monotonic() - start)
            return result
        except Exception as e:
            await self._record_failure()
            raise
    
    async def _record_success(self, elapsed: float):
        async with self._lock:
            self.health.last_response_time_ms = elapsed * 1000
            self.health.total_requests += 1
            
            if self.health.state == CircuitState.HALF_OPEN:
                self.health.success_count += 1
                if self.health.success_count >= self.config.success_threshold:
                    self.health.state = CircuitState.CLOSED
                    self.health.failure_count = 0
            else:
                self.health.failure_count = max(0, self.health.failure_count - 1)
            
            self.health.error_rate = (
                self.health.total_errors / self.health.total_requests 
                if self.health.total_requests > 0 else 0.0
            )
    
    async def _record_failure(self):
        async with self._lock:
            self.health.last_failure_time = time.time()
            self.health.failure_count += 1
            self.health.total_errors += 1
            self.health.total_requests += 1
            
            if self.health.failure_count >= self.config.failure_threshold:
                self.health.state = CircuitState.OPEN
            
            self.health.error_rate = (
                self.health.total_errors / self.health.total_requests
            )
    
    async def health_check(self) -> dict:
        """Return health snapshot for monitoring."""
        async with self._lock:
            return {
                "provider": self.name,
                "state": self.health.state.value,
                "error_rate": round(self.health.error_rate, 3),
                "failure_count": self.health.failure_count,
                "total_requests": self.health.total_requests,
                "last_response_time_ms": round(self.health.last_response_time_ms, 1),
            }

class FallbackChain:
    """Execute multiple strategies with intelligent fallback."""
    
    def __init__(self, name: str, strategies: list[tuple[str, Callable]], 
                 allow_partial: bool = False):
        self.name = name
        self.strategies = strategies  # [(name, fn), ...]
        self.allow_partial = allow_partial
        self.breakers = {s[0]: CircuitBreaker(s[0]) for s in strategies}
        self.attempt_log: list[dict] = []
    
    async def execute(self, *args, **kwargs) -> Any:
        """Try strategies in order until one succeeds."""
        self.attempt_log.clear()
        
        for strategy_name, fn in self.strategies:
            breaker = self.breakers[strategy_name]
            try:
                result = await breaker.call(fn, *args, **kwargs)
                self.attempt_log.append({
                    "strategy": strategy_name,
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                })
                return result
            except Exception as e:
                self.attempt_log.append({
                    "strategy": strategy_name,
                    "status": "failed",
                    "error": str(e)[:100],
                    "timestamp": datetime.now().isoformat(),
                })
        
        log_str = json.dumps(self.attempt_log, indent=2)
        raise Exception(f"[fallback] {self.name}: all strategies exhausted\n{log_str}")
    
    async def health_report(self) -> dict:
        """Detailed health report for all strategies."""
        return {
            "chain": self.name,
            "strategies": [
                await breaker.health_check()
                for breaker in self.breakers.values()
            ],
            "recent_attempts": self.attempt_log[-10:],  # Last 10
        }

async def retry_with_backoff(
    fn: Callable,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> Any:
    """Retry with exponential backoff and optional jitter."""
    import random
    
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as e:
            if attempt >= max_retries:
                raise
            
            delay = min(base_delay * (2 ** attempt), max_delay)
            if jitter:
                delay *= (0.5 + random.random())
            
            await asyncio.sleep(delay)
