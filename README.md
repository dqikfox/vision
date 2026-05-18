# Vision — Universal Accessibility Operator

<p align="center"><strong>Voice-first computer control, operator automation, and live system awareness in one Windows-first AI workspace.</strong></p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-WebSocket%20Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="Windows First" src="https://img.shields.io/badge/Platform-Windows%20First-0078D4?style=for-the-badge&logo=windows&logoColor=white">
  <img alt="OpenClaw" src="https://img.shields.io/badge/OpenClaw-Gateway%20Integrated-7C3AED?style=for-the-badge">
</p>

<p align="center">
  A local AI system that lets anyone control a computer through natural language alone — with live voice, tool use,
  system monitoring, a command center, a self-evolving brain layer that learns from outcomes, and a desktop launcher
  that brings the full stack up with real-time indicators.
</p>

<p align="center">
  <strong>Designed specifically to assist disabled users</strong> by removing physical barriers between people and computers,
  enabling full computer control through voice and text for those with mobility or other physical disabilities.
</p>

<p align="center">
  <img src="docs/images/vision-main-gui.png" alt="VISION main operator GUI" width="100%">
</p>
<p align="center"><em>Main operator interface: voice-first interaction, live state feedback, direct actions, and accessibility-oriented control.</em></p>

<p align="center">
  <img src="docs/images/vision-startup-screen.png" alt="VISION startup screen" width="48%">
  <img src="docs/images/vision-command-center.png" alt="VISION command center" width="31%">
</p>
<p align="center"><em>Startup experience and Command Center: polished boot flow, diagnostics, routines, docs, and system-wide oversight.</em></p>

**Now integrated with OpenClaw Gateway (v2026.4.9)** — orchestrate agents, channels, and multi-agent workflows across Windows, WSL2, and cloud.

---

## Project Architecture

### Core Components

| Component | Purpose | Tech Stack |
|-----------|---------|------------|
| **`vision_mcp_server.py`** | MCP bridge to Vision backend | FastAPI, httpx, MCP SDK |
| **`vision_hotkey.py`** | Hotkey daemon (Ctrl+Alt+V overlay launcher) | keyboard, win32gui |
| **`voice_overlay.py`** | Floating Tkinter HUD with real-time status | Tkinter, WebSocket |
| **`vision_rag.py`** | Local RAG indexing with SQLite FTS5 | sqlite3, pathlib |
| **`vision_rag_integration.py`** | RAG pipeline integration | - |
| **`vision_runtime.py`** | Runtime config and state management | dataclasses, JSON |
| **`vision_admin.py`** | JWT auth and role-based access control | JWT, hashlib, hmac |
| **`vision_openclaw_bridge.py`** | OpenClaw gateway integration | httpx, MCP |
| **`live_chat_ui_v3.html`** | Main web operator interface | HTML5, WebSocket, Canvas API |
| **`vision_command_center.html`** | Command center for diagnostics | HTML5, Fetch API |

### Technology Stack

- **Backend**: FastAPI (WebSocket + REST API), Python 3.14+
- **Frontend**: HTML/CSS/JavaScript (Orbitron font, custom theming)
- **Desktop GUI**: Tkinter (floating overlay with VU meter)
- **Voice Processing**: ElevenLabs API, OpenAI Whisper, Browser Speech API
- **LLM Integration**: Ollama (local), OpenAI, Anthropic (cloud)
- **Windows Automation**: pyautogui, pytesseract, win32gui, win32api
- **Data Storage**: SQLite (FTS5 for RAG), JSON (state files)
- **Deployment**: PowerShell launchers, Windows services

### Key Features

1. **Voice-First Control**: Full computer operation via voice commands
2. **Real-Time HUD**: Floating overlay showing system state, VU meters, active models
3. **Multi-Provider LLM**: Supports Ollama (local), OpenAI, Anthropic
4. **RAG Integration**: Local knowledge base with SQLite FTS5 indexing
5. **Command Center**: Web-based diagnostics, monitoring, and control panel
6. **OpenClaw Integration**: Multi-agent orchestration across platforms
7. **Accessibility Focus**: Designed for users with mobility disabilities
8. **WebSocket Real-Time**: Live state updates across all interfaces
9. **MCP Server**: Standardized protocol for external tool integration
10. **Admin System**: JWT-based authentication with role-based access

### File Structure

```
C:/project/vision/
├── Core Backend
│   ├── vision_mcp_server.py          # MCP bridge (stdio/FastMCP)
│   ├── vision_runtime.py             # Config & state management
│   ├── vision_admin.py               # JWT auth & RBAC
│   └── vision_openclaw_bridge.py     # OpenClaw integration
│
├── Desktop GUI
│   ├── vision_hotkey.py              # Hotkey daemon (Ctrl+Alt+V)
│   └── voice_overlay.py              # Tkinter floating HUD
│
├── Web Interfaces
│   ├── live_chat_ui_v3.html          # Main operator UI
│   ├── vision_command_center.html    # Diagnostics & control
│   └── rag_ui.html                   # RAG interface
│
├── RAG System
│   ├── vision_rag.py                 # SQLite FTS5 indexing
│   └── vision_rag_integration.py     # Pipeline integration
│
├── Automation
│   ├── vision_auto_enhancer.py       # Auto-enhancement
│   └── vision_master_launcher.ps1    # Desktop launcher
│
├── Configuration
│   ├── vision_command_center_config.json  # Non-sensitive config
│   ├── vision_automation_state.json       # Automation history
│   ├── .env                               # Environment secrets
│   └── pyproject.toml                     # Python project config
│
├── Development
│   ├── .github/
│   │   ├── copilot-instructions.md   # Copilot guidelines
│   │   ├── agents/                   # Custom agents
│   │   └── skills/                   # Copilot skills
│   ├── .vscode/                      # VS Code config
│   ├── .editorconfig                 # IDE formatting
│   ├── CONTRIBUTING.md               # Development guide
│   └── README.md                     # This file
│
└── Tests
    └── tests/                        # pytest test suite
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VISION_BASE_URL` | `http://localhost:8765` | Vision backend URL |
| `VISION_HOST` | `127.0.0.1` | Bind host (`0.0.0.0` for LAN) |
| `VISION_ALLOWED_ORIGINS` | - | CORS allowed origins |
| `VISION_TOOL_TOKEN` | - | API authentication token |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `ELEVENLABS_API_KEY` | - | ElevenLabs TTS key |
| `PYTHONPATH` | `c:\project\vision` | Python module path |
| `VISION_MCP_TIMEOUT` | `20` | MCP request timeout (sec) |
| `VISION_ADMIN_SECRET` | auto-generated | JWT signing secret |

---

## Why Vision

**Remove the physical barrier between people and computers.**

Vision is specifically designed to empower disabled users by providing full computer control through voice and text interfaces. The system enables anyone — regardless of mobility, disability, or technical ability — to:
- Open applications and websites
- Click buttons and navigate interfaces
- Type, dictate, and automate workflows
- Read what is on screen
- Monitor system state and operator tooling from one place
- Control their computer without requiring precise motor control or physical interaction

...by speaking or typing naturally, making computing accessible to those who face physical challenges with traditional input methods.

---

## Quick Start

### Option 1: Vision Operator (Local, Standalone)

**Prerequisites**
```
pip install fastapi uvicorn websockets sounddevice numpy scipy pyautogui pytesseract elevenlabs openai httpx pillow
ollama pull gpt-oss:20b  # preferred local default
```

**Launch**
```
cd C:\project\vision
python live_chat_app.py
```
Or use the **Desktop VISION Master Launcher** for the full experience.

Notes:
- `vision_master_launcher.ps1` delegates core startup to `launch_vision.ps1`.
- `launch_vision.ps1` starts `ollama serve` automatically when Ollama is needed and not already listening.
- `vision_command_center_config.json` now controls Ollama access mode for launcher-managed starts: **local** (`127.0.0.1`) or **lan** (`0.0.0.0`), an explicit managed `ollama_host` (for example `0.0.0.0:11434`), configurable `OLLAMA_ORIGINS`, and the managed `ollama_models_path`. The checked-in defaults now prefer fully local Ollama on `127.0.0.1:11434` with only localhost UI origins enabled.
- `launch_vision.ps1` now restarts Ollama as a **managed standalone server** so Vision uses the configured model library instead of an app-respawned default store.
- The launcher also starts the Vision backend when port `8765` is not already active, then checks `/api/health` and `/api/command-center/doctor` before treating startup as successful.
- The embedded ElevenLabs browser widget only gets microphone access on **secure origins** (`http://localhost` counts, plain `http://<lan-ip>` does not). For same-network phone access, use the main/operator surfaces over LAN, or front Vision with HTTPS if you need browser-native microphone capture.

Browser opens at `http://localhost:8765` automatically.
The separate **Vision Command Center** is served at `http://localhost:8765/command-center` for launch, monitoring, docs, workflows, and repo-intelligence control.
For same-network mobile access, set `VISION_HOST=0.0.0.0`, configure trusted `VISION_ALLOWED_ORIGINS`, and use `VISION_TOOL_TOKEN` before opening `http://<your-pc-lan-ip>:8765` or `http://<your-pc-lan-ip>:8765/command-center`. Launcher-managed Ollama should stay in `lan` mode with `0.0.0.0:11434` when you want phone/tablet model access on the same network.
It now also includes **Vision Doctor**, saved maintenance **routines**, higher-level **Mission Control** automation pipelines, a persistent automation history file (`vision_automation_state.json`), a non-sensitive **profile/config** layer (`vision_command_center_config.json`), and an optional **ULTRON Retro** theme.
The Command Center now also exposes a **Layered Control Architecture** view that separates the dependable operator core (launcher, local models, runtime/tool readiness) from the higher-order cognitive layer (context brain, missions, skills, agents, and docs).

### Option 2: Vision with OpenClaw Gateway (Recommended)

**Prerequisites**
- Node.js 24+ (or 22.14+)
- Provider API key (Anthropic, OpenAI, Google, etc.)

**Setup OpenClaw**
```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex        # Windows
openclaw onboard --install-daemon                       # Configure + start gateway
openclaw gateway status                                 # Verify running on port 18789
openclaw dashboard                                      # Open Control UI
```

For full details, use the `/openclaw-getting-started` skill in Copilot.

**Start Vision Operator**
With OpenClaw gateway running, launch Vision in the usual way:
```
python live_chat_app.py
```
The operator can now route commands to OpenClaw agents, access gateway tools, and participate in multi-agent workflows.

---

## Agent & Skill Customizations

Vision is now managed by GitHub Copilot customizations. Use these to run, debug, or extend the system:

### Agents
- **Vision Maintainer** — Main agent for runtime, debugging, and code changes (`.github/agents/vision-maintainer.agent.md`)
- **OpenClaw Operator** — Specialized agent for OpenClaw workflows (installed in this repo)
- **MCP Builder** — Specialist for MCP wiring, skills, and custom agent expansion (`.github/agents/mcp-builder.agent.md`)
- **Context Steward** — Specialist for making Copilot more repo-aware via instructions, skills, memory workflow, and context discipline (`.github/agents/context-steward.agent.md`)
- **Home Ops Steward** — Specialist for single-user home PC, network, security, backup, and automation workflows (`.github/agents/home-ops-steward.agent.md`)
- **Code Review Agent** — Review-focused agent for correctness, security, performance, type safety, and Vision-specific patterns (`.github/agents/code-review.agent.md`)
- **Refactor Agent** — Behavior-preserving refactor specialist for structural cleanup and duplication reduction (`.github/agents/refactor.agent.md`)

### Skills (On-Demand Workflows)
- **vision-operator** — Operate Vision end-to-end across voice, tools, and accessibility workflows
- **vision-runtime-ops** — Start the app, verify endpoints, check provider readiness
- **vision-debugging** — Debug voice, WebSocket, provider, OCR, and tool-call issues
- **vision-tool-audit** — Audit direct tool execution and natural-language tool routing
- **vision-tool-dev** — Add new Vision tools with the required schema/handler/registration wiring
- **vision-code-review** — Review changes for correctness, security, type safety, and async/runtime hazards
- **vision-type-safety** — Fix mypy and type-annotation issues in Vision code
- **vision-context-brain** — Generate and use a machine-readable context brain for broad tasks and post-compaction recovery
- **vision-cognitive-council** — Gather multiple specialist viewpoints before broad, risky, or ambiguous work
- **vision-context-ops** — Improve Copilot repo awareness, context refresh, and memory workflow (`.github/skills/vision-context-ops/SKILL.md`)
- **vision-home-ops** — Apply Vision to home PC administration, networking, security, backups, and automation
- **vision-documentation-ops** — Keep docs, skills, agents, and runtime notes aligned
- **vision-mcp-builder** — Expand repo-local MCP servers and customization wiring
- **vision-mcp-tools** — Use the active MCP server surface effectively inside this workspace
- **vision-git-ops** — Work with commits, branches, PRs, tags, and git history safely
- **vision-web-research** — Research Vision-related topics on the web with MCP-backed search/fetch
- **vision-performance** — Profile and optimize latency, CPU/GPU usage, and pipeline performance
- **vision-multi-monitor** — Target the correct display and coordinate actions across multiple screens
- **vision-adb-control** — Control Android devices via ADB from Vision workflows
- **openclaw-getting-started** — Install and bootstrap OpenClaw (Windows, WSL2, macOS, Linux)
- **mcp-recovery** — Diagnose and restore MCP server configurations

Vision also uses a shared local skill repo at **`C:\project\skills`** for reusable cross-project workflows. Prefer `.github/skills/` when the task is Vision-specific; prefer `C:\project\skills` when the workflow is general and reusable across multiple local repos.

### Repo Instructions
- **Copilot Instructions** — Global guidelines for working in this repo (`.github/copilot-instructions.md`)
- **Local LM Studio RAG Context** — Copilot can inspect the workspace defined by `RAG_PLUGIN_WORKSPACE` through workspace MCP when LM Studio or local retrieval tasks are relevant. If unset, the repo falls back to the curated corpus at `F:\rag-v1\vision-corpus` on Windows and `~/rag-v1/vision-corpus` elsewhere.
- **Documentation Index** — Start with `DOCUMENTATION_INDEX.md` for the current doc map

### External Agent Harnesses
Vision already exposes a repo-local MCP bridge in `vision_mcp_server.py`, so external runtimes that support MCP do **not** need a custom desktop-control adapter first.

For example, OpenHarness can consume Vision over stdio MCP:

```ts
mcpServers: {
  vision: {
    type: "stdio",
    command: "python",
    args: ["vision_mcp_server.py"],
    env: { VISION_BASE_URL: "http://localhost:8765" },
  },
}
```

With a single MCP server, the exposed tool names stay as defined (`vision_health`, `vision_models`, `vision_execute_tool`, etc.). With multiple MCP servers, some harnesses namespace tools by server name, so check that runtime's MCP naming rules.

For deterministic multi-step repo automation, this repo also ships **Archon workflows** in `.archon/workflows/`:
- `vision-repo-maintenance.yaml` — autonomous repo maintenance with a safe compile-time validation step
- `vision-external-agent-integration.yaml` — improve external MCP-harness integrations while reusing `vision_mcp_server.py`

The repo also includes `.archon/config.yaml` with project defaults for Claude/Codex assistant settings, docs discovery, and bundled workflow loading. Archon requires at least one configured assistant on your machine.

Useful Archon CLI commands for this repo:

```powershell
archon workflow list --cwd C:\project\vision
archon workflow run vision-context-brain-refresh --cwd C:\project\vision "Refresh the repo context before a broad task"
archon workflow run vision-cognitive-council --cwd C:\project\vision "Deliberate the best path for a broad or risky task"
archon workflow run vision-repo-maintenance --cwd C:\project\vision "Continue maintaining the Vision repo"
archon workflow run vision-external-agent-integration --cwd C:\project\vision "Improve the OpenHarness MCP integration"
```

For the deepest manual refresh, generate the repo's machine-readable context brain:

```powershell
python hive_tools\context_mapper.py --output .archon\artifacts\project_context.json
```

When Vision is running, the browser-accessible command center gives you a GUI for the same stack:
- a layered view of the **Core Operator Layer** vs the **Cognitive Layer**
- runtime health and metrics
- Vision Doctor readiness checks
- saved maintenance and smoke-test routines
- multi-step automation missions with persistent execution history
- theme/profile settings for launcher and command-center behavior
- configurable Ollama exposure mode and CORS origins for local-only or LAN use
- context brain refresh and artifact access
- Archon workflow launch/copy commands
- docs, skills, agents, MCP surfaces, and core file openers
- direct jump back into the main Vision operator UI

Type `/` in any Copilot chat to browse available skills.

---

## Components

| File | Purpose |
|---|---|
| `live_chat_app.py` | Main FastAPI server — voice + operator backend |
| `live_chat_ui.html` | Browser GUI — orb, chat, actions, memory, log |
| `vision_command_center.html` | Secondary command-center GUI for launch, monitoring, docs, workflows, and repo intelligence |
| `vision_command_center_config.json` | Non-sensitive command-center profile and launcher preferences |
| `vision_automation_state.json` | Persistent routine and mission execution history for command-center automation |
| `launch_vision.ps1` | Windows launcher with health checks, doctor call, and config-aware browser behavior |
| `vision_master_launcher.ps1` | Unified launcher that starts the core stack, checks health/doctor/models, opens both UIs, and reports live status |
| `elite_brain.py` | Cognitive layer with memory, reasoning, critique, curiosity, and self-evolution rules learned from outcomes |
| `elite_goals.py` | **AGI Module** — Autonomous goal management with hierarchical decomposition and planning |
| `elite_world.py` | **AGI Module** — World model with entity tracking, state inference, and prediction |
| `speak.py` | Standalone TTS utility |
| `voice_toggle.py` | Background hotkeys (F9/F10/F11) |
| `memory.json` | Persistent long-term memory (auto-created) |
| `chat_events.log` | Full event log (auto-created) |
| `.brain/` | AGI cognitive data storage (goals, entities, observations) |

---

## Home Ops Objective

Vision is also being shaped into a **single-user home operations assistant** for:
- system administration
- home network management
- security and protection
- backup and data protection
- automation and efficiency
- monitoring and maintenance

The goal is to reduce manual overhead by combining local system control, scripting, diagnostics, monitoring, and documented operating workflows.

---

## Modes

### Chat Mode
Conversational AI assistant.
- Always-listening microphone with voice activity detection (VAD)
- User-facing toggle for **Always Listening ON/OFF**
- Speech output yields when new speech is detected so the user can interrupt naturally
- Speak naturally, AI responds via ElevenLabs TTS
- Full conversation history with memory across sessions

### Operator Mode
Full computer control via voice.
```
"Open Chrome"              → run_command: start chrome
"Click the search bar"     → read_screen → click(x, y)
"Type my email"            → type_text("...")
"Press Control C"          → press_key("ctrl+c")
"Scroll down"              → scroll(x, y, "down")
"What's on screen?"        → read_screen → OCR → TTS response
```

---

## Model Providers

Click the model badge in the header to switch:

| Provider | Where | Example models |
|---|---|---|
| **Ollama** | Local (no internet) | All installed models |
| **OpenAI** | Cloud | gpt-4.1, gpt-4o, o3, computer-use-preview |
| **GitHub Copilot** | Cloud (GitHub Models API) | gpt-4.1, gpt-4o, claude-3.7-sonnet, llama-70b |
| **Anthropic** | Cloud | claude-sonnet-4.5, claude-opus-4.5, claude-3.7-sonnet |
| **DeepSeek** | Cloud | deepseek-chat, deepseek-reasoner, deepseek-coder |
| **Groq** | Cloud | llama-3.3-70b-versatile, llama-3.1-8b-instant |
| **Mistral AI** | Cloud | mistral-large-latest, mistral-small-latest, codestral-latest |
| **Google Gemini** | Cloud | gemini-2.0-flash-lite and other OpenAI-compatible Gemini models |
| **xAI (Grok)** | Cloud | grok-3-mini, grok-2-vision-1212 |

Set API keys in the model picker UI or via environment variables for the providers you want to use:
```
OPENAI_API_KEY=sk-...
AZURE_OPENAI_BASE_URL=https://your-resource.services.ai.azure.com/openai/v1
AZURE_OPENAI_MODEL=gpt-4o
AZURE_OPENAI_API_KEY=...
GITHUB_TOKEN=ghp_...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...
GEMINI_API_KEY=...
XAI_API_KEY=xai-...
ELEVENLABS_API_KEY=sk_...
```

Quick Azure-hosted OpenAI-compatible smoke test:
```
python scripts\invoke_azure_openai_chat.py --prompt "What is the capital of France?"
```

---

## Memory System

The system remembers facts, preferences, and past tasks across sessions.

- **Facts**: Stored manually (Memory tab → Add) or auto-extracted from conversation
- **Task history**: Last 50 voice/text commands
- **User profile**: Name, preferences (learned over time)
- **Session count**: Tracks how many times you've used the system

Memory is stored in `memory.json` — delete to reset.

---

## RAG Knowledge Base (F:\\rag-v1\\data)

Vision now includes a local RAG indexing and retrieval pipeline wired into the runtime, MCP bridge, and Open Harness integration.

### Data Source

- Default corpus path on Windows: `F:\\rag-v1\\data`
- Override with environment variable:
  - `VISION_RAG_SOURCE=F:\\rag-v1\\data`
  - or set `RAG_PLUGIN_WORKSPACE` (Vision will infer a data path when possible, and LM Studio context uses a curated corpus when the workspace is too large)

### New API Endpoints

- `GET /api/brain/status` — self-evolving brain counters, success rate, and top learned adaptations
- `GET /api/rag/status` — index status and metadata
- `POST /api/rag/index` — build/rebuild SQLite FTS index
- `POST /api/rag/search` — retrieve grounded chunks
- `POST /api/rag/export-training` — export JSONL datasets for LLM training/KB ingestion

### New Operator Tools

- `kb_status`
- `kb_index`
- `kb_search`
- `kb_export_training_data`

These are available in normal operator mode, ElevenLabs conversational agent mode, and through `vision_mcp_server.py` for external harnesses.

### Training / Export Output

`kb_export_training_data` writes artifacts under `C:\\project\\vision\\.rag\\exports\\<timestamp>\\` including:

- `knowledge_base.jsonl` (document chunks + metadata)
- `training_corpus.jsonl` (raw corpus lines)
- `instruction_train.jsonl` and `instruction_val.jsonl` (SFT-ready chat examples)
- `manifest.json` (export metadata)

---

## Deployment

Vision can be deployed in multiple ways depending on your needs:

### Local Windows Deployment (Recommended for Accessibility)

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Containerized Deployment

Vision includes Docker support for easy deployment:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the application at http://localhost:8765
```

### Cloud Deployment

Vision can be deployed to cloud platforms like Azure, AWS, or Google Cloud.
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed cloud deployment instructions.

---

## Voice Settings

| Parameter | Default | Description |
|---|---|---|
| `RMS_THRESH` | 500 | Mic sensitivity / ambient-noise gate (higher = less sensitive) |
| `BARGE_RMS` | 1100 | Volume to interrupt AI speech |
| `START_FRAMES` | 3 | Frames of loud audio to start recording (~90ms) |
| `END_FRAMES` | 20 | Frames of silence to stop recording (~600ms) |

---

## Voice Communication Improvements for Disabled Users

Vision's voice communication system is specifically designed to accommodate users with various disabilities:

### Enhanced Speech Recognition
- **Multi-layer STT cascade**: ElevenLabs scribe_v1 → Groq whisper-large-v3-turbo → faster-whisper tiny (offline fallback) for maximum accuracy
- **Adaptive sensitivity**: Configurable VAD thresholds to accommodate different speech patterns and ambient noise conditions
- **Barge-in capability**: Allows users to interrupt AI speech naturally, important for users who may need more time to process responses

### Improved Text-to-Speech
- **High-quality voices**: ElevenLabs WebSocket streaming for natural, clear speech output
- **Customizable voice parameters**: Adjustable rate, volume, and voice selection to suit individual preferences
- **Reduced latency**: ~300ms TTS latency for responsive feedback

### Accessibility Features
- **Wake word support**: "Hey Vision", "OK Vision" for hands-free activation
- **Always Listening mode**: Continuous voice detection for users who cannot manually activate voice input
- **Visual feedback**: Real-time volume indicators and transcription display for users with hearing impairments

### Potential Improvements
1. **Custom wake word training**: Allow users to train personalized wake words that are easier for them to pronounce
2. **Voice profile adaptation**: Learn individual speech patterns and accents for improved recognition
3. **Enhanced barge-in detection**: Better sensitivity adjustment for users with softer or atypical speech patterns
4. **Multi-language support**: Expanded language models for non-English speakers with disabilities
5. **Noise cancellation**: Advanced audio processing to filter out environmental sounds that may interfere with recognition
6. **Speech enhancement**: Amplification and clarity improvements for users with speech difficulties

---

## Keyboard Shortcuts (in browser)

| Key | Action |
|---|---|
| `Enter` | Send text message |
| `M` | Toggle mute |
| `Esc` | Clear chat |

---

## Architecture

```
Microphone
    │
    VAD (energy-based voice activity detection)
    │
  STT cascade: ElevenLabs scribe_v1
           → Groq whisper-large-v3-turbo
           → faster-whisper tiny (offline fallback)
    │
  LLM (Ollama / OpenAI / GitHub / Groq / Gemini / DeepSeek / Mistral / Anthropic / xAI)
  ├── Chat mode: stream response → TTS
  └── Operator mode: tool calls → execute → TTS confirm
         ├── read_screen  (pyautogui + pytesseract OCR)
         ├── click        (pyautogui)
         ├── type_text    (pyautogui)
         ├── press_key    (pyautogui hotkey)
         ├── scroll       (pyautogui)
         └── run_command  (asyncio subprocess)
    │
  ElevenLabs TTS WebSocket (eleven_flash_v2_5, ~300ms latency)
      → Windows OneCore neural
      → pyttsx3 SAPI (last resort)
    │
  Speaker
```

---

## Project Structure

```
C:\project\vision\
├── .github/
│   ├── copilot-instructions.md       ← Global Copilot behavior
│   ├── agents/
│   │   ├── vision-maintainer.agent.md        ← Main repo agent
│   │   ├── openclaw-operator.agent.md        ← OpenClaw specialist
│   │   ├── mcp-builder.agent.md              ← MCP/customization specialist
│   │   ├── context-steward.agent.md          ← Repo awareness specialist
│   │   └── home-ops-steward.agent.md         ← Home operations specialist
│   └── skills/
│       ├── vision-runtime-ops/       ← Run/verify the operator
│       ├── vision-debugging/         ← Debug failures
│       ├── vision-tool-audit/        ← Audit tool-calling
│       ├── vision-context-ops/       ← Improve Copilot context discipline
│       ├── vision-home-ops/          ← Home PC/network/security workflows
│       ├── vision-documentation-ops/ ← Keep docs aligned
│       ├── vision-mcp-builder/       ← Expand MCP capabilities
│       ├── openclaw-getting-started/ ← Install OpenClaw
│       ├── mcp-recovery/             ← Restore MCP config
│       └── (+ other community skills)
├── .archon/
│   ├── config.yaml                     ← Repo-local Archon defaults
│   └── workflows/                    ← Repo-local Archon automation workflows
├── hive_tools/
│   └── context_mapper.py               ← Machine-readable context brain generator
│
├── README.md                          ← This file
├── live_chat_app.py                   ← Main backend server
├── vision_mcp_server.py               ← Repo-local FastMCP bridge
├── live_chat_ui.html                  ← Browser GUI (primary)
├── speak.py                           ← Standalone TTS
├── voice_toggle.py                    ← Hotkey tool (F9/F10/F11)
├── live_chat_launch.bat               ← Desktop launcher
├── voice_toggle_launch.bat            ← Voice toggle launcher
├── memory.json                        ← Persistent memory (auto)
├── chat_events.log                    ← Event log (auto)
│
├── docs/
│   ├── architecture.md                ← System design details
│   ├── components.md                  ← Component reference
│   └── ... (other research)
│
├── architecture.md                    ← Live Chat app architecture
├── components.md                      ← Live Chat component details
├── setup.md                           ← Environment & dependency setup
├── HIVE.md                            ← Agent swarm strategy
└── agent-orchestrator.yaml            ← Agent coordination config
```

---

---

## ⭐ Elite Code Quality System

Vision has been enhanced with **production-grade quality frameworks** to ensure reliability, security, and maintainability:

### 🛡️ Resilience & Safety
- **Circuit Breakers** (`elite_resilience`) — Auto-fallback when providers fail
- **Secret Detection** (`elite_safety`) — Prevents accidental credential exposure
- **Input Validation** — Blocks injection attacks, path traversal
- **Async Safety** — Detects blocking calls in async functions

### 📊 Observability & Metrics
- **Performance Tracking** (`elite_metrics`) — Latency histograms (p50, p95, p99)
- **Tool Analytics** (`elite_tools`) — Execution counts, durations, cache hits
- **Health Monitoring** — Provider status, circuit breaker state
- **Structured Logging** — JSON format for easy analysis

### 🚀 Developer Experience
- **Type Hints** — Full mypy strict compliance enforced
- **Docstrings** — Google-style with examples on all public APIs
- **Reusable Patterns** (`elite_patterns`) — @async_cached, @async_retry decorators
- **Testing Framework** — pytest with async support, fixtures, 70%+ coverage

### 📖 Comprehensive Documentation
- **`.github/copilot-conventions.md`** — Comprehensive style guide (11 sections)
- **`ELITE_ENHANCEMENTS.md`** — Full feature documentation
- **`GETTING_STARTED_ELITE.md`** — Quick reference cookbook
- **`pyproject.toml`** — Tool configuration (mypy, pylint, black, bandit)

### ⚙️ Automated Quality Gates
- **mypy** — Strict type checking enabled
- **pylint** — Code quality ≥ 8.0
- **black** — Automatic code formatting
- **bandit** — Security vulnerability scanning
- **pytest** — Unit + integration tests
- **GitHub Actions** — CI/CD on every push/PR

### 🎯 Quick Example: Safe Tool Execution
```python
from elite_tools import tool_executor
from elite_safety import InputValidator
from elite_metrics import metrics

# Validate input safely
safe_path = InputValidator.sanitize_file_path(user_path, base_dir="/allowed")

# Execute with timeout, caching, and automatic metrics
result = await tool_executor.execute(
    tool="click",
    args={"x": 100, "y": 200},
    executor_fn=exec_tool,
    cacheable=True,           # Cache reads
    timeout_seconds=10.0,     # Prevent hangs
)

# Automatic tracking
print(f"Success: {result.success}")
print(f"Duration: {result.duration_ms}ms")
print(f"Cache hit: {result.cache_hit}")

# Metrics visible at /api/elite/metrics endpoint
```

---

## Getting Help

**For Vision operator issues:**
- Use the `/vision-debugging` skill in Copilot
- Read `setup.md` for environment problems
- Check `architecture.md` for protocol/design questions

**For making Copilot smarter in this repo:**
- Use the `/vision-context-brain` skill when the task is broad or context was compacted
- Use the `/vision-cognitive-council` skill when the task is broad, risky, or ambiguous and needs multiple viewpoints
- Use the `/vision-context-ops` skill
- Invoke the `@Context Steward` agent
- Update `.github/copilot-instructions.md` when the improvement should be always-on
- Pull in the path from `RAG_PLUGIN_WORKSPACE` as local context when the task involves LM Studio or RAG, or use the documented curated platform fallback when the env var is unset

**For documentation maintenance:**
- Start with `DOCUMENTATION_INDEX.md`
- Use the `/vision-documentation-ops` skill
- Update the nearest authoritative doc when behavior changes

**For home PC and network operations:**
- Use the `/vision-home-ops` skill
- Invoke the `@Home Ops Steward` agent
- Prefer documented, repeatable maintenance and automation over one-off fixes

**For code quality & development:**
- Read `.github/copilot-conventions.md` for coding standards
- See `GETTING_STARTED_ELITE.md` for quick recipes
- Use `/vision-code-review` or `@Code Review Agent` before merging significant changes
- Use `/vision-type-safety` when cleaning up mypy or annotation issues
- Use `/vision-runtime-ops` skill to verify the stack

**For OpenClaw integration:**
- Use the `/openclaw-getting-started` skill
- Check `https://docs.openclaw.ai` for full OpenClaw docs

**For adding features or fixing bugs:**
- Invoke the `@Vision Maintainer` agent
- Use `@Refactor Agent` for behavior-preserving cleanup work
- Use `/vision-tool-audit` if working on operator mode
- Run `python test_vision.py` or `python test_tools.py` to validate

---

*"It turns intent into action, so a person does not need hands to use a computer."*
