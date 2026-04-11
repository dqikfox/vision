# Architecture — Universal Accessibility Operator

## Overview

The system is a real-time voice-controlled AI operator with three layers:

```
┌─────────────────────────────────────────────────────┐
│                    PERCEPTION                       │
│  Microphone → VAD → STT → Intent extraction        │
├─────────────────────────────────────────────────────┤
│                     BRAIN                           │
│  LLM (Ollama/OpenAI/GitHub) + Memory + Planning     │
├─────────────────────────────────────────────────────┤
│                     ACTION                          │
│  Tools: OCR, click, type, key, scroll, command      │
└─────────────────────────────────────────────────────┘
```

---

## Data Flow

### Chat Mode
```
mic frame (480 samples @ 16kHz)
  → if always-listening disabled and wake-word mode is off: remain in voice standby
  → VAD.feed() → "start" | "frame" | "end"
  → "end": concatenate frames → WAV → ElevenLabs STT
  → text → LLM stream (Ollama/OpenAI/GitHub)
  → token chunks → ElevenLabs TTS WebSocket (PCM streaming)
  → sounddevice OutputStream → speaker
  → transcript broadcast → browser UI
```

### Operator Mode
```
text → LLM (non-streaming, tools=TOOLS, tool_choice="auto")
  → if finish_reason=="tool_calls":
      for each tool call:
        exec_tool(name, args) → result
        broadcast_action → browser Actions tab
      history.append(tool results)
      LLM (streaming, no tools) → final reply text
  → TTS → speaker
```

---

## Voice Activity Detection (VAD)

Current baseline is simple energy-based VAD using RMS amplitude:

```python
rms = sqrt(mean(frame^2))
if rms > RMS_THRESH (500):
    loud_count++
if loud_count >= START_FRAMES (3):  # ~90ms of speech
    → start recording
if quiet_count >= END_FRAMES (20):  # ~600ms of silence
    → stop, transcribe
```

This was raised from an older 250-threshold setup to reduce ambient false triggers.

---

## Barge-in

While TTS is playing, the mic continues reading.
If RMS > BARGE_RMS (1100) for BARGE_FRAMES (4) consecutive frames:
→ `speak_task.cancel()` → TTS stops mid-sentence
→ VAD restarts → user can speak

Speaker echo may trigger false barge-in (no echo cancellation yet).

---

## WebSocket Protocol

### Server → Client

| Type | Payload | Description |
|---|---|---|
| `init` | `{provider, model, mode, memory}` | Sent on connect |
| `state` | `{state: "listening"\|"recording"\|...}` | State machine update |
| `transcript` | `{role, text}` | User or assistant message |
| `volume` | `{level: 0.0–1.0}` | Mic RMS for visualizer |
| `action` | `{action, params, result}` | Tool call result |
| `screenshot` | `{data: base64jpeg}` | Screen capture |
| `model_changed` | `{provider, model}` | After model switch |
| `memory_updated` | `{memory}` | After memory change |

### Client → Server

| Type | Payload | Description |
|---|---|---|
| `mute` | `{muted: bool}` | Toggle mic |
| `set_continuous` | `{enabled: bool}` | Toggle always-listening mode |
| `mode` | `{mode: "chat"\|"operator"}` | Switch mode |
| `text` | `{text}` | Send typed message |
| `clear` | — | Clear history |
| `add_fact` | `{fact}` | Add memory fact |
| `del_fact` | `{fact}` | Remove memory fact |
| `log` | `{event, detail}` | Browser event logging |

---

## Memory System

```json
{
  "user": { "name": null, "preferences": [] },
  "facts": ["User prefers dark mode", "..."],
  "context_summary": "Recent conversation summary...",
  "session_count": 7,
  "last_session": "2025-01-15T10:30:00",
  "task_history": [
    { "task": "open chrome", "ts": "2025-01-15T10:31:00" }
  ]
}
```

Memory is injected into every LLM system prompt as context.

---

## Voice Interaction Notes

- **Always Listening ON**: VAD continuously monitors for speech and starts capture automatically.
- **Always Listening OFF**: voice input remains in standby unless wake-word mode is enabled.
- During TTS, incoming speech can interrupt playback so the assistant does not continue talking over the user.
Auto-extraction: if AI response contains "remember", names, or preferences → stored as fact.

---

## Provider Abstraction

All providers use the OpenAI-compatible API:

```python
client = AsyncOpenAI(
    base_url=PROVIDERS[current_provider]["base_url"],
    api_key=PROVIDERS[current_provider]["api_key"],
)
```

| Provider | base_url | Notes |
|---|---|---|
| Ollama | `http://localhost:11434/v1` | No internet, any installed model |
| OpenAI | `https://api.openai.com/v1` | Requires OPENAI_API_KEY |
| GitHub | `https://models.inference.ai.azure.com` | Requires GITHUB_TOKEN |
