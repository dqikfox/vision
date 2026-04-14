# Project Guidelines

## Scope
VISION is a Windows-first accessibility operator for full PC control via voice and text.
Treat single-user home PC and network reliability/security/automation as first-class goals.

## Code Style
- Python line length is 120; format with Ruff.
- Keep imports at module top-level (no inline imports in handlers).
- Use type hints for new public functions.
- In async code, use `asyncio.get_running_loop()`.

## Architecture
- Backend source of truth: `live_chat_app.py` (FastAPI + WebSocket, port 8765).
- Primary UI: `live_chat_ui.html` only; do not edit alternate UI files unless explicitly asked.
- Core pipeline is Perception -> Brain -> Action.
- Persistent memory file: `memory.json`.
- Primary runtime log for debugging: `chat_events.log`.

## Build and Test
- Setup and run commands are documented in `README.md` and `setup.md`.
- Canonical tests:
  - `python test_tools.py` (tool smoke tests)
  - `python test_vision.py` (integration tests)

## Context Refresh Workflow
- Start with `DOCUMENTATION_INDEX.md` when you need the fastest route to the right runtime, debugging, or customization doc.
- For runtime work, refresh `README.md`, `setup.md`, and `architecture.md` as needed, and check `chat_events.log` before guessing.
- For Copilot customization work, read `.github/copilot-instructions.md`, the relevant skill or agent doc in `.github/`, and `HIVE.md` together before editing.
- For multi-step work, create or update the session `plan.md` and mirror execution state into SQL `todos` / `todo_deps` so long tasks stay recoverable.
- Only store durable memory when the fact is verified, reusable, and likely to matter in future sessions.
- If LM Studio or local retrieval is in scope, inspect `RAG_PLUGIN_WORKSPACE` first and keep platform-specific fallback guidance aligned with the docs.

## Critical Conventions
- Do not expose API keys or secrets in logs, code, or responses.
- Do not change calibrated VAD/barge-in thresholds unless explicitly requested.
- Keep chat-mode and operator-mode streaming paths separate.
- For blocking operations inside async handlers, use `await loop.run_in_executor(None, fn)`.
- Use `_tool_err(...)` for tool-handler errors.
- In WebSocket broadcasts, iterate over `list(clients)` (snapshot) to avoid disconnect race errors.

### Tooling Integrity Rule (must-follow)
When adding or renaming a tool, update all three surfaces together:
1. `TOOLS` schema
2. `exec_tool` / `_exec_tool_impl` handler
3. `_EL_TOOL_NAMES`

Missing one of the three can silently break ElevenLabs ConvAI tool usage.

## Documentation Map (Link, Don't Embed)
- Overview and quick start: `README.md`
- Setup and environment: `setup.md`
- Runtime architecture: `architecture.md`
- Endpoints, protocol, and components: `components.md`
- Agent/skill ecosystem: `HIVE.md`
- Documentation index: `DOCUMENTATION_INDEX.md`
- Project roadmap/context: `PROJECT.md`

Keep this file concise and task-driving. Put detailed behavior in the docs above and link to them.
