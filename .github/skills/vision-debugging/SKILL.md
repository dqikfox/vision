---
name: vision-debugging
description: 'Debug runtime, voice, WebSocket, and provider issues in the Vision operator. Use for root-cause analysis of startup failures, missing replies, microphone problems, OCR issues, and browser connection bugs.'
argument-hint: 'Describe the failing path: startup, audio, websocket, provider, OCR, or tool execution.'
user-invocable: true
---

# Vision Debugging

Use this skill when the operator is broken, inconsistent, or partially working.

## Debug Order
1. Reproduce the failure with the smallest possible path.
2. Identify the layer involved: startup, HTTP, WebSocket, provider, voice pipeline, or tool execution.
3. Inspect the nearest authoritative file before patching code.
4. Validate the fix with the narrowest useful test.

## Layer Map
- Startup and environment: `setup.md`, `README.md`
- Protocol and mode separation: `architecture.md`
- Integration checks: `test_vision.py`, `test_tools.py`

## Common Branches
### Startup fails
- Check Python dependency availability
- Check provider keys only by presence, never by printing secrets
- Confirm expected local ports are free and reachable

### UI connects but no meaningful reply
- Verify `/api/models` output
- Check whether the active provider actually has credentials or local models available
- Distinguish between chat-mode response failure and operator-mode tool-call failure

### Voice pipeline misbehaves
- Compare symptoms against the thresholds documented in `architecture.md`
- Avoid changing VAD and barge-in thresholds casually; treat them as calibrated values

### OCR or tool path breaks
- Confirm Tesseract and desktop-control dependencies first
- Test direct tool invocation before debugging natural-language tool routing

## Completion Checks
- Root cause is identified at a specific layer
- Fix is validated with a targeted command or test
- No unrelated voice/protocol behavior changed accidentally
