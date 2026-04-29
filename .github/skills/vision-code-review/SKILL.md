---
name: vision-code-review
description: 'Full code review for Vision — correctness, security, types, async safety, and Vision-specific patterns. Use before merging any significant change.'
argument-hint: 'File or area to review. E.g. "review exec_tool changes" or "review the new STT provider".'
user-invocable: true
---

# Vision Code Review

## Quick checks (run first)
```powershell
python -m flake8 c:\project\vision\ --count 2>&1
python -m mypy c:\project\vision\live_chat_app.py --ignore-missing-imports 2>&1
python test_tools.py 2>&1
```

## Vision-specific review points

### Tool handler completeness
Every new tool needs ALL THREE:
1. Entry in `TOOLS` list (JSON schema)
2. Handler in `_exec_tool_impl()` 
3. Name in `_EL_TOOL_NAMES` list

Missing any one silently breaks ElevenLabs ConvAI.

### Async safety
```python
# ❌ blocks event loop
result = requests.get(url)
time.sleep(1)

# ✅ correct
result = await httpx_client.get(url)
await asyncio.sleep(1)
```

### broadcast() safety
```python
# ❌ RuntimeError if client disconnects mid-loop
for ws in clients:
    await ws.send_text(...)

# ✅ snapshot first
for ws in list(clients):
    await ws.send_text(...)
```

### Exception ordering
```python
# ❌ APITimeoutError never reached (it's a subclass of APIConnectionError)
except openai.APIConnectionError: ...
except openai.APITimeoutError: ...

# ✅ subclass first
except openai.APITimeoutError: ...
except openai.APIConnectionError: ...
```

### Type annotations
- All public functions need return types
- `dict` → `dict[str, Any]`
- `asyncio.Queue` → `asyncio.Queue[np.ndarray]`
- `asyncio.Task` → `asyncio.Task[None]`
