# Copilot VS Code Update Note

Use this message in GitHub Copilot Chat inside VS Code to update context on recent Open Harness changes:

```
Context update for C:\project\vision\open-harness:

1) Runtime architecture updates
- Added centralized runtime/provider configuration in src/runtime.ts
- Supports MODEL_PROVIDER=ollama|openai
- Unified model selection via MODEL_NAME fallback chain
- Centralized Vision MCP stdio config via getVisionMcpServerConfig()

2) Startup and readiness
- Added Vision preflight checks in src/preflight.ts (GET /api/health)
- CLI now runs preflight before starting agent loop
- Added dedicated health command in src/health.ts and npm run health
- Health validates:
  - MCP script path exists
  - Vision API reachability
  - Ollama connection and model presence (or OPENAI_API_KEY if provider=openai)

3) Agent/session behavior
- src/vision-agent.ts now uses Session (not just stateless run)
- Added retry behavior and turn-level telemetry output
- Added safer approval policy with risk scoring
- Read-only tools auto-approve; unsafe tools prompt unless VISION_AUTO_APPROVE_UNSAFE=true

4) Subagent demo hardening
- src/subagent-demo.ts now uses shared runtime config helpers
- Includes preflight output and safer approval defaults
- Uses session retry config and consistent MCP wiring

5) Orchestration
- Added start-all.ps1
  - Starts Vision backend if port 8765 is not listening
  - Waits for /api/health readiness
  - Runs npm run health
  - Launches npm run start:vision-agent
- Added npm scripts:
  - npm run health
  - npm run start:all

6) Env/docs updates
- Extended .env.example with:
  - MODEL_PROVIDER, MODEL_NAME
  - OPENAI settings
  - MCP process options
  - AGENT_MAX_STEPS, AGENT_CONTEXT_WINDOW
  - VISION_AUTO_APPROVE_UNSAFE
- README updated with health and start:all workflow

Current status:
- Typecheck passes
- Harness runs
- Vision connectivity can still fail when backend is not running; health + preflight now make this explicit

Please use this as baseline context for future edits in this folder.
```
