# VISION — Elite Copilot Instructions

You are operating inside the **VISION Universal Accessibility Operator** — a production-grade,
Windows-first AI system that gives any human full computer control through voice and text alone.

---

## System Identity

- **Backend**: `live_chat_app.py` — FastAPI + WebSocket server on `http://localhost:8765`
- **Frontend**: `live_chat_ui.html` — primary browser UI (do NOT use alternate UI files unless explicitly asked)
- **Architecture**: 3-layer pipeline — Perception → Brain → Action (see `architecture.md`)
- **Memory**: `memory.json` — persistent facts, task history, user profile across sessions
- **Logs**: `chat_events.log` — full event log, always check here first when debugging

---

## Providers (all active)

| Provider | Base URL | Key Env Var |
|---|---|---|
| Ollama (local) | `http://localhost:11434/v1` | none |
| OpenAI | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| GitHub Models | `https://models.inference.ai.azure.com` | `GITHUB_TOKEN` |
| DeepSeek | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` |
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` |
| Mistral | `https://api.mistral.ai/v1` | `MISTRAL_API_KEY` |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` | `GEMINI_API_KEY` |

Keys live in `.env` (gitignored). Never print or log key values.

---

## All 41 Tools (exec_tool)

**Vision**: `read_screen`, `screenshot`
**Mouse**: `click`, `double_click`, `right_click`, `move_mouse`, `drag`, `scroll`
**Keyboard**: `type_text`, `press_key`
**Clipboard**: `get_clipboard`, `set_clipboard`
**Windows**: `list_windows`, `focus_window`
**Shell**: `run_command`
**Files**: `read_file`, `write_file`, `list_files`
**Browser (Playwright)**: `browser_open`, `browser_click`, `browser_fill`, `browser_extract`, `browser_screenshot`, `browser_press`

Test any tool directly:
```powershell
Invoke-RestMethod -Uri http://localhost:8765/api/tool/execute -Method Post `
  -Body '{"name":"screenshot","parameters":{}}' -ContentType "application/json"
```

---

## MCP Servers (active in VSCode)

| Server | Purpose |
|---|---|
| `github` | GitHub Copilot MCP — PRs, issues, code search |
| `openclaw` | OpenClaw agent orchestration |
| `openclaw-acp` | OpenClaw ACP session bridge |
| `filesystem` | Read/write `C:\project`, Desktop, Documents |
| `memory` | Persistent cross-session knowledge graph |
| `sequential-thinking` | Multi-step reasoning decomposition |
| `fetch` | HTTP fetch any URL |
| `brave-search` | Web search via Brave API |
| `puppeteer` | Headless browser automation |
| `vision-local` | Direct VISION tool execution via `http://localhost:8765/mcp` |

---

## Agent Swarm (HIVE MIND)

| Agent | File | Role |
|---|---|---|
| Vision Maintainer | `.github/agents/vision-maintainer.agent.md` | Runtime, debug, protocol |
| OpenClaw Operator | `.github/agents/openclaw-operator.agent.md` | OpenClaw install/run |
| Coding Agent | `.gemini/agents/coding.md` | Features, refactoring, TDD |
| Debug Agent | `.gemini/agents/debug.md` | Root cause, log analysis |
| Analysis Agent | `.gemini/agents/analysis.md` | Architecture, security, perf |
| Deploy Agent | `.gemini/agents/deploy.md` | CI/CD, git, releases |
| Security Agent | `.gemini/agents/security.md` | Secrets, vulns, hardening |
| Voice Agent | `.gemini/agents/voice.md` | STT/TTS pipeline |

---

## Skills (invoke with @skill-name)

- `vision-operator` — operate VISION end-to-end
- `vision-runtime-ops` — start, verify, smoke-test the stack
- `vision-debugging` — debug any layer (startup/voice/WS/OCR/tools)
- `vision-tool-audit` — audit tool-call routing and action broadcasts
- `vision-tool-dev` — add new tools (schema + handler + EL registration)
- `mcp-recovery` — diagnose and restore broken MCP servers
- `openclaw-getting-started` — install and run OpenClaw

---

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/api/health` | Component health (ollama/ocr/gpu/browser) |
| GET | `/api/models` | All providers + current model |
| POST | `/api/model` | Switch provider/model |
| GET | `/api/metrics` | CPU/RAM/GPU live stats |
| GET | `/api/voices` | All TTS voices (SAPI + OneCore) |
| GET | `/api/memory` | Full memory dump |
| POST | `/api/memory/fact` | Add a fact |
| DELETE | `/api/memory/fact` | Remove a fact |
| POST | `/api/tool/execute` | Execute any tool directly |
| GET | `/screenshot` | Live desktop screenshot (base64 JPEG) |
| WS | `/ws` | Real-time chat/voice/state stream |
| POST | `/api/el-agent/start` | Start ElevenLabs ConvAI agent |
| POST | `/api/el-agent/stop` | Stop ElevenLabs ConvAI agent |

---

## WebSocket Message Types

**Inbound (client → server)**:
`text`, `input`, `mute`, `mode`, `set_model`, `set_api_key`, `set_voice_settings`,
`execute_tool`, `add_fact`, `del_fact`, `clear`, `log`, `el_agent_start`, `el_agent_stop`

**Outbound (server → client)**:
`init`, `state`, `transcript`, `token`, `stream_start`, `stream_finalize`,
`action`, `screenshot`, `volume`, `thinking`, `model_changed`, `memory_updated`,
`key_saved`, `voice_settings`, `el_agent`, `partial_transcript`

---

## Voice Pipeline

```
Mic → VAD (energy-based) → STT cascade:
  1. ElevenLabs scribe_v1  (cloud, best quality)
  2. Groq whisper-large-v3-turbo  (cloud, fast)
  3. faster-whisper tiny  (local, offline fallback)
→ LLM (operator mode: tool loop) → TTS cascade:
  1. ElevenLabs WebSocket stream (eleven_flash_v2_5, ~300ms)
  2. Windows OneCore neural (win32com)
  3. pyttsx3 SAPI (last resort)
→ Speaker
```

VAD thresholds (calibrated — do NOT change casually):
- `RMS_THRESH=500`, `START_FRAMES=3`, `END_FRAMES=20`, `BARGE_RMS=1100`

---

## LLM Routing

- **Ollama**: native `ollama.AsyncClient` with streaming + tool calling + think mode for reasoning models
- **OpenAI Responses API**: used for `computer-use-preview`, `gpt-4.1`, `gpt-4.1-mini`, `o4-mini`, `o3`
- **All others**: OpenAI-compatible Chat Completions streaming
- **Fallback**: if Ollama errors → auto-cascade to OpenAI if key present
- **Prompt-based tool calling**: fallback for models without native FC

---

## Testing

```powershell
python test_tools.py    # tool execution smoke tests
python test_vision.py   # full integration tests
```

---

## Editing Rules

1. `live_chat_app.py` is the single source of truth for backend logic
2. `live_chat_ui.html` is the primary UI — do not touch alternate UI files unless asked
3. Never collapse chat-mode and operator-mode streaming paths
4. Never change VAD/barge-in thresholds without explicit instruction
5. Never print, log, or expose API key values
6. Always use `await loop.run_in_executor(None, fn)` for blocking calls in async context
7. New tools require 3 changes: `TOOLS` schema + `exec_tool` handler + `_EL_TOOL_NAMES`
8. WebSocket contract changes require coordinated backend + frontend update
9. Prefer surgical edits — no broad rewrites unless explicitly requested
10. After any backend change: verify with `GET /api/health` and a tool execute test
