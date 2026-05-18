---
applyTo: "vision_mcp_server.py"
---

# Vision MCP Server Instructions

## MCP Server Architecture
Vision's MCP server (`vision_mcp_server.py`) is a **thin bridge** to the main FastAPI backend. It does NOT duplicate backend logic - it wraps existing HTTP endpoints using `httpx`.

## Design Principles
1. **Thin wrapper**: Use `_vision_request()` helper for all backend calls
2. **Consistent responses**: Always return `dict[str, Any]` with `ok` field
3. **Error handling**: Catch and normalize HTTP errors gracefully
4. **Screenshot sanitization**: Strip large base64 data unless explicitly requested
5. **Timeout configuration**: Use `VISION_MCP_TIMEOUT` environment variable

## Tool Function Pattern
```python
@mcp.tool()
def vision_tool_name(param: str) -> dict[str, Any]:
    """Clear docstring: What this tool does and when to use it.

    Args:
        param: Description of parameter

    Returns:
        dict with ok, status_code, and data fields
    """
    return _vision_request("GET", f"/api/endpoint/{param}")
```

## Response Normalization
The `_vision_request()` helper normalizes all responses to:
```python
{
    "ok": True,           # Success indicator
    "status_code": 200,   # HTTP status
    "data": {...}         # Response payload
}
```

Or on error:
```python
{
    "ok": False,
    "url": "http://...",
    "status_code": 500,
    "error": "Error message"
}
```

## Screenshot Handling
Large base64 image data can bloat context. Use `_sanitize_screenshot_response()` for tools that return images:
```python
@mcp.tool()
def vision_screenshot() -> dict[str, Any]:
    """Capture screenshot from Vision backend."""
    result = _vision_request("POST", "/api/screenshot")
    if result.get("ok"):
        result = _sanitize_screenshot_response(result)
    return result
```

This will replace large base64 strings with:
```python
{
    "image": "<omitted base64 image data; set VISION_MCP_INCLUDE_SCREENSHOT_B64=1 to include>",
    "image_preview": "iVBORw0KGgoAAAANSUhEUgAA...",
    "image_chars": 245678
}
```

## Environment Variables
Always respect these environment variables:
- `VISION_BASE_URL` - Backend URL (default: http://localhost:8765)
- `VISION_MCP_TIMEOUT` - Request timeout in seconds (default: 20)
- `VISION_MCP_INCLUDE_SCREENSHOT_B64` - Include full screenshots (default: 0)

```python
VISION_BASE_URL = os.environ.get("VISION_BASE_URL", "http://localhost:8765").rstrip("/")
VISION_MCP_TIMEOUT = float(os.environ.get("VISION_MCP_TIMEOUT", "20"))
```

## Tool Categories

### System Health Tools
- `vision_health()` - Component health status
- `vision_metrics()` - Live system metrics (CPU, memory, etc.)

### Model Management Tools
- `vision_models()` - Provider and model information
- `vision_switch_model(provider, model)` - Change active LLM

### Memory/Context Tools
- `vision_memory()` - Current memory payload
- `vision_add_memory(content, tags)` - Add to memory

### Tool Execution
- `vision_execute_tool(tool_name, **kwargs)` - Execute Vision backend tool
- Always validate tool_name against available tools first

## Error Messages
Provide actionable error messages for external callers:
```python
if not _ws_connected:
    return {
        "ok": False,
        "error": "Vision backend is not running. Start with: python live_chat_app.py"
    }
```

## Testing MCP Tools
Test tools from command line:
```bash
# Using MCP stdio protocol
echo '{"method":"tools/call","params":{"name":"vision_health"}}' | python vision_mcp_server.py
```

Or from Python:
```python
from vision_mcp_server import vision_health
result = vision_health()
assert result["ok"] is True
```

## Adding New Tools
When adding a new MCP tool:
1. Add corresponding backend endpoint first (in main FastAPI app)
2. Add MCP tool that wraps the endpoint
3. Document the tool's purpose clearly in docstring
4. Add example usage in docstring
5. Handle errors gracefully
6. Update README.md with new tool

Example:
```python
@mcp.tool()
def vision_set_voice_provider(provider: str, voice_id: str | None = None) -> dict[str, Any]:
    """Switch TTS voice provider for Vision.

    Args:
        provider: Voice provider name (e.g., 'elevenlabs', 'openai', 'browser')
        voice_id: Optional voice ID/name for the provider

    Returns:
        Success status and new voice configuration

    Example:
        >>> vision_set_voice_provider("elevenlabs", "EXAVITQu4vr4xnSDxMaL")
        {"ok": True, "provider": "elevenlabs", "voice": "EXAVITQu4vr4xnSDxMaL"}
    """
    payload = {"provider": provider}
    if voice_id:
        payload["voice_id"] = voice_id
    return _vision_request("POST", "/api/voice/set_provider", payload=payload)
```

## MCP Server Metadata
Keep server metadata up to date:
```python
mcp = FastMCP("Vision Local")
# Update version, description, capabilities as features are added
```

## Integration Testing
Ensure MCP server works with:
- **OpenClaw Gateway**: stdio MCP integration
- **VS Code**: GitHub Copilot with MCP extension
- **Claude Desktop**: MCP server configuration
- **OpenHarness**: Multi-agent orchestration

Test configuration:
```json
{
  "mcpServers": {
    "vision": {
      "command": "python",
      "args": ["vision_mcp_server.py"],
      "env": {
        "VISION_BASE_URL": "http://localhost:8765"
      }
    }
  }
}
```
