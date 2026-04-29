---
name: vision-cognitive-council
description: 'Use a structured cognitive council to gather multiple specialist viewpoints before broad, risky, or ambiguous work.'
argument-hint: 'Describe the decision or task that needs deeper reasoning: architecture choice, broad maintenance, risky change, or ambiguous goal.'
user-invocable: true
---

# Vision Cognitive Council

Use this skill when a task needs more than one line of reasoning. It builds on the context brain and forces several fresh perspectives before action.

## Core Files
- `hive_tools/context_mapper.py` - generates the shared context brain
- `.archon/artifacts/project_context.json` - latest generated context brain artifact
- `.archon/workflows/vision-cognitive-council.yaml` - deterministic council workflow
- `.github/copilot-instructions.md` - always-on guidance that should stay aligned with the council pattern

## Procedure
1. Generate or refresh the context brain.
   - Run `python hive_tools\context_mapper.py --output .archon\artifacts\project_context.json`

2. Gather multiple viewpoints.
   - Runtime/operator view: what could break or drift from Vision runtime behavior
   - Context/customization view: what should change in `.github/`, skills, workflows, or docs
   - Risk/reliability view: what validation or guardrails are needed
   - Automation/workflow view: what deterministic workflow or MCP surface should be reused

3. Synthesize one plan.
   - Resolve conflicts between viewpoints
   - Pick the smallest coherent path forward
   - Name the files, checks, and workflows that should be used next

## Completion Checks
- The task has at least three distinct viewpoints before implementation starts
- The final path names concrete files, workflows, or validation steps instead of staying abstract
- The chosen approach is better justified than a single-pass answer
