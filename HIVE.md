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

### Advanced Orchestration Patterns

Inspired by the [ComposioHQ/agent-orchestrator](https://github.com/ComposioHQ/agent-orchestrator), we implement the following advanced patterns:

1. **Workspace Isolation:**
   - For complex, concurrent tasks, agents should ideally operate in isolated environments.
   - **Strategy:** Utilize `git worktree` when implementing features across multiple branches to prevent file system collisions.

2. **Event-Driven Reactions:**
   - The Hive Mind monitors for external signals (e.g., test failures, CI errors, or user hints) and triggers "Reactions" from the relevant agent.
   - **Self-Healing:** If `@coding-agent` introduces a bug detected by `@debug-agent`, the Hive Mind automatically routes the fix back to the coding agent.

3. **Parallel Worker Management:**
   - Multiple agents can be dispatched simultaneously for independent sub-tasks (e.g., `@analysis-agent` auditing security while `@maintenance-agent` updates dependencies).
   - **Concurrency Safety:** The Hive Mind ensures that agents do not mutate the same files simultaneously unless isolated via worktrees.

4. **Task Lifecycle Management:**
   - **Planning:** The Hive Mind maps the objective and selects the best agent.
   - **Execution:** Specialized agents perform the work and validate it.
   - **Validation & Feedback:** All changes are verified through tests and project-specific standards. If validation fails, the task cycles back into execution.

---

*This swarm is designed to grow. New agents can be added to `.gemini/agents/` as the project evolves.*

