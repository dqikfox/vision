# Vision workspace Copilot instructions

This file is a **workspace mirror** for humans and local tooling. The authoritative always-on Copilot instruction file for this repo is `.github/copilot-instructions.md`.

Use this workspace as a **repo-aware Vision operator codebase**, not a generic project.

## Refresh Order

1. `DOCUMENTATION_INDEX.md`
2. `.github/copilot-instructions.md`
3. `README.md`
4. the nearest source-of-truth file for the task

Do **not** anchor on nested sample apps, archived worktrees, or stale scaffold docs as your default context. Ignore `azure-search-openai-demo\`, AWS SAM sample content, and curated snapshot folders unless the task explicitly targets them.

## Source of Truth

- `live_chat_app.py` - backend logic
- `live_chat_ui.html` - primary UI
- `vision_command_center.html` - command center UI
- `vision_runtime.py` - runtime/config helpers
- `vision_mcp_server.py` - local MCP bridge
- `.vscode/mcp.json` - active workspace MCP servers

## Non-Generic Behavior

- Prefer existing Vision patterns, helpers, launchers, and skills over generic suggestions.
- Use `.github/skills/` and `.github/agents/` when the task matches a repo-defined workflow.
- Treat `.vscode/mcp.json` as the MCP source of truth.
- Preserve the calibrated voice thresholds and the existing tool-registration wiring.
- Reference concrete files, endpoints, and commands from this repo in responses.
- If documentation conflicts, trust `DOCUMENTATION_INDEX.md`, `setup.md`, `architecture.md`, and the source-of-truth runtime files over nested samples.
