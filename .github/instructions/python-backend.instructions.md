---
applyTo: "vision_*.py"
---

# Vision Python Backend Instructions

## Import Standards
Always start Python files with:
```python
from __future__ import annotations
```

Use modern type hints:
- ✅ `dict[str, Any]` not `Dict[str, Any]`
- ✅ `list[int]` not `List[int]`
- ✅ `str | None` not `Optional[str]`

## Error Handling Pattern
Always use specific exceptions with logging:
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except ConnectionError as e:
    logger.warning(f"Connection failed: {e}")
    return None
```

Never use bare `except:` - always specify the exception type.

## Configuration Management
- **Never hardcode secrets** or API keys in code
- Always read from environment variables using `os.environ.get()`
- Provide sensible defaults when appropriate
- Use `python-dotenv` for local development

Example:
```python
import os
from dotenv import load_dotenv

load_dotenv()
VISION_BASE_URL = os.environ.get("VISION_BASE_URL", "http://localhost:8765")
```

## WebSocket Message Structure
Vision uses WebSocket extensively. Follow this pattern:
```python
message = {
    "type": "state_change",  # Always include type
    "state": "listening",
    "timestamp": time.time(),
    # Additional fields as needed
}
ws.send(json.dumps(message))
```

Common message types:
- `init` - Initial connection
- `state` - State change (idle, listening, thinking, speaking)
- `volume` - Audio level update
- `model_changed` - LLM model switched
- `voice_settings` - STT/TTS configuration
- `continuous_state` - Always-on mode toggle
- `mute_state` - Microphone mute status

## MCP Tool Pattern
When creating MCP tools, follow this structure:
```python
@mcp.tool()
def tool_name(param: str) -> dict[str, Any]:
    """Clear docstring describing what the tool does."""
    try:
        result = perform_operation(param)
        return {
            "ok": True,
            "status_code": 200,
            "data": result
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
```

Always return `dict[str, Any]` with `ok` field for consistency.

## Accessibility Considerations
Vision is designed for disabled users. When writing backend code:
- Provide clear, actionable error messages (read aloud by screen readers)
- Include text descriptions for all state changes
- Log all important events for debugging accessibility issues
- Support keyboard-only workflows (no mouse required)

## Code Style
- Use Ruff formatter: `ruff format .`
- Max line length: 120 characters
- Use descriptive variable names (avoid abbreviations)
- Add docstrings for all public functions
- Type hint all function parameters and return values

## Testing
When writing tests:
- Use pytest
- Mock external services (Ollama, ElevenLabs, OpenAI)
- Test error handling paths
- Include accessibility test cases
