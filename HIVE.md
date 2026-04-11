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
- `hive_tools/context_mapper.py`: Dependency & structure mapping.
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
- **`F:\rag-v1` (via workspace MCP)**: External local LM Studio plugin workspace available as an extra context source for LM Studio and RAG-related tasks.
- **`DOCUMENTATION_INDEX.md`**: Top-level map for runtime, customization, and debugging documentation.

### On-Demand Skills (invoke with `@skill-name`)
- **`vision-runtime-ops`**: Start, verify, and smoke-test the local Vision stack
- **`vision-debugging`**: Root-cause analysis for voice, WebSocket, provider, OCR, tool-call failures
- **`vision-tool-audit`**: Audit direct tool execution and NL routing behavior
- **`vision-context-ops`**: Improve Copilot repo awareness, memory workflow, and context continuity
- **`vision-home-ops`**: Apply Vision to home PC, network, security, backup, and automation work
- **`vision-documentation-ops`**: Keep docs, skill listings, and runtime notes synchronized
- **`vision-mcp-builder`**: Add or expand repo-local MCP servers and related customizations
- **`mcp-recovery`**: Diagnose and restore MCP server configuration

### Specialized Agents (invoke via Copilot Chat)
- **Vision Maintainer**: Focused handler for operator runtime, WebSocket protocol, tool calling, and code changes to `live_chat_app.py`
- **OpenClaw Operator**: Dedicated agent for OpenClaw installation, daemon setup, gateway bootstrapping, and multi-agent orchestration
- **MCP Builder**: Dedicated agent for MCP server wiring, repo-local bridges, and Copilot customization changes
- **Context Steward**: Dedicated agent for improving Copilot instructions, memory workflow, and repo-awareness surfaces
- **Home Ops Steward**: Dedicated agent for home-environment maintenance, security, backup, and automation workflows

### How to Use
1. Open Copilot Chat (`Ctrl+Shift+I` or `Cmd+Shift+I`)
2. Type `/skill-name` to invoke a skill (e.g., `/vision-runtime-ops`)
3. Ask a question about your task; Copilot will route to the appropriate skill or agent
4. Type `@agent-name` to force a specific agent (e.g., `@Vision Maintainer` for protocol/runtime issues)
