# Vision Tool Development Skill

Use this skill to add new tools to the VISION operator.

## Architecture
Tools are defined in `live_chat_app.py` in three places:
1. **`TOOLS` list** (~line 1552) — OpenAI-format JSON schema for the LLM
2. **`_exec_tool_impl()`** (~line 2570) — Python handler that executes the tool
3. **`_EL_TOOL_NAMES`** (~line 5246) — list of names forwarded to ElevenLabs ConvAI agent

## Adding a New Tool — Checklist

### Step 1: Define schema in TOOLS list
```python
{
  "type": "function",
  "function": {
    "name": "my_tool",
    "description": "Clear description of what it does and when to use it.",
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {"type": "string", "description": "What this param does"},
        "param2": {"type": "integer", "description": "...", "default": 10}
      },
      "required": ["param1"]
    }
  }
}
```

### Step 2: Add handler in _exec_tool_impl()
```python
elif name == "my_tool":
    param1 = args.get("param1", "")
    param2 = args.get("param2", 10)
    try:
        result = await loop.run_in_executor(None, lambda: blocking_op(param1))
        return f"Result: {result}"
    except Exception as e:
        return _tool_err("my_tool", e)
```

### Step 3: Add to _EL_TOOL_NAMES
```python
_EL_TOOL_NAMES: list[str] = [
    ...,
    "my_tool",
]
```

## Rules
- Always use `await loop.run_in_executor(None, blocking_fn)` for CPU/IO-bound ops
- Return a string from exec_tool — the LLM sees this as the tool result
- Use `_tool_err(name, e)` in every except block — never raw `f"Error: {e}"`
- If the tool takes a screenshot, set `_last_screenshot_b64` for vision injection
- For long operations, broadcast intermediate status via `await broadcast({...})`
- Test with: `Invoke-RestMethod -Uri http://localhost:8765/api/tool/execute -Method Post -Body '{"name":"my_tool","parameters":{"param1":"test"}}' -ContentType "application/json"`

## Common Patterns
```python
# Run blocking code off the event loop
result = await loop.run_in_executor(None, lambda: some_blocking_call())

# Broadcast UI update mid-tool
await broadcast({"type": "status", "text": "Working..."})

# Access clipboard
import pyperclip
text = pyperclip.paste()

# Run shell command
proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
out, _ = await proc.communicate()
```
