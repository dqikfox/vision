# Vision Documentation Index

**Project map for runtime, debugging, customization, MCP, and operator workflows.**

---

## Start Here

| Goal | Read First | Then |
|---|---|---|
| Understand the project | `README.md` | `architecture.md` |
| Install and launch locally | `setup.md` | `README.md` quick start |
| Debug runtime or voice issues | `chat_events.log` | `.github/skills/vision-debugging/SKILL.md` |
| Work on Copilot customizations | `.github/copilot-instructions.md` | `HIVE.md` |
| Extend MCP or tool access | `.vscode/mcp.json` | `vision_mcp_server.py` |
| Improve docs or repo context | `.github/skills/vision-documentation-ops/SKILL.md` | this file |
| Work on home PC or network operations | `.github/skills/vision-home-ops/SKILL.md` | `.github/copilot-instructions.md` |

---

## Core Runtime Docs

| File | Purpose | When to Use |
|---|---|---|
| `README.md` | Project overview, quick start, skills, agents, major features | First orientation |
| `setup.md` | Environment setup, dependencies, startup and troubleshooting | Installing or repairing the stack |
| `architecture.md` | Runtime architecture, data flow, protocol, memory model | Understanding backend behavior |
| `live_chat_app.py` | Source of truth for backend logic | Any real runtime change |
| `live_chat_ui.html` | Primary browser UI | UI or WebSocket integration work |
| `chat_events.log` | Main event log | First stop during debugging |
| `vision_error.log` | Runtime errors and stack traces | Investigating failures |

---

## Copilot Customization Layer

| File | Purpose | When to Use |
|---|---|---|
| `.github/copilot-instructions.md` | Always-on repo guidance for Copilot | Before changing behavior or conventions |
| `HIVE.md` | Agent swarm and customization overview | Understanding agent/skill layout |
| `.github/agents/vision-maintainer.agent.md` | Runtime/debug/code-change specialist | Backend and protocol work |
| `.github/agents/mcp-builder.agent.md` | MCP and customization specialist | MCP wiring and tool expansion |
| `.github/agents/context-steward.agent.md` | Repo-awareness and context specialist | Memory, context, and workflow continuity |
| `.github/skills/vision-context-ops/SKILL.md` | Improve Copilot itself in this repo | Repo-awareness and context upgrades |
| `.github/skills/vision-documentation-ops/SKILL.md` | Keep docs aligned with the real system | Documentation maintenance |
| `.github/skills/vision-home-ops/SKILL.md` | Home PC/network/security/backup operations | Operational maintenance workflows |

---

## Skills by Task

| Task | Skill |
|---|---|
| Start or verify the operator | `vision-runtime-ops` |
| Debug voice, provider, WebSocket, OCR, or tool failures | `vision-debugging` |
| Audit tool-calling behavior | `vision-tool-audit` |
| Add new tool support | `vision-tool-dev` |
| Improve Copilot context/memory workflow | `vision-context-ops` |
| Work on home PC, network, security, backup, or automation tasks | `vision-home-ops` |
| Keep docs synchronized | `vision-documentation-ops` |
| Expand MCP wiring | `vision-mcp-builder` |
| Repair MCP setup | `mcp-recovery` |
| Work with OpenClaw | `openclaw-getting-started` |

---

## MCP and External Context

| File / Surface | Purpose |
|---|---|
| `.vscode/mcp.json` | Workspace MCP server definitions |
| `vision_mcp_server.py` | Repo-local FastMCP bridge for Vision endpoints |
| `F:\rag-v1` | User-owned LM Studio plugin workspace available as local RAG/plugin context |

Current important MCP surfaces include:
- `github`
- `filesystem`
- `lmstudio-rag`
- `fetch`
- `git`
- `memory`
- `sequential-thinking`
- `puppeteer`
- `vision-local`

---

## Voice and Memory Surfaces

| File | Purpose |
|---|---|
| `memory.json` | Persistent memory facts, preferences, summaries, and task history |
| `elite_memory.py` | Advanced context/memory helpers available for future integration |
| `elite_voice.py` | Voice/audio helper module |
| `voice_toggle.py` | Hotkey-driven voice control helper |
| `speak.py` | Standalone speech output utility |

---

## Operational Notes

1. `live_chat_app.py` is the backend source of truth.
2. `live_chat_ui.html` is the primary UI; alternate UI files are not the default target.
3. `chat_events.log` should be checked before guessing at runtime failures.
4. Docs should be updated when skills, agents, MCP servers, runtime thresholds, or memory behavior change.
5. When documentation drifts from code, prefer updating the docs rather than preserving stale explanations.

---

## Validation Shortlist

Use the repo’s existing checks:

```powershell
python -m py_compile live_chat_app.py
python test_tools.py
python test_vision.py
```

For runtime verification, also check:
- `GET http://localhost:8765/api/health`
- `GET http://localhost:8765/api/models`
- direct tool execution via `POST /api/tool/execute`

