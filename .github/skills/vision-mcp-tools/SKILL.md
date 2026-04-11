---
name: vision-mcp-tools
description: 'Master all active MCP servers available in this VSCode environment. Use when you need filesystem access, persistent memory, web fetch, search, browser automation, or sequential reasoning via MCP.'
argument-hint: 'Describe which MCP capability you need: filesystem, memory, fetch, search, puppeteer, or sequential-thinking.'
user-invocable: true
---

# Vision MCP Tools

Repo MCP servers are primarily configured in `.vscode/mcp.json`. User-level MCP config may add extra servers on top of that.

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

### git
Repository-aware git inspection through MCP.

### vision-local
Repo-local FastMCP bridge defined in `vision_mcp_server.py`.
It talks to the running Vision backend at `http://localhost:8765` and exposes:
```
vision_health()            → component health incl. anthropic_sdk, providers map
vision_models()            → all providers + current active model
vision_metrics()           → live CPU/RAM/GPU stats
vision_memory()            → full memory dump (facts, prefs, task_history)
vision_add_fact(fact)
vision_delete_fact(fact)
vision_set_model(provider, model)
vision_execute_tool(name, parameters?)
vision_voices()            → all SAPI + OneCore TTS voices
vision_screenshot()        → desktop screenshot as base64 JPEG
vision_wake_word(enabled)  → toggle wake-word activation mode
```
Use `vision_execute_tool()` for the full 70-tool Vision surface when the backend is running.

### lmstudio-rag
Filesystem access to the user's LM Studio RAG plugin workspace at `F:\rag-v1`.
Same tools as `filesystem` but scoped to that directory.
Use when the user asks about LM Studio plugins, RAG, prompt preprocessing, or local retrieval.
Read `manifest.json`, `src/`, and `.lmstudio/` before making assumptions about the plugin.

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
  → vision-local: vision_execute_tool("run_command", {"command": "ollama pull <model>"})
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

### Check which providers are configured
```
vision_health() → look at result.providers  # {openai: true, groq: false, xai: true, ...}
                → result.anthropic_sdk       # true if native SDK is installed
```
