# VISION Project File

## Mission
Build and maintain VISION as a reliable, secure, and high-performance accessibility operator that enables full computer control through voice and text.

## Current Scope
- Windows-first runtime with FastAPI + WebSocket backend
- Real-time voice and chat interface
- Tool execution for desktop, browser, file, and system operations
- Multi-provider LLM routing and model switching
- Persistent memory and operational telemetry
- Home-ops workflows for single-user PC/network maintenance

## Product Pillars
1. Accessibility and usability
2. Reliability and resilience
3. Security and privacy
4. Performance and low latency
5. Automation and maintainability

## Architecture Summary
- Backend: `live_chat_app.py`
- Primary UI: `live_chat_ui.html`
- Memory store: `memory.json`
- Event log: `chat_events.log`
- MCP integration: workspace-configured servers for tools, memory, and automation

## Evolution Roadmap

### Phase 1: Runtime Hardening
- Strengthen startup validation and dependency checks
- Improve health endpoint diagnostics and provider visibility
- Expand tool execution smoke coverage

### Phase 2: Voice and Interaction Quality
- Reduce end-to-end voice latency with tighter pipeline instrumentation
- Improve barge-in reliability and transcript consistency
- Add clearer user feedback states in the UI

### Phase 3: Tooling and Safety
- Expand tool guardrails and intent verification for high-risk actions
- Standardize tool error formats and recovery suggestions
- Add audit-friendly traces for operator actions

### Phase 4: Home Ops Automation
- Add repeatable workflows for backup verification and cleanup
- Add network and system maintenance automation tasks
- Add periodic health summary generation and alerts

### Phase 5: Documentation and Contributor Experience
- Keep architecture and setup docs synchronized with runtime behavior
- Improve onboarding flow for local setup and verification
- Document playbooks for common failures and recovery

## Success Metrics (Rolling 30 Days)
- Runtime availability: >= 99.5% local session uptime during active use
- Voice responsiveness: median STT -> first token <= 1.5s
- Tool reliability: >= 98% successful tool execution for non-destructive actions
- Recovery speed: median time to recover from provider/tool failure <= 2 minutes
- Documentation freshness: <= 1 known runtime/doc drift item open > 14 days until automated doc consistency checks are live

## Active Iteration Board

### Now (In Progress)
- [ ] Add runtime preflight checks for keys, OCR binary, browser availability, and audio devices
- [ ] Add structured stage timing for STT, LLM, tool-call loop, and TTS
- [ ] Add weekly home-ops maintenance workflow and summary output
- [ ] Add automated doc consistency checks for key runtime contracts

### Next (Planned)
- [ ] Add high-risk action confirmations with explicit user intent capture
- [ ] Add standard tool error taxonomy and user-facing recovery hints
- [ ] Add operator action trace export for debugging and audits

### Later (Queued)
- [ ] Add latency benchmark baselines per model/provider combination
- [ ] Add onboarding validator that runs setup and smoke checks end-to-end

## Iteration Cadence
- Planning: weekly, prioritize top 3 items from Now/Next
- Delivery: small, testable changes merged continuously
- Validation: run health + smoke/integration checks after runtime-affecting changes
- Review: close or re-scope stale tasks every 2 weeks

## Risks and Mitigations
- Provider instability
	- Mitigation: strengthen fallback routing and expose clearer provider health state
- WebSocket contract breaking changes
	- Mitigation: use versioned message contracts, keep schemas backward-compatible, coordinate deploys, and run automated integration tests
- Local environment drift
	- Mitigation: preflight checks and one-command runtime validation
- Credential leakage
	- Mitigation: enforce secret scanning, log redaction, environment variable policies, and pre-commit hooks that block committing secrets
- Network/authentication failures
	- Mitigation: add retry/backoff logic, token refresh and rotation policies, health checks/synthetic monitoring, and clearer auth/timeout error surfaces
- Tool safety regressions
	- Mitigation: enforce confirmations for high-risk actions and add regression tests
- Documentation drift
	- Mitigation: require doc updates in the same change when behavior changes

## Quality Gates
- Health endpoint passes: `GET /api/health`
- Core tools smoke test passes: `python test_tools.py`
- Integration test passes: `python test_vision.py`
- No secrets logged or committed

## Definition of Done for New Features
- Feature works in operator mode and chat mode where applicable
- Error paths are handled with actionable messages
- Metrics/logging are sufficient for debugging
- Docs updated in the same change when behavior changes
- Relevant tests added or updated

## Immediate Next Iteration
1. Add a runtime preflight command to validate provider keys and local dependencies
2. Add structured timing metrics for STT -> LLM -> TTS stages
3. Add a weekly maintenance workflow for system and backup health checks

## Change Log
- 2026-04-11: Initialized project file with mission, roadmap, quality gates, and ownership
- 2026-04-11: Added success metrics, iteration board, cadence, and risk management sections

## Ownership
- Primary maintainers: project owner and collaborating agents
- Source of truth for runtime behavior: `live_chat_app.py`
- Source of truth for operator UX: `live_chat_ui.html`
