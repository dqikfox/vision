# Component Reference

## live_chat_app.py

The main FastAPI server. All voice, STT, LLM, TTS, and tool logic lives here.

### Key constants (top of file)
| Constant | Default | Tune when |
|---|---|---|
| `RMS_THRESH` | 250 | Mic not triggering (lower) or false triggers (raise) |
| `BARGE_RMS` | 1200 | Barge-in too sensitive (raise) or not working (lower) |
| `START_FRAMES` | 3 | Recording starts too early (raise) |
| `END_FRAMES` | 33 | Cuts off too early (raise) or too slow to stop (lower) |
| `PORT` | 8765 | If port conflict |

### HTTP endpoints
- `GET /` — Serve UI HTML
- `GET /api/models` — List all providers + models
- `POST /api/model` — Switch provider/model `{provider, model}`
- `GET /api/memory` — Get full memory JSON
- `POST /api/memory/fact` — Add fact `{fact}`
- `DELETE /api/memory/fact` — Remove fact `{fact}`
- `GET /screenshot` — Take + return JPEG screenshot

### WebSocket `/ws`
See architecture.md for full protocol.

### Voice loop
```
mic → VAD → STT → llm_stream() → speak()
                              ↑ barge-in check runs in parallel
```

---

## live_chat_ui.html

Single-file browser app. No build step. Opens via FastAPI file serve.

### Layout
```
Header: Logo | Model picker | Mode toggle | Connection
Left:   Orb (canvas) | State | Volume bars | Status | Controls
Right:  Tabs → Chat | Actions | Memory | Log
Footer: Text input | Send
```

### Orb states
| State | Color | Behavior |
|---|---|---|
| idle | Indigo | Slow gentle pulse |
| listening | Blue | Medium pulse |
| recording | Red | Fast, larger |
| thinking | Amber | Shimmer label |
| speaking | Purple | Large, fast |
| muted | Dark grey | Minimal |

### Model picker
- Opens as overlay on model badge click
- Sections: Ollama (with ⟳ refresh) | OpenAI | GitHub Copilot
- Click any model to switch immediately
- API key input per cloud provider

---

## Memory (memory.json)

```json
{
  "user": {
    "name": "string or null",
    "preferences": ["array of strings"]
  },
  "facts": ["string facts, max 100"],
  "session_count": 7,
  "last_session": "ISO datetime",
  "task_history": [
    { "task": "string", "ts": "ISO datetime" }
  ]
}
```

**Auto-extraction**: If AI response contains trigger words (remember, name, prefer, like), the sentence is auto-stored as a fact.

**Manual**: Memory tab → type in input → Add. Or speak "remember that..."

---

## speak.py

Standalone TTS for use outside the live chat app.

```bash
python speak.py "Hello, this is a test"
```

Requires `ELEVENLABS_API_KEY` in environment.

Uses WebSocket streaming (`eleven_flash_v2_5`, PCM 16kHz) via `sounddevice`.

---

## voice_toggle.py

Background hotkey tool for use with any app (e.g. Copilot CLI chat).

| Key | Action |
|---|---|
| F9 (hold) | Record mic → STT → paste + Enter |
| F10 | Toggle TTS on/off |
| F11 | Replay last TTS |
| ESC | Quit |

Run via `Voice Toggle` desktop shortcut.
