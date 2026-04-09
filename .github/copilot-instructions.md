# Vision Copilot Instructions

This repository is a Windows-first local accessibility operator with a FastAPI/WebSocket backend, browser UI, voice pipeline, and desktop-control tool layer.

## Working Priorities
- Preserve the architecture split from `architecture.md`: perception, brain, and action are separate concerns.
- Treat `live_chat_app.py` as the backend entrypoint and `live_chat_ui.html` as the primary UI unless the task explicitly targets an alternate UI file.
- Keep chat mode and operator mode behavior distinct. Do not collapse tool-calling logic into the normal chat streaming path.
- Preserve the existing WebSocket contract unless the task explicitly includes coordinated backend and frontend protocol changes.

## Runtime Assumptions
- Primary local URL: `http://localhost:8765`
- WebSocket endpoint: `ws://localhost:8765/ws`
- Supported providers in this repo: Ollama, OpenAI, GitHub Models
- ElevenLabs is used for STT/TTS when keys are present; some local fallbacks appear in tests

## Verification Guidance
- For backend or protocol changes, prefer targeted verification with `python test_tools.py` or `python test_vision.py` when practical.
- For setup and runtime issues, consult `setup.md`, `README.md`, and `architecture.md` before changing code.
- When debugging tool execution, inspect both direct tool invocation and natural-language-triggered tool calls.

## Editing Guidance
- Prefer minimal, surgical changes over broad rewrites.
- Keep Windows-specific behavior intact unless cross-platform improvements are explicitly required.
- If a change affects memory, model/provider selection, voice thresholds, or WebSocket message types, call that out clearly in the final summary.
