---
name: vision-documentation-ops
description: 'Keep the Vision project well documented by aligning docs, skills, agents, MCP notes, and runtime explanations with the real system.'
argument-hint: 'Describe what needs documentation help: stale docs, missing index entries, new skill/agent docs, or runtime explanation drift.'
user-invocable: true
---

# Vision Documentation Operations

Use this skill when the task is to improve or repair the documentation layer for the Vision project.

## Core Files
- `DOCUMENTATION_INDEX.md` - top-level project documentation map
- `README.md` - overview and entry point for humans
- `setup.md` - install/start/troubleshooting guide
- `architecture.md` - runtime and protocol reference
- `.github/copilot-instructions.md` - always-on Copilot guidance
- `HIVE.md` - agent and customization overview
- `.github/skills/` and `.github/agents/` - reusable Copilot-facing documentation surfaces

## Documentation Rules
1. Prefer updating existing docs over creating redundant new files.
2. Keep runtime values, protocol names, and tool/MCP names aligned with the real code.
3. When a new skill or agent is added, update any files that enumerate available customizations.
4. When runtime behavior changes, update the nearest authoritative doc in the same change.

## Procedure
1. Read the doc entry points first.
   - `DOCUMENTATION_INDEX.md`
   - `README.md`
   - the most relevant technical doc (`setup.md`, `architecture.md`, or `.github/copilot-instructions.md`)
2. Check for drift against code or configuration.
3. Make the smallest coherent set of doc changes.
4. Verify that names, paths, and descriptions are consistent across docs.

## Completion Checks
- The docs describe the current system rather than an older version
- New or renamed skills/agents are discoverable
- The top-level documentation index points to the right places
