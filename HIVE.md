# HIVE MIND — Elite Copilot Optimizer Strategy

> "Optimizing the intelligence that builds the future."

This project is managed by a **Hive Mind** (Gemini CLI) and an **Elite Swarm** of specialized **Copilot Optimizers**. This architecture ensures that AI-generated code is not just "functional," but secure, efficient, and idiomatic.

## The Elite Optimizer Swarm

| Agent | Purpose | Optimization Focus |
|---|---|---|
| **@analysis-agent** | Context Architect. | Type Hints & Project Mapping |
| **@coding-agent** | Completion Refiner. | Idiomatic PEP 8 & Modularity |
| **@maintenance-agent** | Workflow Automator. | Snippets & Tool Integration |
| **@security-agent** | Safe Auditor. | Zero-Trust AI Completions |
| **@debug-agent** | Mistake Tracker. | Corrective Prompt Engineering |
| **@vision-maintainer** | Operator Protocol Guardian. | WebSocket, perception, tool routing |
| **@openclaw-operator** | Gateway Orchestrator. | Installation, daemon, SLA enforcement |
| **@mcp-builder** | Customization Specialist. | MCP wiring, skills, and agent expansion |
| **@context-steward** | Repo Awareness Specialist. | Memory workflow, context refresh, Copilot customization |
| **@home-ops-steward** | Home Operations Specialist. | System admin, network reliability, security, backups, automation |

## Elite Infrastructure (Hive Tools)

Agents leverage specialized scripts in `hive_tools/` for autonomous optimization:
- `hive_tools/copilot_audit.py`: AST-based scan for "Context Entropy".
- `hive_tools/style_enforcer.py`: PEP 8 & Idiom verification.
- `hive_tools/snippet_generator.py`: Pattern-based VS Code snippets.
- `hive_tools/context_mapper.py`: Machine-readable context brain generator for repo refresh, workflow bootstrap, and compaction recovery.
- `vision_command_center.html`: Browser command center for launching, monitoring, and opening the repo's runtime and intelligence surfaces.
- `vision_command_center_config.json`: Non-sensitive profile layer for command-center theme, refresh cadence, and launcher behavior.
- `hive_tools/copilot_mistakes.log`: Data-driven iterative learning.

## The Mission

1. **Enhance Context:** Provide Copilot with the best possible signals through type hints, docstrings, and clean architecture.
2. **Refine Output:** Surgical refactoring of AI suggestions for maximum efficiency and maintainability.
3. **Ensure Safety:** Automated security gates for all AI-generated code.
4. **Automate Friction:** Eliminate repetitive tasks through snippets and project scaffolding.

---

*The AI is a tool. The Swarm is the craftsman. The Hive Mind is the vision.*

## Copilot Customization Layer (VS Code-Native)

In addition to the CLI-based Hive Mind, this repo includes a **Copilot Customization Layer** stored in `.github/`:

### Always-On Guidance
- **`.github/copilot-instructions.md`**: Repository-scoped instructions loaded in every Copilot chat. Covers working priorities, runtime assumptions, verification patterns, and editing rules.
- **`RAG_PLUGIN_WORKSPACE` (via workspace MCP)**: External local LM Studio plugin workspace path for LM Studio and RAG-related tasks. If unset, the repo falls back to `F:\rag-v1` on Windows and `~/rag-v1` elsewhere.
- **`vision_mcp_server.py`**: Repo-local MCP bridge that can be consumed by external harnesses with MCP support, including OpenHarness-style stdio MCP clients.
- **`http://localhost:8765/command-center`**: Separate Command Center UI for health/metrics monitoring, context-brain refresh, workflow launch, and fast access to docs, skills, agents, and MCP surfaces.
- **`DOCUMENTATION_INDEX.md`**: Top-level map for runtime, customization, and debugging documentation.

### On-Demand Skills (invoke with `/skill-name`)
- **`vision-operator`**: Operate Vision end-to-end across voice, tools, and accessibility workflows
- **`vision-runtime-ops`**: Start, verify, and smoke-test the local Vision stack
- **`vision-debugging`**: Root-cause analysis for voice, WebSocket, provider, OCR, tool-call failures
- **`vision-tool-audit`**: Audit direct tool execution and NL routing behavior
- **`vision-tool-dev`**: Add new Vision tools with the required schema, handler, and registration wiring
- **`vision-code-review`**: Review changes for correctness, type safety, async hazards, and Vision-specific patterns
- **`vision-type-safety`**: Fix mypy and type-annotation issues in Vision code
- **`vision-context-brain`**: Generate and use a machine-readable context brain before broad tasks or after context compaction
- **`vision-cognitive-council`**: Gather multiple fresh specialist viewpoints before broad, risky, or ambiguous work
- **`vision-context-ops`**: Improve Copilot repo awareness, memory workflow, and context continuity (`.github/skills/vision-context-ops/SKILL.md`)
- **`vision-home-ops`**: Apply Vision to home PC, network, security, backup, and automation work
- **`vision-documentation-ops`**: Keep docs, skill listings, and runtime notes synchronized
- **`vision-mcp-builder`**: Add or expand repo-local MCP servers and related customizations
- **`vision-mcp-tools`**: Use the active MCP server surface effectively inside this workspace
- **`vision-git-ops`**: Work with commits, branches, PRs, tags, and repo history safely
- **`vision-web-research`**: Research Vision-related topics on the web with MCP-backed search and fetch
- **`vision-performance`**: Profile and optimize latency, memory, and CPU/GPU usage
- **`vision-multi-monitor`**: Coordinate capture and actions across multiple displays
- **`vision-adb-control`**: Control Android devices via ADB from Vision workflows
- **`mcp-recovery`**: Diagnose and restore MCP server configuration

### Specialized Agents (invoke via Copilot Chat)
- **Vision Maintainer**: Focused handler for operator runtime, WebSocket protocol, tool calling, and code changes to `live_chat_app.py`
- **OpenClaw Operator**: Dedicated agent for OpenClaw installation, daemon setup, gateway bootstrapping, and multi-agent orchestration
- **MCP Builder**: Dedicated agent for MCP server wiring, repo-local bridges, and Copilot customization changes
- **Context Steward**: Dedicated agent for improving Copilot instructions, memory workflow, and repo-awareness surfaces
- **Home Ops Steward**: Dedicated agent for home-environment maintenance, security, backup, and automation workflows
- **Code Review Agent**: Dedicated reviewer for correctness, security, performance, type safety, and Vision-specific patterns
- **Refactor Agent**: Dedicated refactoring specialist for structural cleanup without behavior changes

### How to Use
1. Open Copilot Chat (`Ctrl+Shift+I` or `Cmd+Shift+I`)
2. Type `/skill-name` to invoke a skill (e.g., `/vision-runtime-ops`)
3. Ask a question about your task; Copilot will route to the appropriate skill or agent
4. Type `@agent-name` to force a specific agent (e.g., `@Vision Maintainer` for protocol/runtime issues)

### External Harness Interop
If you want to drive Vision from another agent runtime, prefer reusing `vision_mcp_server.py` over re-implementing the HTTP API surface. MCP-capable runtimes such as OpenHarness can attach to the bridge over stdio and inherit the existing Vision tool model.

For deterministic multi-step maintenance, the repo can also be driven by Archon workflows committed under `.archon/workflows/`. Vision now ships repo-local workflows for general maintenance and external-agent integration so the process can be reused across runs.
Repo-local Archon defaults live in `.archon/config.yaml`, and the expected entrypoints are `archon workflow list --cwd C:\project\vision` plus targeted `archon workflow run ...` commands from the repo root.
When a task is broad or context was compacted, start with `python hive_tools\context_mapper.py --output .archon\artifacts\project_context.json` or the `vision-context-brain-refresh` Archon workflow.
When the task is broad, risky, or ambiguous, run the `vision-cognitive-council` workflow after the initial refresh to force multiple independent viewpoints before implementation.
