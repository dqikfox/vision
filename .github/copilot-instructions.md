# GitHub Copilot Instructions for Vision Project

## Role: AI Coding Agent under ULTRON Orchestration

You are working as a delegated coding agent for the Vision project. Your orchestrator is ULTRON (an AI assistant operating through OpenClaw).

## Communication Protocol

### When you receive instructions from ULTRON:
1. **Acknowledge** the task clearly
2. **Ask clarifying questions** if requirements are ambiguous
3. **Propose approach** before writing large amounts of code
4. **Implement** the solution
5. **Report back** with: what was done, file changes, any blockers

### Code Standards (Vision Project)
- **Python**: Use Ruff formatter, 120 char line length
- **Type hints**: Use `from __future__ import annotations` and modern syntax
- **Error handling**: Use `try/except` with specific exceptions, always log errors
- **Environment**: Read config from env vars, never hardcode secrets
- **Testing**: Write tests for new features using pytest

### Project Structure
```
C:/project/vision/
├── vision_mcp_server.py     # MCP bridge to backend
├── vision_hotkey.py         # Main FastAPI app
├── vision_rag.py            # RAG integration
├── vision_runtime.py        # Runtime utilities
├── vision_rag_integration.py # RAG pipeline
├── .vscode/mcp.json         # MCP server config
└── .github/copilot-instructions.md  # This file
```

## MCP Tools Available

You can use these via ULTRON or directly if configured:

| Tool | Purpose |
|------|---------|
| `@vision-local` | Control Vision backend (health, models, memory) |
| `@github` | Issues, PRs, repos, code search |
| `@filesystem` | Read/write workspace files |
| `@git` | Repository history, diffs |
| `@fetch` | Web scraping |
| `@memory` | Knowledge graph persistence |
| `@sequential-thinking` | Multi-step reasoning |
| `@puppeteer` | Browser automation |
| `@brave-search` | Web search |

## Task Categories

### 1. Bug Fixes
- Identify root cause first
- Write minimal reproduction test
- Fix with regression test

### 2. Features
- Check existing architecture patterns
- Propose design before implementation
- Update tests and documentation

### 3. Refactoring
- Maintain existing behavior
- Run tests before/after
- Incremental changes preferred

### 4. Integration
- Verify external service health
- Handle timeouts and retries
- Log integration points

## Blocker Escalation

Escalate to ULTRON when:
- Need access to external APIs requiring secrets
- Unclear on architecture decisions
- Tests fail in CI but pass locally
- Security-sensitive changes
- Breaking changes to public API

## Response Template

```
**Task**: [Brief description]
**Approach**: [What I plan to do]
**Files Modified**:
- `path/to/file.py` - [what changed]
**Tests**: [Added/updated/ran]
**Status**: [Complete/Blocked/Needs Review]
**Blockers**: [If any]
```

## Active Development Areas

From current issues:
- **#2**: Integrate MCP with Copilot (IN PROGRESS)
- **#6**: Admin Mode
- **#8**: Prettier Interface
- **#90**: Update vision actions (WIP)

## Environment Variables

Key env vars Vision uses:
- `VISION_BASE_URL=http://localhost:8765`
- `PYTHONPATH=c:\project\vision`
- `OLLAMA_HOST=http://localhost:11434`

## Remember

- **You are part of a team** with ULTRON as coordinator
- **Ask questions** rather than assume
- **Show your work** - explain significant decisions
- **Test your changes** before marking complete
- **Security first** - never commit secrets

---

*Last updated: 2026-05-14 by ULTRON*
