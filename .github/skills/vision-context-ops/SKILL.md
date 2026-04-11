---
name: vision-context-ops
description: 'Improve Copilot itself in this repo by strengthening instructions, skills, memory workflow, and context-refresh behavior.'
argument-hint: 'Describe what makes Copilot feel under-informed: weak memory, poor repo awareness, context drift, or missing customization.'
user-invocable: true
---

# Vision Context Ops

Use this skill when the goal is to make **Copilot smarter in this repository**, not just to change application code.

## Core Files
- `.github/copilot-instructions.md` - always-on repo guidance
- `.github/agents/` - reusable specialist roles
- `.github/skills/` - on-demand workflows that teach Copilot how to work here
- `README.md` and `HIVE.md` - human-facing documentation for the customization layer
- Session `plan.md` and SQL todos - short-term working memory during multi-step work
- `RAG_PLUGIN_WORKSPACE` (env var) - configurable path to the user-owned LM Studio plugin workspace for local RAG/plugin context (example: `F:\rag-v1` on Windows, `/home/user/rag-v1` on Linux/macOS). If unset, use a documented fallback default per environment.

## What This Skill Optimizes
1. Repo awareness
   - Refresh the most important files before acting
   - Reduce drift between instructions, docs, and real runtime behavior

2. Context continuity
   - Keep plan/todo state current during long tasks
   - Add durable guidance for future sessions when it is genuinely reusable

3. Customization leverage
   - Add or refine skills and agents instead of overloading a single giant instruction file
   - Reuse existing MCP and memory surfaces when they already solve part of the problem

## Procedure
1. Audit the current context surfaces.
   - Read `.github/copilot-instructions.md`
   - Read relevant skill and agent docs
   - Read the current `plan.md` if the task spans multiple steps
   - Query SQL todos so active work is visible
   - If the task involves LM Studio or local retrieval, inspect `RAG_PLUGIN_WORKSPACE` before proposing changes

2. Decide whether the improvement belongs in:
   - always-on instructions
   - a reusable skill
   - a reusable agent
   - documentation for humans using Copilot here

3. Implement the smallest coherent customization set.
   - Prefer surgical instruction/skill/agent additions
   - Update docs that enumerate the available customizations
   - Avoid promising persistent memory behavior that is not actually wired up

4. Verify the customization layer.
   - Check names and paths are consistent
   - Confirm new skills/agents are listed anywhere the repo enumerates them
   - Keep instructions and docs aligned

## Completion Checks
- Copilot has a clearer repo-specific context workflow than before
- New skills or agents are documented consistently
- Always-on instructions reflect the improved context discipline

## Maintainer Decision Note
- Decide whether this skill should be multi-machine or single-environment. Multi-machine setups should require `RAG_PLUGIN_WORKSPACE` (with platform-aware fallback guidance), while single-environment setups may keep one fixed default path in docs.
