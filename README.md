# Vision

**Windows-first accessibility operator with voice, desktop control, WebSocket UX, tool execution, RAG, command-center supervision, and repo-local MCP integration.**

Vision is the main runtime in this repository. It is **not** the AWS SAM sample or the `azure-search-openai-demo` subtree. When Copilot or another assistant needs repo context, anchor on the Vision docs and source files below instead of nested sample apps unless the task explicitly targets those folders.

## Start Here

1. `DOCUMENTATION_INDEX.md` - map of runtime, debugging, skills, agents, and MCP surfaces
2. `setup.md` - install, provider setup, and launch steps
3. `architecture.md` - runtime flow, WebSocket protocol, VAD, and tool loop
4. `.github/copilot-instructions.md` - always-on repo guidance for Copilot and agents

## Source of Truth

- `live_chat_app.py` - backend runtime and API surface
- `live_chat_ui.html` - main browser UI
- `vision_command_center.html` - command center UI
- `vision_runtime.py` - runtime/config helpers
- `vision_mcp_server.py` - repo-local MCP bridge
- `.vscode/mcp.json` - active workspace MCP server definitions

## What Vision Does

- Real-time voice interaction with STT, TTS, VAD, and barge-in handling
- Local and hosted LLM routing across Ollama, OpenAI, GitHub, Groq, Gemini, DeepSeek, Anthropic, xAI, and more
- Desktop/operator tools for OCR, clicking, typing, scrolling, commands, and browser-facing action broadcasts
- Command-center monitoring for runtime health, missions, skills, agents, and repo intelligence
- Repo-local MCP integration for GitHub, filesystem, LM Studio RAG, memory, sequential thinking, browser automation, and Vision-specific endpoints

## Quick Start

```powershell
cd C:\project\vision
python -m pip install -r requirements.txt
python live_chat_app.py
```

Then open:

- `http://localhost:8765` - main UI
- `http://localhost:8765/command-center` - command center

Useful checks:

```powershell
Invoke-RestMethod -Uri http://localhost:8765/api/health
python test_tools.py
python test_vision.py
```

## Copilot and Customization Layer

The repo includes a Vision-specific Copilot customization layer:

- `.github/copilot-instructions.md` - repo-wide always-on guidance
- `.vscode/copilot-instructions.md` - local mirror for humans and workspace tooling; the authoritative always-on Copilot file is `.github/copilot-instructions.md`
- `.github/skills/` - Vision-local workflows
- `.github/agents/` - specialist agents
- `C:\project\skills` - shared local reusable skills

If Copilot starts responding generically, refresh context from `DOCUMENTATION_INDEX.md`, then use the relevant repo skill such as `vision-context-ops`, `vision-context-brain`, `vision-runtime-ops`, or `mcp-recovery`.

## Important Repo Boundaries

- Treat Vision as the primary project at the repo root.
- Do not use `azure-search-openai-demo`, AWS sample docs, or other nested sandboxes as default context unless the task explicitly names them.
- Prefer existing Vision launchers, helpers, UI surfaces, and skills over inventing parallel systems.

## More Documentation

- `DOCUMENTATION_INDEX.md` - master documentation map
- `setup.md` - installation and launch flows
- `architecture.md` - runtime architecture
- `HIVE.md` - customization layer overview
- `CLAUDE.md` - Claude/Desktop operating manual for this repo
