---
name: vision-performance
description: 'Profile, benchmark, and optimize Vision operator performance. Use for diagnosing latency in STT/TTS/LLM pipeline, memory leaks, high CPU/GPU usage, or slow tool execution.'
argument-hint: 'Describe the symptom: high latency, memory growth, slow startup, or specific tool bottleneck.'
user-invocable: true
---

# Vision Performance

## Live Metrics
```powershell
Invoke-RestMethod http://localhost:8765/api/metrics
# Returns: cpu, ram, ram_used_gb, disk, gpu, gpu_mem, gpu_name
```

## Latency Budget (targets)
| Stage | Target |
|---|---|
| VAD detection | ~90ms |
| STT ElevenLabs | 300–800ms |
| LLM first token (Groq) | <500ms |
| LLM first token (Ollama) | <2s |
| TTS first audio (ElevenLabs flash) | ~300ms |
| Total voice round-trip | <3s |

## Common Bottlenecks & Fixes
| Symptom | Cause | Fix |
|---|---|---|
| Slow first response | Ollama cold start | Pre-warm: `ollama run llama3.2 ""` |
| High RAM | History unbounded | History capped at 20 — verify cap is active |
| TTS cuts out | WS buffer underrun | Increase sentence buffer in `_send()` |
| OCR slow | Full-screen Tesseract | Crop region before OCR |
| Playwright slow | Browser cold start | `_prewarm_playwright` runs at startup — check logs |
| CPU spike | Blocking call on event loop | Wrap in `await loop.run_in_executor(None, fn)` |

## Optimization Checklist
- [ ] Ollama model loaded in RAM (not swapping to disk)
- [ ] ElevenLabs `auto_mode=true` enabled (already set)
- [ ] faster-whisper using `int8` quantization (already set)
- [ ] Playwright pre-warmed at startup (already set)
- [ ] History capped at 20 messages (already set)
- [ ] Screenshots JPEG quality=55 (already set)
- [ ] `_stt_failure_until` cooldown not stuck (check if all STT providers failed)
