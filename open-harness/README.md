# Vision Open Harness

Open Harness integration for the Vision accessibility operator.

This project gives you a CLI agent and a subagent demo that connect to Vision via MCP and use an Ollama-hosted model through OpenAI-compatible endpoints.

It now includes:
- provider switching (`ollama` or `openai`)
- startup preflight against Vision health endpoint
- stateful session mode with retry handling
- safer approval prompts for non-read-only tools
- persistent session storage and telemetry logs
- model fallback chain for transient provider failures

## Prerequisites

- Node.js 22+
- Vision backend running at `http://localhost:8765`
- Ollama running and serving your model

## Setup

1. Install dependencies:

```bash
npm install
```

2. Create your local environment file:

```bash
copy .env.example .env
```

3. Confirm model configuration in `.env`:

- `MODEL_PROVIDER` (`ollama` or `openai`)
- `MODEL_NAME` (recommended single source of truth)
- `MODEL_FALLBACKS` (comma-separated backup models)
- `OLLAMA_HOST` (default `127.0.0.1` for local, `0.0.0.0` for LAN exposure)
- `OLLAMA_PORT` (default `11434`)
- `OLLAMA_MODEL` (fallback model name)
- `OPENAI_API_KEY` (required for `MODEL_PROVIDER=openai`)
- `VISION_BASE_URL` (default `http://localhost:8765`)
- `VISION_MCP_PYTHON` and `VISION_MCP_SCRIPT` for custom MCP process launch
- `VISION_MCP_INCLUDE_SCREENSHOT_B64=0` to avoid sending huge base64 image blobs to the model
- `VISION_AUTO_APPROVE_UNSAFE=false` to keep destructive tool calls gated
- `SESSION_PERSIST`, `SESSION_DIR`, `SESSION_ID` for resumable sessions
- `TELEMETRY_ENABLED`, `TELEMETRY_PATH` for JSONL runtime events
- `POLICY_PATH` to enforce tool/input deny rules

## Run

Single task:

```bash
npm run start:vision-agent -- "Check Vision health and list available models"
```

Interactive CLI:

```bash
npm run start:vision-agent
```

Subagent demo:

```bash
npm run start:subagents
```

Run readiness checks only:

```bash
npm run health
```

Start Vision (if needed), run health checks, then launch the CLI agent:

```bash
npm run start:all
```

## Notes

- Vision MCP tools are namespaced by server name, so they appear as `vision_*` tool names in runs.
- The CLI agent includes approval prompts for non-read-only tools.
- The CLI and subagent demo perform a Vision preflight (`/api/health`) before starting the run.
- `npm run health` verifies MCP script path, Vision API reachability, and provider/model readiness.
- `npm run health` also checks Vision RAG status via `/api/rag/status`.
- Runtime policy defaults are defined in `.openharness-policy.json`.
- Telemetry is written to `.logs/vision-agent.jsonl` when enabled.
- Typecheck command:

```bash
npm run typecheck
```
