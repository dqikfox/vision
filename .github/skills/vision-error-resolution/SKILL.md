---
name: vision-error-resolution
description: 'Systematically resolve Vision errors using an analyze-identify-fix-review-apply workflow. Use for degraded components, repeated failures, or crash recovery.'
argument-hint: 'Describe the error, degraded component, or failing runtime path you need to resolve.'
user-invocable: true
---

# Vision Error Resolution Skill

## Purpose
Run the full **Analyze → Identify → Fix → Review → Confirm → Apply** cycle for any Vision
system error. Use this skill whenever an error, degraded component, or crash needs
systematic investigation and repair — not just a one-off patch.

## Core files
| File | Role |
|------|------|
| `vision_errors.jsonl` | Machine-readable error ledger — primary input |
| `vision_structured.log` | Structured JSON logs with context |
| `hive_tools/error_analyzer.py` | Pipeline entry point |
| `vision_diagnostics.py` | Error ledger API + `/api/diagnostics` |
| `vision_watchdog.py` | Background monitor + circuit breaker |
| `vision_errors.py` | Typed exception hierarchy |
| `vision_logger.py` | Structured logger |
| `.archon/workflows/vision-error-resolution.yaml` | Full DAG workflow |
| `.github/agents/error-sentinel.agent.md` | Autonomous sentinel |

## Procedure

### Quick check (read-only, no changes)
```bash
python hive_tools/error_analyzer.py --report
```
Prints: error groups, root cause hypotheses, fix plans, review result — without applying anything.

### Full automated cycle
```bash
# With confirmation prompt (default)
python hive_tools/error_analyzer.py --full-cycle

# Fully automatic (CI / autonomous use)
python hive_tools/error_analyzer.py --full-cycle --auto

# Dry run (plan but don't execute)
python hive_tools/error_analyzer.py --full-cycle --dry-run
```

### Archon workflow (multi-step, with approval gate)
```
/workflow run vision-error-resolution
```
Runs the full DAG with a human approval step before applying changes.

### Single-stage (for custom pipelines)
```bash
python hive_tools/error_analyzer.py --stage analyze  --output /tmp/a.json
python hive_tools/error_analyzer.py --stage identify --input /tmp/a.json --output /tmp/b.json
python hive_tools/error_analyzer.py --stage fix      --input /tmp/b.json --output /tmp/c.json
python hive_tools/error_analyzer.py --stage review   --input /tmp/c.json --output /tmp/d.json
python hive_tools/error_analyzer.py --stage apply    --input /tmp/c.json
```

## Diagnostic endpoints
| Endpoint | Returns |
|----------|---------|
| `GET /api/errors` | Last 50 unresolved errors with full context |
| `GET /api/errors?unresolved=true` | Unresolved only |
| `GET /api/errors?category=provider` | Filter by category |
| `POST /api/errors/{id}/resolve` | Mark an error as resolved |
| `GET /api/diagnostics` | Full system snapshot: health + errors + metrics |
| `GET /api/health` | Enhanced: HEALTHY / DEGRADED / UNHEALTHY per component |

## Error categories
| Category | Examples |
|----------|---------|
| `provider` | LLM API call failed, rate limited, auth error |
| `tool` | Screenshot, OCR, run_command failed |
| `voice` | VAD, STT, TTS, microphone error |
| `websocket` | Client disconnect, message parsing failure |
| `auth` | API key missing or invalid |
| `config` | .env misconfiguration |
| `ocr` | Tesseract not installed or failed |
| `network` | HTTP timeout, connection refused |
| `memory` | memory.json read/write failure |
| `system` | OS-level failure |

## Resolution patterns
| Root cause | Standard fix |
|------------|-------------|
| API key missing | Check `.env`, restart app |
| Provider timeout | Increase timeout, activate fallback chain |
| Rate limit (429) | Add circuit breaker backoff |
| Ollama unreachable | Restart Ollama service |
| Missing dependency | `pip install -r requirements.txt` |
| VAD/mic failure | Check sounddevice, microphone permissions |
| OCR failure | Verify Tesseract on PATH |
| JSON parse error | Check model output format; consider structured output |

## Completion checks
- [ ] `vision_errors.jsonl` has 0 unresolved entries (or all newly added ones are known-benign)
- [ ] `GET /api/diagnostics` returns `overall: "healthy"`
- [ ] `python -m py_compile live_chat_app.py` exits 0
- [ ] No new entries in `vision_structured.log` at ERROR or CRITICAL level
- [ ] Watchdog has not triggered auto-resolve in the last 5 minutes

## Constraints
- Never change VAD thresholds
- Never expose API key values — mask after 8 chars
- Always read `architecture.md` before touching voice-related code
- live_chat_app.py is single source of truth for backend logic
