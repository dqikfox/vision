---
name: vision-web-research
description: 'Search the web, fetch URLs, and research topics to answer questions or complete operator tasks. Uses brave-search MCP and fetch MCP.'
argument-hint: 'Describe what to search for or which URL to fetch.'
user-invocable: true
---

# Vision Web Research

## Available MCP Tools
- `brave-search` → `brave_web_search(query, count)` — top N results with titles, URLs, snippets
- `fetch` → `fetch(url)` — full page content as markdown

## Procedure
1. Open-ended questions → `brave_web_search` with focused query (≤10 words)
2. Specific URL → `fetch` directly
3. Summarize in 2–4 sentences unless full content requested
4. For operator tasks ("find download link for X") → extract URL → `browser_open(url)`

## Fallback (no Brave key)
```
fetch("https://html.duckduckgo.com/html/?q=<url-encoded-query>")
```

## Integration with Vision Tools
```
brave_web_search("python asyncio tutorial") 
  → extract best URL 
  → browser_open(url) 
  → browser_extract() 
  → summarize to user via TTS
```

## Rules
- Prefer official sources (.gov, .org, vendor docs)
- Never fabricate results — only report what MCP returns
- If result contains a download link the user needs, pass it to `run_command("start <url>")` or `browser_open`
