# Vision Documentation Index

**Project map for runtime, debugging, customization, MCP, and operator workflows.**

---

## Start Here

| Goal | Read First | Then |
|---|---|---|
| Understand the project | `README.md` | `architecture.md` |
| Install and launch locally | `setup.md` | `README.md` quick start |
| Launch and monitor the repo intelligence stack | `http://localhost:8765/command-center` | `README.md` |
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
| `vision_command_center.html` | Secondary command-center GUI for launch, monitoring, and repo intelligence control | Operating the broader Vision stack |
| `vision_command_center_config.json` | Command-center profile, theme, launcher preferences, explicit Ollama host/mode/origins, and Ollama models path | Changing non-sensitive UI/launcher behavior |
| `vision_automation_state.json` | Persistent automation mission and routine run history | Inspecting or validating command-center automation outcomes |
| `launch_vision.ps1` | Windows launcher with health checks, doctor-aware startup, configurable Ollama access mode, and managed Ollama model-store startup | Starting or repairing the local stack |
| `vision_master_launcher.ps1` | Unified launcher that starts the core stack and opens both monitoring UIs | One-click full startup from the desktop |
| `chat_events.log` | Main event log | First stop during debugging |
| `vision_error.log` | Runtime errors and stack traces | Investigating failures |

---

## Copilot Customization Layer

| File | Purpose | When to Use |
|---|---|---|
| `.github/copilot-instructions.md` | Always-on repo guidance for Copilot | Before changing behavior or conventions |
| `HIVE.md` | Agent swarm and customization overview | Understanding agent/skill layout |
| `.github/agents/vision-maintainer.agent.md` | Runtime/debug/code-change specialist | Backend and protocol work |
| `.github/agents/openclaw-operator.agent.md` | OpenClaw installation and gateway specialist | OpenClaw onboarding and repair |
| `.github/agents/mcp-builder.agent.md` | MCP and customization specialist | MCP wiring and tool expansion |
| `.github/agents/context-steward.agent.md` | Repo-awareness and context specialist | Memory, context, and workflow continuity |
| `.github/agents/home-ops-steward.agent.md` | Home-ops specialist for PC, network, security, and backup work | Operational maintenance tasks |
| `.github/agents/code-review.agent.md` | Review specialist for correctness, security, and type safety | Reviewing significant changes |
| `.github/agents/refactor.agent.md` | Behavior-preserving refactor specialist | Structural cleanup without feature changes |
| `.github/skills/vision-context-ops/SKILL.md` | Improve Copilot itself in this repo | Repo-awareness and context upgrades |
| `.github/skills/vision-documentation-ops/SKILL.md` | Keep docs aligned with the real system | Documentation maintenance |
| `.github/skills/vision-home-ops/SKILL.md` | Home PC/network/security/backup operations | Operational maintenance workflows |
| `.github/skills/vision-code-review/SKILL.md` | Review Vision changes with repo-specific checks | Pre-merge review work |
| `.github/skills/vision-type-safety/SKILL.md` | Fix type-annotation and mypy issues | Type-cleanup work |
| `.github/skills/vision-context-brain/SKILL.md` | Generate and use a machine-readable context brain | Broad-task refresh and compaction recovery |
| `.github/skills/vision-cognitive-council/SKILL.md` | Gather multiple specialist viewpoints before action | Broad, risky, or ambiguous work |
| `.github/skills/vision-git-ops/SKILL.md` | Git workflow for commits, branches, PRs, and tags | Repo history and release tasks |

---

## Skills by Task

| Task | Skill |
|---|---|
| Start or verify the operator | `vision-runtime-ops` |
| Debug voice, provider, WebSocket, OCR, or tool failures | `vision-debugging` |
| Audit tool-calling behavior | `vision-tool-audit` |
| Add new tool support | `vision-tool-dev` |
| Review a change before merge | `vision-code-review` |
| Fix type errors or missing annotations | `vision-type-safety` |
| Refresh deep repo context before a broad task | `vision-context-brain` |
| Deliberate a broad or high-risk change before acting | `vision-cognitive-council` |
| Improve Copilot context/memory workflow | `vision-context-ops` |
| Work on home PC, network, security, backup, or automation tasks | `vision-home-ops` |
| Keep docs synchronized | `vision-documentation-ops` |
| Expand MCP wiring | `vision-mcp-builder` |
| Use the active MCP servers effectively | `vision-mcp-tools` |
| Work with commits, branches, PRs, or tags | `vision-git-ops` |
| Research Vision topics on the web | `vision-web-research` |
| Diagnose latency or performance issues | `vision-performance` |
| Work across multiple displays | `vision-multi-monitor` |
| Control Android devices through ADB | `vision-adb-control` |
| Repair MCP setup | `mcp-recovery` |
| Work with OpenClaw | `openclaw-getting-started` |

---

## MCP and External Context

| File / Surface | Purpose |
|---|---|
| `.vscode/mcp.json` | Workspace MCP server definitions |
| `vision_mcp_server.py` | Repo-local FastMCP bridge for Vision endpoints and external MCP-capable runtimes such as OpenHarness |
| `hive_tools/context_mapper.py` | Machine-readable context brain generator for repo refresh and workflow bootstrap |
| `.archon/config.yaml` | Repo-local Archon defaults for assistants, docs path, and bundled workflow loading |
| `.archon/workflows/` | Repo-local Archon workflows for deterministic maintenance and integration runs |
| `launch_lmstudio_rag_mcp.py` | Env-aware launcher for the `lmstudio-rag` filesystem MCP server |
| `RAG_PLUGIN_WORKSPACE` (fallback: `F:\rag-v1` on Windows, `~/rag-v1` elsewhere) | User-owned LM Studio plugin workspace available as local RAG/plugin context |

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

