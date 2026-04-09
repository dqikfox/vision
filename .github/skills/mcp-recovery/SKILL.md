---
name: mcp-recovery
description: 'Inspect and restore MCP-related workspace setup safely. Use for checking whether VS Code or repo settings define MCP servers, verifying dependencies, and diagnosing why MCP-backed tooling is unavailable.'
argument-hint: 'Describe the MCP server or tool that is missing, broken, or expected to exist.'
user-invocable: true
---

# MCP Recovery

Use this skill when MCP-backed workflows are expected but missing or broken.

## Scope
- Inspect workspace settings and repo files for MCP-related configuration
- Verify whether a concrete MCP server definition exists
- Check whether required CLI/runtime dependencies are installed
- Distinguish between missing configuration and broken runtime

## Procedure
1. Search the repo for MCP configuration or references.
- `.vscode/settings.json`
- repo docs and setup files
- agent or skill files that mention MCP expectations

2. If no concrete server definition exists, stop assuming MCP is available.
- Report that the repo has no declared MCP server config
- Ask for the intended server package, transport, and credentials only if needed for the next step

3. If configuration exists, validate the runtime.
- Confirm required executable or package exists
- Check environment variables or auth references without printing secrets
- Capture exact startup/runtime errors

4. Prefer repair over reinvention.
- Restore broken dependencies first
- Avoid inventing new MCP server config unless the user explicitly requests a new one

## Completion Checks
- MCP expectation is mapped to an actual server definition, or absence is confirmed
- Missing dependency or config issue is identified concretely
- Next action is unambiguous: install, configure, or stop relying on MCP for this repo
