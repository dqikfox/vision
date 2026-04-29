# Architecture — Universal Accessibility Operator

## Overview

The system is a real-time voice-controlled AI operator with three layers:

```
┌─────────────────────────────────────────────────────┐
│                    PERCEPTION                       │
│  Microphone → VAD → STT → Intent extraction        │
├─────────────────────────────────────────────────────┤
│                     BRAIN                           │
│  LLM (Ollama/OpenAI/GitHub/Groq/Gemini/DeepSeek/    │
│       Mistral/Anthropic/xAI) + Memory + Planning    │
├─────────────────────────────────────────────────────┤
│                     ACTION                          │
│  Tools: OCR, click, type, key, scroll, command      │
└─────────────────────────────────────────────────────┘
```

The Command Center now presents this runtime as two supervisory bands:
- **Core Operator Layer** — launcher, local-model/runtime readiness, health, voice/tool responsiveness
- **Cognitive Layer** — context brain, missions, memory/catalog surfaces, skills, agents, and orchestration

This is a monitoring and control split, not a change to the underlying Perception → Brain → Action runtime.

---

## Data Flow

### Chat Mode
```
mic frame (480 samples @ 16kHz)
  → if always-listening disabled and wake-word mode is off: remain in voice standby
  → VAD.feed() → "start" | "frame" | "end"
  → "end": concatenate frames → WAV → STT cascade
      1. ElevenLabs scribe_v1
      2. Groq whisper-large-v3-turbo
      3. faster-whisper tiny (offline fallback)
  → text → provider-specific LLM stream
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
| `token` | `{text}` | Streaming LLM token |
| `stream_start` | — | LLM stream beginning |
| `stream_finalize` | `{text}` | Full assembled response |
| `volume` | `{level: 0.0–1.0}` | Mic RMS for visualizer |
| `action` | `{action, params, result}` | Tool call result |
| `screenshot` | `{data: base64jpeg}` | Screen capture |
| `thinking` | `{text}` | Reasoning/thinking tokens (think-mode models) |
| `model_changed` | `{provider, model}` | After model switch |
| `memory_updated` | `{memory}` | After memory change |
| `key_saved` | `{provider}` | After API key stored |
| `voice_settings` | `{voice_id, rate, ...}` | After voice settings change |
| `el_agent` | `{status, agent_id}` | ElevenLabs ConvAI agent state |
| `partial_transcript` | `{text}` | Partial STT result during recording |

### Client → Server

| Type | Payload | Description |
|---|---|---|
| `text` or `input` | `{text}` | Send typed message |
| `mute` | `{muted: bool}` | Toggle mic |
| `mode` | `{mode: "chat"\|"operator"}` | Switch mode |
| `set_model` | `{provider, model}` | Switch active provider/model |
| `set_api_key` | `{provider, key}` | Store API key securely |
| `set_voice_settings` | `{voice_id?, rate?, volume?}` | Update TTS settings |
| `execute_tool` | `{name, parameters}` | Run a tool directly via WebSocket |
| `add_fact` | `{fact}` | Add memory fact |
| `del_fact` | `{fact}` | Remove memory fact |
| `clear` | — | Clear conversation history |
| `log` | `{event, detail}` | Browser event logging |
| `el_agent_start` | — | Start ElevenLabs ConvAI agent |
| `el_agent_stop` | — | Stop ElevenLabs ConvAI agent |

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

Most providers use the OpenAI-compatible API:

```python
client = AsyncOpenAI(
    base_url=PROVIDERS[current_provider]["base_url"],
    api_key=PROVIDERS[current_provider]["api_key"],
)
```

Anthropic uses its native SDK, and Ollama uses its own async client for local streaming and tool support.

Current routing behavior:
- Ollama uses a native `ollama.AsyncClient`
- Anthropic uses the native Anthropic SDK tool loop
- OpenAI uses the Responses API for `gpt-4.1`, `gpt-4.1-mini`, `o4-mini`, `o3`, and `computer-use-preview`
- GitHub, Groq, Gemini, DeepSeek, Mistral, and xAI use OpenAI-compatible chat completions
- If Ollama fails, provider fallback order is `github → groq → gemini → deepseek → openai → mistral → anthropic → xai`

| Provider | base_url | Notes |
|---|---|---|
| Ollama | `http://localhost:11434/v1` | No internet, any installed model |
| OpenAI | `https://api.openai.com/v1` | Requires OPENAI_API_KEY; Responses API for o-series/computer-use |
| GitHub | `https://models.inference.ai.azure.com` | Requires GITHUB_TOKEN |
| DeepSeek | `https://api.deepseek.com/v1` | Requires DEEPSEEK_API_KEY |
| Groq | `https://api.groq.com/openai/v1` | Requires GROQ_API_KEY; also used for Whisper STT |
| Mistral | `https://api.mistral.ai/v1` | Requires MISTRAL_API_KEY |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` | Requires GEMINI_API_KEY |
| Anthropic | native SDK (not OpenAI-compatible) | Requires ANTHROPIC_API_KEY; requires `pip install anthropic` |
| xAI (Grok) | `https://api.x.ai/v1` | Requires XAI_API_KEY; vision via grok-2-vision-1212 |
