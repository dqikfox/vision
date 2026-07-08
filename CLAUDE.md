# CLAUDE.md

**Operating manual for assistants working in the Vision repository.**

## Read First

1. `DOCUMENTATION_INDEX.md`
2. `.github/copilot-instructions.md`
3. `README.md`
4. `setup.md`
5. `architecture.md`

## Use Vision Context, Not Nested Samples

This repository contains side projects, snapshots, and sample apps. Unless a task explicitly targets them, do **not** anchor on:

- `azure-search-openai-demo\`
- legacy AWS SAM sample content
- archived worktrees or curated data snapshots

Default to the Vision root runtime and docs instead.

## Source of Truth

- `live_chat_app.py` - backend runtime
- `live_chat_ui.html` - primary UI
- `vision_command_center.html` - command center UI
- `vision_runtime.py` - runtime/config helpers
- `vision_mcp_server.py` - repo-local MCP bridge
- `.vscode/mcp.json` - active workspace MCP servers

## Validation Surfaces

- `python test_tools.py`
- `python test_vision.py`
- `python vision_test_suite.py`
- `python -m pytest -q`
- `Invoke-RestMethod -Uri http://localhost:8765/api/health`

## Copilot Customization Layer

- `.github/copilot-instructions.md` - always-on guidance
- `.vscode/copilot-instructions.md` - workspace mirror only; `.github/copilot-instructions.md` is the authoritative always-on Copilot file
- `.github/skills/` - Vision-specific skills
- `.github/agents/` - specialist agents
- `C:\project\skills` - shared reusable skills
