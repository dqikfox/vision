"""
elite_metrics.py — Observability, metrics, profiling
====================================================
Real-time performance tracking, latency histograms, token usage analytics.
"""

import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict, deque
from typing import Optional

@dataclass
class Metric:
    """Single metric measurement."""
    name: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    tags: dict = field(default_factory=dict)

@dataclass
class LatencyHistogram:
    """Track latency distribution (percentiles)."""
    name: str
    measurements: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def record(self, ms: float):
        self.measurements.append(ms)
    
    def percentile(self, p: float) -> float:
        """Get percentile (e.g., 0.95 for p95)."""
        if not self.measurements:
            return 0.0
        sorted_vals = sorted(self.measurements)
        idx = int(len(sorted_vals) * p)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]
    
    def snapshot(self) -> dict:
        if not self.measurements:
            return {"name": self.name, "count": 0}
        return {
            "name": self.name,
            "count": len(self.measurements),
            "min": min(self.measurements),
            "max": max(self.measurements),
            "mean": sum(self.measurements) / len(self.measurements),
            "p50": self.percentile(0.50),
            "p95": self.percentile(0.95),
            "p99": self.percentile(0.99),
        }

class MetricsCollector:
    """Central metrics hub for Vision."""
    
    def __init__(self):
        self.latencies: dict[str, LatencyHistogram] = defaultdict(
            lambda: LatencyHistogram(name="")
        )
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}
        self.events: deque = deque(maxlen=10000)  # Event audit log
        self.session_start = time.time()
    
    def record_latency(self, name: str, ms: float):
        """Record latency measurement."""
        if name not in self.latencies:
            self.latencies[name] = LatencyHistogram(name=name)
        self.latencies[name].record(ms)
    
    def increment(self, counter: str, value: int = 1):
        """Increment counter."""
        self.counters[counter] += value
    
    def set_gauge(self, gauge: str, value: float):
        """Set gauge value."""
        self.gauges[gauge] = value
    
    def record_event(self, event_type: str, detail: str, level: str = "info"):
        """Log structured event."""
        self.events.append({
            "type": event_type,
            "detail": detail,
            "level": level,
            "timestamp": datetime.now().isoformat(),
        })
    
    def llm_request_stats(self, provider: str, model: str, tokens: int, latency_ms: float):
        """Record LLM API call metrics."""
        self.record_latency(f"llm_latency_{provider}", latency_ms)
        self.increment(f"llm_tokens_{provider}", tokens)
        self.increment(f"llm_requests_{provider}")
        self.record_event(f"llm_call", f"{provider}/{model}: {tokens} tokens, {latency_ms:.0f}ms")
    
    def tool_execution_stats(self, tool_name: str, duration_ms: float, success: bool):
        """Record tool execution metrics."""
        self.record_latency(f"tool_latency_{tool_name}", duration_ms)
        self.increment(f"tool_calls_{tool_name}")
        if success:
            self.increment(f"tool_success_{tool_name}")
        else:
            self.increment(f"tool_error_{tool_name}")
    
    def snapshot(self) -> dict:
        """Return complete metrics snapshot."""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.session_start,
            "latencies": {
                name: hist.snapshot()
                for name, hist in self.latencies.items()
            },
            "counters": dict(self.counters),
            "gauges": self.gauges,
            "recent_events": list(self.events)[-20:],
        }
    
    def summary(self) -> dict:
        """High-level summary for dashboard."""
        llm_requests = {
            k: v for k, v in self.counters.items()
            if k.startswith("llm_requests_")
        }
        tool_calls = {
            k: v for k, v in self.counters.items()
            if k.startswith("tool_calls_")
        }
        return {
            "uptime_minutes": round((time.time() - self.session_start) / 60, 1),
            "total_llm_requests": sum(llm_requests.values()),
            "total_tool_calls": sum(tool_calls.values()),
            "top_latencies": {
                k: v.snapshot()
                for k, v in sorted(
                    self.latencies.items(),
                    key=lambda x: x[1].snapshot().get("max", 0),
                    reverse=True,
                )[:5]
            },
            "error_count": self.counters.get("tool_error_total", 0),
        }

class ExecutionProfiler:
    """Profile execution time of async functions."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.elapsed_ms: float = 0.0
    
    async def __aenter__(self):
        self.start_time = time.monotonic()
        return self
    
    async def __aexit__(self, *args):
        if self.start_time:
            self.elapsed_ms = (time.monotonic() - self.start_time) * 1000
    
    def report(self) -> str:
        return f"[profile] {self.name}: {self.elapsed_ms:.1f}ms"

# Global singleton
metrics = MetricsCollector()
