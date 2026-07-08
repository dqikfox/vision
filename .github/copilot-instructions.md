# GitHub Copilot Instructions for Vision

Vision is a **Windows-first accessibility operator** with voice, desktop control, WebSocket UX, tool execution,
RAG, a command center, and MCP integration. Keep responses and changes grounded in the actual repo instead of
generic assistant behavior.

## Start Here

When context is missing or the task is broad, read in this order:

1. `DOCUMENTATION_INDEX.md`
2. `README.md`
3. `setup.md`
4. `architecture.md`
5. the nearest authoritative file for the area you are changing

Do **not** treat nested sample apps, archived worktrees, or stale scaffold docs as the default repo context. In particular, ignore `azure-search-openai-demo\`, AWS SAM sample content, and curated snapshot folders unless the task explicitly targets them.

## Source of Truth

- **Backend:** `live_chat_app.py`
- **Primary UI:** `live_chat_ui.html`
- **Command Center UI:** `vision_command_center.html`
- **Runtime/config helpers:** `vision_runtime.py`
- **Local MCP bridge:** `vision_mcp_server.py`
- **RAG runtime:** `vision_rag.py`, `vision_rag_integration.py`
- **Workspace MCP config:** `.vscode/mcp.json`

Do **not** drift to alternate entry points or duplicate systems when one of the files above already owns the behavior.

## How to Work in This Repo

- Inspect relevant files first, then make the smallest coherent change.
- Prefer existing helpers, endpoints, launchers, and UI surfaces over inventing parallel ones.
- Keep docs aligned when runtime behavior, startup flow, MCP wiring, skills, agents, or validation commands change.
- Use existing validation surfaces rather than inventing new ones.
- For debugging or maintenance, check logs before guessing: `chat_events.log` and `vision_error.log`.
- If top-level docs and nested sample content disagree, trust `DOCUMENTATION_INDEX.md`, `setup.md`, `architecture.md`, and the source-of-truth files over the sample content.

## Runtime Validation Surfaces

Use the narrowest existing validation that matches the change:

- `python test_tools.py`
- `python test_vision.py`
- `python vision_test_suite.py`
- `python -m pytest -q`
- `Invoke-RestMethod -Uri http://localhost:8765/api/health`
- `Invoke-RestMethod -Uri http://localhost:8765/api/models`

## Repo-Specific Rules to Preserve

1. New operator tools must wire through **all three** surfaces:
   - `TOOLS`
   - `_exec_tool_impl()`
   - `_EL_TOOL_NAMES`
2. `broadcast()` must iterate over `list(clients)`, not the live set directly.
3. Do **not** change the calibrated voice thresholds unless the user explicitly asks:
   - `RMS_THRESH=500`
   - `START_FRAMES=3`
   - `END_FRAMES=20`
   - `BARGE_RMS=1100`
4. Use `PIL.Image.Resampling.LANCZOS`, not deprecated `PIL.Image.LANCZOS`.
5. Catch `APITimeoutError` before `APIConnectionError`.
6. Use `asyncio.get_running_loop()`, not `get_event_loop()`.
7. Never hardcode secrets; read from env vars or existing config layers.

## Copilot Customization Guidance

- Use Vision-local skills from `.github/skills/` when the workflow is specific to this repo.
- Check `C:\project\skills` first when a workflow could be reusable across repositories.
- Use custom agents from `.github/agents/` when the task matches a specialist role.
- Treat `.vscode/mcp.json` as the source of truth for active workspace MCP servers.
- If Copilot feels under-informed for a broad task, refresh context from `DOCUMENTATION_INDEX.md` and then use the
  relevant skill such as `vision-context-ops`, `vision-context-brain`, `vision-runtime-ops`, or `vision-debugging`.

## Collaboration Style

- Lead with the result, then the key facts.
- Be specific about files, endpoints, and commands in this repo.
- Do the work instead of staying at high-level advice when the request is actionable.
- Ask only when a decision would materially change behavior.

## ULTRON Context

You are operating inside Vision under ULTRON orchestration, but repo accuracy takes priority over roleplay.
Stay grounded in the current codebase, runtime, and customization files.
