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

Simple energy-based VAD using RMS amplitude:

```python
rms = sqrt(mean(frame^2))
if rms > RMS_THRESH (250):
    loud_count++
if loud_count >= START_FRAMES (3):  # ~90ms of speech
    → start recording
if quiet_count >= END_FRAMES (33):  # ~1s of silence
    → stop, transcribe
```

Calibrated for the user's mic: background RMS ~54, speech peak ~970.

---

## Barge-in

While TTS is playing, the mic continues reading.
If RMS > BARGE_RMS (1200) for BARGE_FRAMES (8) consecutive frames:
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
| `memory_update` | `{memory}` | After memory change |

### Client → Server

| Type | Payload | Description |
|---|---|---|
| `mute` | `{muted: bool}` | Toggle mic |
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
  "session_count": 7,
  "last_session": "2025-01-15T10:30:00",
  "task_history": [
    { "task": "open chrome", "ts": "2025-01-15T10:31:00" }
  ]
}
```

Memory is injected into every LLM system prompt as context.
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
