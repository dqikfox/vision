# Vision Operator Skill

Use this skill to operate VISION — the universal AI computer-control system.

## What VISION Does
VISION is a FastAPI + WebSocket backend that lets an AI model control a Windows desktop using:
- **Voice input** (faster-whisper STT) and **voice output** (ElevenLabs TTS)
- **Screen reading** (pyautogui screenshots + Tesseract OCR)  
- **Mouse/keyboard control** (pyautogui, pywin32)
- **Browser automation** (Playwright)
- **41 built-in tools** for any computer task

## Starting VISION
```powershell
cd C:\project\vision
python live_chat_app.py
# Opens at http://localhost:8765
```

## Key Endpoints
| Endpoint | Purpose |
|----------|---------|
| `GET /` | Web UI |
| `GET /api/health` | System status |
| `GET /screenshot` | Live screen capture |
| `POST /api/tool/execute` | Run any tool directly |
| `WS /ws` | Real-time chat/voice stream |
| `POST /webhook/agent-orchestrator` | AO CI event receiver |

## Tool Categories
- **Vision**: `read_screen`, `screenshot`, `screenshot_region`, `ocr_region`
- **Mouse**: `click`, `double_click`, `right_click`, `drag`, `scroll`, `get_mouse_position`
- **Keyboard**: `type_text`, `press_key`, `hotkey`
- **Browser**: `browser_open`, `browser_click`, `browser_type`, `browser_eval`, `browser_scroll`
- **System**: `run_command`, `get_screen_size`, `window_resize`, `window_move`, `wait`
- **Memory**: `remember`, `recall`, `forget`
- **Files**: `read_file`, `write_file`, `list_files`, `fetch_url`
- **Search**: `web_search`
- **AO**: `ao_start`, `ao_status`, `ao_stop`, `ao_command`

## Voice Commands (examples)
> "Open Chrome and search for weather in London"  
> "Take a screenshot and describe what's on screen"  
> "Click the Start button and open Notepad"  
> "Read the error in the terminal and fix it"

## Config
- Model: edit `current_model` / `current_provider` via `/api/model` endpoint
- Memory: `memory.json` — persistent facts across sessions
- Secrets: `.env` (gitignored) — `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`
