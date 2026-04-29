"""Repo-local MCP bridge for the Vision backend.

This follows the same pattern as dqikfox/mcp: expose a focused MCP server that
wraps the existing FastAPI app instead of duplicating backend logic.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

VISION_BASE_URL = os.environ.get("VISION_BASE_URL", "http://localhost:8765").rstrip("/")
VISION_MCP_TIMEOUT = float(os.environ.get("VISION_MCP_TIMEOUT", "20"))
VISION_MCP_INCLUDE_SCREENSHOT_B64 = os.environ.get("VISION_MCP_INCLUDE_SCREENSHOT_B64", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

mcp = FastMCP("Vision Local")


def _vision_request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call the running Vision backend and normalize the response shape."""
    url = f"{VISION_BASE_URL}{path}"

    try:
        with httpx.Client(timeout=VISION_MCP_TIMEOUT) as client:
            response = client.request(method, url, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip() or str(exc)
        return {
            "ok": False,
            "url": url,
            "status_code": exc.response.status_code,
            "error": detail,
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "url": url, "error": str(exc)}

    if not response.content:
        return {"ok": True, "status_code": response.status_code}

    try:
        data = response.json()
    except ValueError:
        data = {"text": response.text}

    if isinstance(data, dict):
        return {"ok": True, "status_code": response.status_code, **data}

    return {"ok": True, "status_code": response.status_code, "data": data}


def _sanitize_screenshot_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip large base64 screenshot data from MCP output to avoid context blowups."""
    sanitized = dict(payload)
    candidate_keys = ("image", "image_base64", "screenshot", "jpeg_base64", "png_base64", "data")

    for key in candidate_keys:
        value = sanitized.get(key)
        if isinstance(value, str) and len(value) > 512:
            sanitized[f"{key}_preview"] = f"{value[:80]}..."
            sanitized[f"{key}_chars"] = len(value)
            sanitized[key] = "<omitted base64 image data; set VISION_MCP_INCLUDE_SCREENSHOT_B64=1 to include>"

    return sanitized


@mcp.tool()
def vision_health() -> dict[str, Any]:
    """Return Vision component health from /api/health."""
    return _vision_request("GET", "/api/health")


@mcp.tool()
def vision_models() -> dict[str, Any]:
    """Return provider and model information from /api/models."""
    return _vision_request("GET", "/api/models")


@mcp.tool()
def vision_metrics() -> dict[str, Any]:
    """Return live system metrics from /api/metrics."""
    return _vision_request("GET", "/api/metrics")


@mcp.tool()
def vision_memory() -> dict[str, Any]:
    """Return the current Vision memory payload from /api/memory."""
    return _vision_request("GET", "/api/memory")


@mcp.tool()
def vision_add_fact(fact: str) -> dict[str, Any]:
    """Add a fact to Vision memory."""
    return _vision_request("POST", "/api/memory/fact", payload={"fact": fact})


@mcp.tool()
def vision_delete_fact(fact: str) -> dict[str, Any]:
    """Delete a fact from Vision memory."""
    return _vision_request("DELETE", "/api/memory/fact", payload={"fact": fact})


@mcp.tool()
def vision_set_model(provider: str, model: str) -> dict[str, Any]:
    """Switch the active Vision provider/model pair."""
    return _vision_request("POST", "/api/model", payload={"provider": provider, "model": model})


@mcp.tool()
def vision_execute_tool(name: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run any Vision operator tool through the existing tool execution API."""
    return _vision_request(
        "POST",
        "/api/tool/execute",
        payload={"name": name, "parameters": parameters or {}},
    )


@mcp.tool()
def vision_voices() -> dict[str, Any]:
    """Return all available TTS voices (SAPI + OneCore) from /api/voices."""
    return _vision_request("GET", "/api/voices")


@mcp.tool()
def vision_screenshot() -> dict[str, Any]:
    """Take a live desktop screenshot and return it as base64-encoded JPEG."""
    response = _vision_request("GET", "/screenshot")

    if not response.get("ok") or VISION_MCP_INCLUDE_SCREENSHOT_B64:
        return response

    return _sanitize_screenshot_response(response)


@mcp.tool()
def vision_wake_word(enabled: bool) -> dict[str, Any]:
    """Enable or disable wake-word activation mode."""
    return _vision_request("POST", "/api/wake-word", payload={"enabled": enabled})


@mcp.tool()
def vision_recall(query: str = "") -> dict[str, Any]:
    """Search Vision memory facts. Pass an optional query to filter results."""
    return _vision_request(
        "POST",
        "/api/tool/execute",
        payload={"name": "recall", "parameters": {"query": query} if query else {}},
    )


@mcp.tool()
def vision_kb_status() -> dict[str, Any]:
    """Return Vision RAG knowledge-base status and index metadata."""
    return _vision_request("GET", "/api/rag/status")


@mcp.tool()
def vision_kb_index(max_files: int = 0, chunk_size: int = 1400, overlap: int = 220) -> dict[str, Any]:
    """Build or rebuild the Vision RAG index from the configured corpus."""
    return _vision_request(
        "POST",
        "/api/rag/index",
        payload={
            "max_files": max_files,
            "chunk_size": chunk_size,
            "overlap": overlap,
        },
    )


@mcp.tool()
def vision_kb_search(query: str, limit: int = 8, include_content: bool = True) -> dict[str, Any]:
    """Search the Vision RAG index for grounded retrieval context."""
    return _vision_request(
        "POST",
        "/api/rag/search",
        payload={"query": query, "limit": limit, "include_content": include_content},
    )


@mcp.tool()
def vision_kb_export_training_data(max_examples: int = 0) -> dict[str, Any]:
    """Export indexed corpus as JSONL datasets for training and KB ingestion."""
    return _vision_request(
        "POST",
        "/api/rag/export-training",
        payload={"max_examples": max_examples},
    )


if __name__ == "__main__":
    mcp.run()
