---
name: vision-context-brain
description: 'Generate and use a machine-readable context brain before broad tasks, post-compaction recovery, or external agent bootstrapping.'
argument-hint: 'Describe why a deep refresh is needed: broad task, context loss, external harness bootstrap, or repo-awareness gap.'
user-invocable: true
---

# Vision Context Brain

Use this skill when a task is too broad for ad hoc file reads and you want a structured cognition pack first.

## Core Files
- `hive_tools/context_mapper.py` - generates the machine-readable context brain
- `.archon/artifacts/project_context.json` - default output artifact for the latest generated context brain
- `.github/copilot-instructions.md` - always-on repo guidance that should stay aligned with the generator
- `DOCUMENTATION_INDEX.md` - top-level doc map that should match the generator's refresh order
- `.archon/config.yaml` and `.archon/workflows/` - deterministic workflow layer that should be reflected in the brain

## Procedure
1. Generate the latest context brain.
   - Run `python hive_tools\context_mapper.py --output .archon\artifacts\project_context.json`
   - Use `--stdout` when you want the JSON inline instead of writing a file

2. Read the context brain before broad work.
   - Start with `refresh.primary_order`
   - Use `catalog.skills`, `catalog.agents`, and `integration.mcp_servers` to choose the next repo surfaces
   - Use `automation.validation_commands` to decide which existing checks apply

3. Improve the brain when it goes stale.
   - Update the generator if it misses a key repo surface
   - Update instructions/docs if the generator's output no longer matches reality

## Completion Checks
- A fresh `.archon/artifacts/project_context.json` exists or the equivalent JSON was emitted to stdout
- The next task can choose files, skills, agents, and validation steps from the brain instead of guessing
- Any generator drift is fixed in the same task
