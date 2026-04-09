---
name: vision-runtime-ops
description: 'Run, validate, and troubleshoot the Vision accessibility operator locally. Use for starting the FastAPI/WebSocket app, checking providers, confirming browser connectivity, and running runtime smoke tests.'
argument-hint: 'Describe whether you need startup, runtime verification, provider checks, or local troubleshooting.'
user-invocable: true
---

# Vision Runtime Operations

Use this skill to start the local operator reliably and verify the end-to-end runtime path.

## When to Use
- Start the local operator stack
- Confirm the browser UI and WebSocket endpoint are healthy
- Check provider readiness before deeper debugging
- Run smoke tests after changes to backend or UI

## Core Files
- `live_chat_app.py` - backend server entrypoint
- `live_chat_ui.html` - main browser UI
- `setup.md` - environment and dependency checklist
- `README.md` - high-level runtime and provider overview

## Procedure
1. Confirm local prerequisites from `setup.md`.
- Python dependencies installed
- Tesseract installed if OCR-related tools are in scope
- Ollama running if local model coverage is needed
- `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`, or `GITHUB_TOKEN` set if those providers are expected

2. Start the app.
- Run `python live_chat_app.py`
- Confirm the service binds to `http://localhost:8765`

3. Verify transport health.
- Check `GET /`
- Check `GET /api/models`
- Connect to `ws://localhost:8765/ws` and confirm the initial `init` message

4. Verify user-facing readiness.
- Open the browser UI
- Confirm the connected indicator appears
- Confirm current provider/model are populated

5. Run a smoke test when needed.
- `python test_tools.py` for tool interaction validation
- `python test_vision.py` for broader integration validation

## Completion Checks
- App serves HTTP successfully
- WebSocket init works
- At least one provider path is available for the target scenario
- UI connects and shows runtime state
