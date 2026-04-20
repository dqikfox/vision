# VISION — Copilot Instructions (Core)

You are operating inside the **VISION Universal Accessibility Operator** — a production-grade Windows-first AI system for voice/text computer control.

---

## Quick Identity

| Component | Location |
|-----------|----------|
| **Backend** | `live_chat_app.py` — FastAPI + WebSocket on `http://localhost:8765` |
| **Primary UI** | `live_chat_ui.html` — **ONLY use this file** (ignore v2/v3/backup) |
| **Memory** | `memory.json` — persistent facts, user profile |
| **Logs** | `chat_events.log` — check first when debugging |
| **Health** | `GET /api/health` — runtime status check |

---

## Critical Rules (Never Break)

1. **Never print/log API key values** — check existence only
2. **Never change VAD thresholds** (`RMS_THRESH=500`, `BARGE_RMS=1100`) without explicit instruction
3. **Use `asyncio.get_running_loop()`** — never `get_event_loop()`
4. **Use `loop.run_in_executor(None, fn)`** for blocking calls in async context
5. **New tools need 3 changes**: `TOOLS` schema + `exec_tool` handler + `_EL_TOOL_NAMES`
6. **Primary UI only**: edit `live_chat_ui.html`, never alternate versions
7. **Snapshot clients before broadcast**: `for ws in list(clients):`

---

## Skills Quick Reference

| Problem | Invoke |
|---------|--------|
| Start/stop Vision or check health | `@vision-runtime-ops` |
| Voice/OCR/tool not working | `@vision-debugging` |
| Add new tool | `@vision-tool-dev` |
| Code review needed | `@vision-code-review` |
| Fix type/mypy issues | `@vision-type-safety` |
| Home network/backup/security | `@vision-home-ops` |
| Docs out of sync | `@vision-documentation-ops` |
| Add MCP server | `@vision-mcp-builder` |
| Repo maintenance | `@vision-context-ops` or `@vision-context-brain` |

---

## Agent Quick Reference

| Task | Invoke |
|------|--------|
| Runtime issues, voice broken, tool fails | `@Vision Maintainer` |
| OpenClaw setup/integration | `@OpenClaw Operator` |
| MCP/agent customization | `@MCP Builder` |
| Copilot context/memory issues | `@Context Steward` |
| Home PC/network/security | `@Home Ops Steward` |
| Pre-merge review | `@Code Review Agent` |
| Behavior-preserving refactor | `@Refactor Agent` |

---

## Testing Commands

```powershell
# Quick tool smoke test
python test_tools.py

# Full integration test
python test_vision.py

# Direct tool execution
Invoke-RestMethod -Uri http://localhost:8765/api/tool/execute -Method Post `
  -Body '{"name":"screenshot","parameters":{}}' -ContentType "application/json"
```

---

## Common Mistakes to Avoid

| Mistake | Correct |
|---------|---------|
| `asyncio.get_event_loop()` | `asyncio.get_running_loop()` |
| `import shutil` inside function | Import at module top |
| Only adding `exec_tool` handler | Also add TOOLS schema + `_EL_TOOL_NAMES` |
| Printing `e` in error handler | Use `_tool_err("tool_name", e)` |
| Broadcasting without `list(clients)` | `for ws in list(clients):` |

---

## Tool Pattern Template

```python
elif name == "my_tool":
    param = args.get("param", "default")
    try:
        result = await loop.run_in_executor(None, lambda: _blocking_op(param))
        return f"Success: {result}"
    except Exception as e:
        return _tool_err("my_tool", e)
```

---

## Need Details?

- **Full technical reference**: See `copilot-reference.md`
- **Interaction examples**: See `copilot-examples.md`
- **Architecture deep-dive**: See `architecture.md`
- **Project roadmap**: See `PROJECT.md`

---

## Elite Execution Protocol

Use this protocol for high-impact work in both VS Code chat and CLI agent flows.

1. **Execution-first**
  - If the request is implementable, act immediately instead of only proposing.
  - Prefer tool-backed verification over assumptions.

2. **Tool leverage**
  - Use search and read tools to map context before edits.
  - Run targeted validation commands (`test_tools.py`, `test_vision.py`, or focused checks) after edits.

3. **Memory discipline**
  - Persist durable, non-secret project facts for future sessions.
  - Never store API key values, tokens, or passwords.
  - Store only secret variable names and locations when needed.

4. **Change quality**
  - Keep edits minimal and coherent.
  - Preserve existing architecture patterns unless explicitly refactoring.
  - Report: what changed, what was verified, and what remains unverified.

5. **Security and safety**
  - Immediately flag hardcoded secrets or unsafe patterns.
  - Avoid destructive commands unless explicitly requested by the user.
