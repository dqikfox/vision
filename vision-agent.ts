/**
 * vision-agent.ts — OpenHarness agent wrapping Vision's 65+ tools
 *
 * Features from OpenHarness:
 *   - Session: auto-compaction + retry on transient errors
 *   - Subagents: specialist agents (coder, researcher, operator) with background execution
 *   - Skills: on-demand instruction packages loaded from .github/skills/
 *   - MCP: Vision's tool surface via localhost:8765/mcp
 *   - Reasoning: streams thinking tokens for o3/claude-3-7 models
 *
 * Usage:
 *   npx tsx vision-agent.ts "Take a screenshot and describe what you see"
 *   npx tsx vision-agent.ts --agent coder "Fix the flake8 errors in elite_tools.py"
 *   npx tsx vision-agent.ts --session "Continue the last task"
 */

import { Agent, Session, DefaultCompactionStrategy } from "@openharness/core";
import { openai } from "@ai-sdk/openai";
import { anthropic } from "@ai-sdk/anthropic";
import { tool } from "ai";
import { z } from "zod";
import * as fs from "fs";
import * as path from "path";

// ── Config ────────────────────────────────────────────────────────────────────

const VISION_BASE = process.env.VISION_BASE_URL ?? "http://localhost:8765";
const OPENAI_KEY  = process.env.OPENAI_API_KEY ?? "";
const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY ?? "";

// Pick best available model
const model = ANTHROPIC_KEY
  ? anthropic("claude-sonnet-4-5")   // best reasoning + tool use
  : openai("gpt-4.1");               // fallback

// ── Vision REST tool factory ──────────────────────────────────────────────────

function visionTool(name: string, description: string, schema: z.ZodObject<any>) {
  return tool({
    description,
    inputSchema: schema,
    execute: async (args) => {
      const res = await fetch(`${VISION_BASE}/api/tool/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, parameters: args }),
      });
      if (!res.ok) return `Error: ${res.status} ${res.statusText}`;
      const data = await res.json() as { result: string };
      return data.result ?? "(no result)";
    },
  });
}

// ── Tool definitions ──────────────────────────────────────────────────────────

const visionTools = {
  read_screen: visionTool("read_screen",
    "Take a full screenshot and OCR all visible text. Use before clicking to identify coordinates.",
    z.object({})),

  screenshot: visionTool("screenshot",
    "Take a screenshot without OCR.",
    z.object({})),

  screenshot_region: visionTool("screenshot_region",
    "Crop screenshot of a specific region for precise inspection.",
    z.object({
      x: z.number(), y: z.number(),
      width: z.number(), height: z.number(),
    })),

  click: visionTool("click",
    "Click at pixel coordinates.",
    z.object({ x: z.number(), y: z.number(), button: z.enum(["left","right","middle"]).optional() })),

  type_text: visionTool("type_text",
    "Type text at current keyboard focus.",
    z.object({ text: z.string() })),

  press_key: visionTool("press_key",
    "Press a key or shortcut e.g. 'ctrl+c', 'enter', 'win+r'.",
    z.object({ key: z.string() })),

  run_command: visionTool("run_command",
    "Run a Windows shell command and return output.",
    z.object({ command: z.string(), timeout: z.number().optional() })),

  read_file: visionTool("read_file",
    "Read file contents from disk.",
    z.object({ path: z.string(), encoding: z.string().optional() })),

  write_file: visionTool("write_file",
    "Write content to a file.",
    z.object({ path: z.string(), content: z.string() })),

  list_files: visionTool("list_files",
    "List files in a directory.",
    z.object({ path: z.string().optional(), pattern: z.string().optional() })),

  web_search: visionTool("web_search",
    "Search the web via DuckDuckGo.",
    z.object({ query: z.string(), max_results: z.number().optional() })),

  fetch_url: visionTool("fetch_url",
    "Fetch a URL and return content as markdown.",
    z.object({ url: z.string(), as_markdown: z.boolean().optional() })),

  browser_open: visionTool("browser_open",
    "Open a URL in the controlled Chromium browser.",
    z.object({ url: z.string() })),

  browser_extract: visionTool("browser_extract",
    "Extract text from the browser page.",
    z.object({ selector: z.string().optional() })),

  execute_python: visionTool("execute_python",
    "Execute Python code and return stdout. Full library access.",
    z.object({ code: z.string(), timeout: z.number().optional() })),

  get_system_info: visionTool("get_system_info",
    "Get CPU, RAM, disk, GPU usage and running processes.",
    z.object({})),

  remember: visionTool("remember",
    "Store a persistent fact in Vision's memory.",
    z.object({ fact: z.string() })),

  recall: visionTool("recall",
    "Search Vision's persistent memory.",
    z.object({ query: z.string().optional() })),

  wait: visionTool("wait",
    "Pause execution for N seconds.",
    z.object({ seconds: z.number() })),

  find_on_screen: visionTool("find_on_screen",
    "Find text on screen using OCR and return coordinates.",
    z.object({ text: z.string(), confidence: z.number().optional() })),

  send_notification: visionTool("send_notification",
    "Show a Windows desktop notification.",
    z.object({ title: z.string(), message: z.string() })),
};

// ── Specialist subagents ──────────────────────────────────────────────────────

const coderAgent = new Agent({
  name: "coder",
  description: "Expert Python/TypeScript developer. Reads files, writes code, runs tests, fixes bugs.",
  model,
  systemPrompt: `You are an elite Python developer working on the Vision project at C:\\project\\vision.
Rules:
- Line length 120 chars, formatter is Ruff not Black
- asyncio.get_running_loop() not get_event_loop()
- New Vision tools need 3 changes: TOOLS schema + exec_tool handler + _EL_TOOL_NAMES
- Always run python test_tools.py after changes
- broadcast() must use list(clients) snapshot`,
  tools: {
    read_file: visionTools.read_file,
    write_file: visionTools.write_file,
    list_files: visionTools.list_files,
    run_command: visionTools.run_command,
    execute_python: visionTools.execute_python,
  },
  maxSteps: 30,
});

const researcherAgent = new Agent({
  name: "researcher",
  description: "Web researcher. Searches the web, fetches URLs, summarises findings.",
  model,
  systemPrompt: "You are a technical research specialist. Find authoritative sources, extract key facts, and return concise summaries with citations.",
  tools: {
    web_search: visionTools.web_search,
    fetch_url: visionTools.fetch_url,
    remember: visionTools.remember,
  },
  maxSteps: 15,
});

const operatorAgent = new Agent({
  name: "operator",
  description: "Desktop operator. Controls the screen, clicks, types, runs commands, automates tasks.",
  model,
  systemPrompt: `You are a Windows desktop automation specialist.
- Always read_screen() first to see current state
- Use wait() after opening apps (let UI settle)
- Use find_on_screen() to locate elements reliably
- Confirm actions with screenshot() after each step`,
  tools: {
    read_screen: visionTools.read_screen,
    screenshot: visionTools.screenshot,
    screenshot_region: visionTools.screenshot_region,
    click: visionTools.click,
    type_text: visionTools.type_text,
    press_key: visionTools.press_key,
    run_command: visionTools.run_command,
    find_on_screen: visionTools.find_on_screen,
    wait: visionTools.wait,
    send_notification: visionTools.send_notification,
  },
  maxSteps: 40,
});

// ── Master agent ──────────────────────────────────────────────────────────────

const masterAgent = new Agent({
  name: "vision-master",
  description: "Master orchestrator for the Vision AI system. Routes tasks to specialist subagents.",
  model,
  systemPrompt: `You are VISION — an elite AI operator with full control of a Windows computer.

You have specialist subagents:
- coder: Python/TypeScript development, file editing, running tests
- researcher: web search, URL fetching, technical research  
- operator: desktop control, screenshots, clicking, automation

Rules:
1. ACT FIRST — never narrate before acting
2. Use subagents for complex tasks (delegate to coder for code, operator for desktop)
3. Run multiple subagents in parallel when tasks are independent
4. Store important facts with remember()
5. Check system health with get_system_info() when needed

Vision backend: http://localhost:8765
Project: C:\\project\\vision`,
  tools: {
    ...visionTools,
  },
  subagents: [coderAgent, researcherAgent, operatorAgent],
  maxSubagentDepth: 2,
  subagentBackground: {
    tools: { status: true, cancel: true, await: ["all", "allSettled", "any"] },
  },
  skills: {
    directories: [
      path.join(process.cwd(), ".github", "skills"),
    ],
  },
  mcpServers: {
    vision: {
      type: "http",
      url: `${VISION_BASE}/mcp`,
    },
  },
  maxSteps: 50,
});

// ── Session with compaction + retry ──────────────────────────────────────────

const SESSION_FILE = path.join(process.cwd(), ".brain", "openharness-session.json");

function loadSession(): any[] {
  try {
    if (fs.existsSync(SESSION_FILE)) {
      return JSON.parse(fs.readFileSync(SESSION_FILE, "utf-8"));
    }
  } catch {}
  return [];
}

function saveSession(messages: any[]) {
  fs.mkdirSync(path.dirname(SESSION_FILE), { recursive: true });
  fs.writeFileSync(SESSION_FILE, JSON.stringify(messages, null, 2));
}

const session = new Session({
  agent: masterAgent,
  contextWindow: 128_000,
  reservedTokens: 8_000,
  autoCompact: true,
  compactionStrategy: new DefaultCompactionStrategy({
    protectedTokens: 20_000,
    summaryPrompt: `Summarize this Vision AI session:
1. What the user was trying to accomplish
2. Key decisions made and why
3. Files changed or commands run
4. Current state and what's pending
5. Important facts discovered (API keys, paths, errors found)`,
  }),
  retry: {
    maxRetries: 3,
    initialDelayMs: 1000,
    maxDelayMs: 15_000,
  },
  hooks: {
    onAfterResponse: ({ turnNumber, usage }) => {
      if (usage.totalTokens) {
        process.stderr.write(`[turn ${turnNumber}] tokens: ${usage.totalTokens}\n`);
      }
      saveSession(session.messages);
    },
    onError: (error, attempt) => {
      process.stderr.write(`[retry ${attempt}] ${error.message}\n`);
    },
  },
});

// Restore previous session if --session flag
const args = process.argv.slice(2);
const resumeSession = args.includes("--session");
const agentFlag = args.indexOf("--agent");
const prompt = args.filter(a => !a.startsWith("--") && args[args.indexOf(a)-1] !== "--agent").join(" ");

if (resumeSession) {
  session.messages = loadSession();
  process.stderr.write(`[session] Restored ${session.messages.length} messages\n`);
}

// ── Run ───────────────────────────────────────────────────────────────────────

async function run() {
  if (!prompt) {
    console.error("Usage: npx tsx vision-agent.ts [--session] [--agent coder|researcher|operator] <prompt>");
    process.exit(1);
  }

  // Route to specific subagent if --agent flag
  let targetAgent: Agent = masterAgent;
  if (agentFlag !== -1) {
    const agentName = args[agentFlag + 1];
    const subagentMap: Record<string, Agent> = { coder: coderAgent, researcher: researcherAgent, operator: operatorAgent };
    targetAgent = subagentMap[agentName] ?? masterAgent;
    process.stderr.write(`[routing] Using ${targetAgent.name} agent\n`);
  }

  const runSession = targetAgent === masterAgent ? session : new Session({
    agent: targetAgent,
    contextWindow: 128_000,
    retry: { maxRetries: 3 },
  });

  process.stderr.write(`[vision-agent] ${targetAgent.name} — "${prompt.slice(0, 80)}"\n`);

  for await (const event of runSession.send(prompt)) {
    switch (event.type) {
      case "text.delta":
        process.stdout.write(event.text);
        break;
      case "reasoning.delta":
        process.stderr.write(`\x1b[2m${event.text}\x1b[0m`); // dim reasoning
        break;
      case "tool.start":
        process.stderr.write(`\n[tool] ${event.toolName}(${JSON.stringify(event.input).slice(0, 80)})\n`);
        break;
      case "tool.done":
        process.stderr.write(`[done] ${event.toolName}: ${String(event.output).slice(0, 100)}\n`);
        break;
      case "compaction.start":
        process.stderr.write(`\n[compaction] Context overflow — compacting...\n`);
        break;
      case "compaction.done":
        process.stderr.write(`[compaction] ${event.tokensBefore} → ${event.tokensAfter} tokens\n`);
        break;
      case "retry":
        process.stderr.write(`[retry] attempt ${event.attempt + 1}/${event.maxRetries + 1} in ${event.delayMs}ms\n`);
        break;
      case "done":
        process.stdout.write("\n");
        break;
    }
  }
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
