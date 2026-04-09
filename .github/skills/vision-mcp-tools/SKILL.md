---
name: vision-mcp-tools
description: 'Master all active MCP servers available in this VSCode environment. Use when you need filesystem access, persistent memory, web fetch, search, browser automation, or sequential reasoning via MCP.'
argument-hint: 'Describe which MCP capability you need: filesystem, memory, fetch, search, puppeteer, or sequential-thinking.'
user-invocable: true
---

# Vision MCP Tools

All MCP servers are configured in `%APPDATA%\Code\User\mcp.json`.

## Active Servers & Capabilities

### filesystem
Read/write files in `C:\project`, Desktop, Documents.
```
list_directory(path)
read_file(path)
write_file(path, content)
create_directory(path)
move_file(src, dst)
search_files(path, pattern)
get_file_info(path)
```

### memory
Persistent knowledge graph — survives across sessions.
```
create_entities([{name, entityType, observations}])
create_relations([{from, to, relationType}])
add_observations([{entityName, contents}])
search_nodes(query)
open_nodes([names])
delete_entities([names])
```
Use this to remember user preferences, project facts, and task context permanently.

### sequential-thinking
Break complex problems into verified reasoning steps.
```
sequentialthinking(thought, nextThoughtNeeded, thoughtNumber, totalThoughts)
```
Use for: multi-step planning, debugging complex issues, architecture decisions.

### fetch
Retrieve any URL as markdown.
```
fetch(url, maxLength?, startIndex?)
```

### brave-search
Web search (requires `BRAVE_API_KEY` in mcp.json).
```
brave_web_search(query, count?)
brave_local_search(query, count?)
```

### puppeteer
Headless Chromium browser automation.
```
puppeteer_navigate(url)
puppeteer_screenshot(name, selector?, width?, height?)
puppeteer_click(selector)
puppeteer_fill(selector, value)
puppeteer_evaluate(script)
puppeteer_hover(selector)
puppeteer_select(selector, value)
```

### vision-local
Direct Vision tool execution via HTTP MCP at `http://localhost:8765/mcp`.
Exposes all 41 Vision tools as MCP tools — use when Vision server is running.

### github
GitHub Copilot MCP — search code, manage PRs, issues, repos.

### openclaw / openclaw-acp
OpenClaw agent orchestration and ACP session bridge.

## Power Patterns

### Remember a fact permanently
```
memory.create_entities([{"name": "UserPreference", "entityType": "preference", "observations": ["prefers dark mode", "uses Groq for STT"]}])
```

### Research + act
```
brave_web_search("latest ollama models 2025")
  → fetch(best_url)
  → vision-local: run_command("ollama pull <model>")
```

### Complex task planning
```
sequential-thinking: break "build a new Vision tool" into:
  1. Define schema
  2. Write handler
  3. Register in _EL_TOOL_NAMES
  4. Test via /api/tool/execute
  5. Verify in operator mode
```
