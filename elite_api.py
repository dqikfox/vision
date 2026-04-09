"""
elite_api.py — Elite endpoints for monitoring, debugging, optimization
======================================================================
Metrics dashboard, provider health, tool analytics, memory insights.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json

async def register_elite_endpoints(app: FastAPI):
    """Register all elite monitoring & debug endpoints."""
    
    from elite_metrics import metrics
    from elite_tools import tool_executor
    
    @app.get("/api/elite/metrics")
    async def get_metrics():
        """Full metrics snapshot for monitoring dashboard."""
        return JSONResponse(metrics.snapshot())
    
    @app.get("/api/elite/health")
        async def get_health_report():
        """Provider health and circuit breaker status."""
        # Will be populated when providers register their breakers
        return JSONResponse({
            "timestamp": json.dumps({"ready": True}),
            "providers": {},
        })
    
    @app.get("/api/elite/tools")
    async def get_tool_analytics():
        """Tool execution analytics and cache stats."""
        return JSONResponse(tool_executor.analytics_summary())
    
    @app.get("/api/elite/memory")
    async def get_memory_insights():
        """Memory usage and context optimization stats."""
        # Will integrate with elite_memory module
        return JSONResponse({
            "context_tokens": 0,
            "message_count": 0,
            "facts": 0,
        })
    
    @app.post("/api/elite/cache/clear")
    async def clear_tool_cache():
        """Clear tool result cache."""
        tool_executor.cache.clear()
        return JSONResponse({"ok": True})
    
    @app.post("/api/elite/tool/block/{tool_name}")
    async def block_tool(tool_name: str):
        """Block a tool from execution (safety)."""
        tool_executor.block_tool(tool_name)
        return JSONResponse({"ok": True, "blocked": tool_name})
    
    @app.post("/api/elite/tool/unblock/{tool_name}")
    async def unblock_tool(tool_name: str):
        """Unblock a previously blocked tool."""
        tool_executor.unblock_tool(tool_name)
        return JSONResponse({"ok": True, "unblocked": tool_name})
    
    @app.get("/api/elite/summary")
    async def elite_summary():
        """High-level summary for voice + UI."""
        return JSONResponse({
            "uptime": "...",
            "metrics": metrics.summary(),
            "tools": tool_executor.analytics_summary(),
        })
    
    print("[elite] endpoints registered")

# Advanced debugging mode
DEBUG_MODE = False

def set_debug(enabled: bool):
    """Enable/disable verbose debugging."""
    global DEBUG_MODE
    DEBUG_MODE = enabled
    if enabled:
        print("[elite] debug mode enabled — expect verbose logging")

def debug_log(category: str, message: str):
    """Log in debug mode."""
    if DEBUG_MODE:
        print(f"[{category}] {message}")
