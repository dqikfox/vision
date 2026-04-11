---
name: vision-mcp-builder
description: 'Add or expand MCP capabilities for Vision by wiring repo-local servers, workspace config, and Copilot customizations together.'
argument-hint: 'Describe the MCP capability you want to add or repair: workspace config, vision-local bridge, skill wiring, or agent wiring.'
user-invocable: true
---

# Vision MCP Builder

Use this skill when the task is to make Copilot more capable in this repo by expanding MCP wiring, not just by editing application code.

## Core Files
- `.vscode/mcp.json` - workspace MCP server definitions for Copilot
- `vision_mcp_server.py` - repo-local FastMCP bridge for the running Vision backend
- `.github/agents/` - custom agents that should know how to use the MCP surface
- `.github/skills/` - on-demand workflows that explain how to use or extend MCP
- `.github/copilot-instructions.md` - always-on guidance that must stay consistent with the real setup

## Reference Pattern
Use `dqikfox/mcp` as the model:
1. Prefer a focused FastMCP bridge over duplicating backend logic.
2. Expose useful high-level tools that wrap existing HTTP or service APIs.
3. Register the server in workspace MCP config so agents can actually use it.
4. Keep skills and agent docs aligned with the real MCP entrypoints.

## Procedure
1. Audit the current MCP declarations.
- Check `.vscode/mcp.json`
- Check related docs and skills for drift
- Confirm the target runtime or endpoint really exists

2. Repair configuration drift before adding new surface area.
- Fix wrong URLs, commands, or server names
- Fill in missing but clearly expected servers such as `fetch`, `git`, or `sequential-thinking`

3. Add repo-local MCP capability when needed.
- Prefer a bridge that wraps existing Vision endpoints
- Keep tool names explicit and task-oriented
- Surface errors clearly instead of hiding backend failures

4. Expand the customization layer.
- Add or update skills that explain the new MCP flow
- Add or update custom agents when a reusable specialist role now exists
- Update `.github/copilot-instructions.md` and README entries that describe the MCP surface

## Completion Checks
- Workspace MCP config points at real servers
- Repo-local bridge code is present if the docs claim it exists
- Skill and agent docs match the actual MCP setup
- The new MCP surface can be imported or started without configuration surprises
