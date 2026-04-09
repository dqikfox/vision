# Vision — Universal Accessibility Operator

> A local AI system that lets anyone control any computer through natural language alone.
> No mouse. No keyboard. No technical skill required.

**Now integrated with OpenClaw Gateway (v2026.4.9)** — orchestrate agents, channels, and multi-agent workflows across Windows, WSL2, and cloud.

---

## Mission

**Remove the physical barrier between people and computers.**

Anyone — regardless of mobility, disability, or technical ability — should be able to:
- Open any application
- Click any button  
- Type any text
- Read anything on screen
- Execute any command

...by speaking or typing naturally.

---

## Quick Start

### Option 1: Vision Operator (Local, Standalone)

**Prerequisites**
```
pip install fastapi uvicorn websockets sounddevice numpy scipy pyautogui pytesseract elevenlabs openai httpx pillow
ollama pull llama3.2  # or any model you prefer
```

**Launch**
```
cd C:\project\vision
python live_chat_app.py
```
Or use the **Live Chat** desktop shortcut.

Browser opens at `http://localhost:8765` automatically.

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

### Skills (On-Demand Workflows)
- **vision-runtime-ops** — Start the app, verify endpoints, check provider readiness
- **vision-debugging** — Debug voice, WebSocket, provider, OCR, and tool-call issues
- **vision-tool-audit** — Audit direct tool execution and natural-language tool routing
- **openclaw-getting-started** — Install and bootstrap OpenClaw (Windows, WSL2, macOS, Linux)
- **mcp-recovery** — Diagnose and restore MCP server configurations

### Repo Instructions
- **Copilot Instructions** — Global guidelines for working in this repo (`.github/copilot-instructions.md`)

Type `/` in any Copilot chat to browse available skills.

---

## Components

| File | Purpose |
|---|---|
| `live_chat_app.py` | Main FastAPI server — voice + operator backend |
| `live_chat_ui.html` | Browser GUI — orb, chat, actions, memory, log |
| `speak.py` | Standalone TTS utility |
| `voice_toggle.py` | Background hotkeys (F9/F10/F11) |
| `memory.json` | Persistent long-term memory (auto-created) |
| `chat_events.log` | Full event log (auto-created) |

---

## Modes

### Chat Mode
Conversational AI assistant.
- Always-on microphone with voice activity detection (VAD)
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

| Provider | Where | Models |
|---|---|---|
| **Ollama** | Local (no internet) | All installed models |
| **OpenAI** | Cloud | gpt-4o, gpt-4o-mini, gpt-4-turbo |
| **GitHub Copilot** | Cloud (GitHub Models API) | gpt-4o, claude-3.5-sonnet, llama-70b |

Set API keys in the model picker UI or via environment variables:
```
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
ELEVENLABS_API_KEY=sk_...
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

## Voice Settings

| Parameter | Default | Description |
|---|---|---|
| `RMS_THRESH` | 250 | Mic sensitivity (lower = more sensitive) |
| `BARGE_RMS` | 1200 | Volume to interrupt AI speech |
| `START_FRAMES` | 3 | Frames of loud audio to start recording (~90ms) |
| `END_FRAMES` | 33 | Frames of silence to stop recording (~1s) |

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
  ElevenLabs STT (scribe_v1)
    │
  LLM (Ollama / OpenAI / GitHub)
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
│   │   └── openclaw-operator.agent.md        ← OpenClaw specialist
│   └── skills/
│       ├── vision-runtime-ops/       ← Run/verify the operator
│       ├── vision-debugging/         ← Debug failures
│       ├── vision-tool-audit/        ← Audit tool-calling
│       ├── openclaw-getting-started/ ← Install OpenClaw
│       ├── mcp-recovery/             ← Restore MCP config
│       └── (+ other community skills)
│
├── README.md                          ← This file
├── live_chat_app.py                   ← Main backend server
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

## Getting Help

**For Vision operator issues:**
- Use the `/vision-debugging` skill in Copilot
- Read `setup.md` for environment problems
- Check `architecture.md` for protocol/design questions

**For OpenClaw integration:**
- Use the `/openclaw-getting-started` skill
- Check `https://docs.openclaw.ai` for full OpenClaw docs

**For adding features or fixing bugs:**
- Invoke the `/vision-maintainer` agent
- Use `/vision-tool-audit` if working on operator mode
- Run `python test_vision.py` or `python test_tools.py` to validate

---

*"It turns intent into action, so a person does not need hands to use a computer."*
