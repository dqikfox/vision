---
name: vision-tool-audit
description: 'Audit tool-calling behavior in the Vision operator. Use for checking direct tool execution, natural-language tool invocation, action broadcasts, and regressions in operator mode.'
argument-hint: 'Describe the tool path to audit: direct execute_tool, NL tool call, action feed, or browser automation.'
user-invocable: true
---

# Vision Tool Audit

Use this skill when reviewing or debugging operator mode and tool-call orchestration.

## Audit Focus
- Direct `execute_tool` requests over WebSocket
- Natural-language prompts that should trigger tool calls
- `action` and `screenshot` events sent back to the UI
- Separation between tool execution pass and final assistant response

## Procedure
1. Confirm expected protocol messages from `architecture.md`.
2. Reproduce the path with `test_tools.py` or the focused sections of `test_vision.py`.
3. Check whether the failure is in:
- Tool selection by the model
- Tool execution itself
- Action/result broadcast to the client
- Final assistant follow-up after tool execution

4. When reviewing a code change, prioritize these risks.
- Tool names or argument shapes drift from what the client sends
- Operator mode accidentally streams or replies before tool results are appended
- Browser UI no longer renders `action` or `screenshot` messages consistently

## Completion Checks
- Direct tool execution works for the audited path
- Natural-language trigger either works or has a clearly identified provider/model limitation
- UI receives the right event types and payload shape
