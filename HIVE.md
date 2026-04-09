# HIVE MIND — Swarm Orchestration Strategy

> "We are many, yet we act as one."

This project is now managed by a **Hive Mind** (Gemini CLI) and a specialized **Swarm** of subagents. This architecture ensures that every task—from low-level maintenance to high-level architecture analysis—is handled by an expert with a focused context and toolset.

## The Swarm

| Agent | Purpose | Key Tools |
|---|---|---|
| **@maintenance-agent** | System health, dependencies, logs, and integrity. | `run_shell_command`, `read_file` |
| **@debug-agent** | Root cause analysis, bug reproduction, and fixing. | `grep_search`, `replace`, `run_shell_command` |
| **@analysis-agent** | Architecture review, performance auditing, and security. | `codebase_investigator`, `glob` |
| **@coding-agent** | Feature implementation, refactoring, and testing. | `write_file`, `replace`, `run_shell_command` |

## Orchestration (The Hive Mind)

As the **Hive Mind**, I (Gemini CLI) coordinate these agents. You can invoke them explicitly using the `@` syntax, or I will automatically delegate tasks to them based on your requests.

### Usage Examples

- **Maintenance:** `@maintenance-agent Check for outdated dependencies and verify the environment.`
- **Debug:** `@debug-agent Analyze the logs for any recent failures in the TTS pipeline.`
- **Analysis:** `@analysis-agent Perform a security audit of the credential management in keys.py.`
- **Coding:** `@coding-agent Implement a new tool for taking multi-monitor screenshots.`

## Command Protocol

1. **Research:** The Hive Mind maps the objective and selects the best agent for the task.
2. **Delegation:** The task is handed off to the specialized agent.
3. **Execution:** The agent performs the work, validates it, and reports back.
4. **Synthesis:** The Hive Mind reviews the agent's work and presents the final outcome.

---

*This swarm is designed to grow. New agents can be added to `.gemini/agents/` as the project evolves.*
