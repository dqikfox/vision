#!/usr/bin/env node
/**
 * Subagent Demo - Multi-Agent System with Vision
 *
 * Demonstrates the subagent pattern where a parent agent delegates
 * tasks to specialized child agents.
 */
import { Agent, Session } from "@openharness/core";
import { checkVisionHealth } from "./preflight.js";
import {
  createLanguageModel,
  getVisionMcpServerConfig,
  loadRuntimeConfig,
} from "./runtime.js";
import { config } from "dotenv";

config({ path: ".env" });

async function main() {
  const runtime = loadRuntimeConfig();

  console.log("🦎 Vision Subagent Demo");
  console.log("=======================\n");
  console.log(`Provider: ${runtime.provider}`);
  console.log(`Model: ${runtime.model}`);
  console.log(`Vision: ${runtime.visionBaseUrl}\n`);

  const preflight = await checkVisionHealth(runtime.visionBaseUrl);
  if (preflight.ok) {
    console.log(`✅ Vision preflight OK (${preflight.status ?? "n/a"})\n`);
  } else {
    console.log(`⚠️  Vision preflight warning: ${preflight.message}\n`);
  }

  const model = createLanguageModel(runtime);
  const visionMcp = getVisionMcpServerConfig(runtime);

  // Create specialized subagents
  const explorerAgent = new Agent({
    name: "explorer",
    description: "Read-only codebase and screen exploration.",
    model,
    mcpServers: {
      vision: visionMcp,
    },
    maxSteps: 10,
  });

  const operatorAgent = new Agent({
    name: "operator",
    description: "Computer control via Vision.",
    model,
    mcpServers: {
      vision: visionMcp,
    },
    maxSteps: 15,
    approve: async ({ toolName }) =>
      runtime.autoApproveUnsafe ||
      toolName === "vision_vision_screenshot" ||
      toolName === "vision_vision_health",
  });

  const analystAgent = new Agent({
    name: "analyst",
    description: "Analyzes code, screens, and system state to provide insights and recommendations.",
    model,
    mcpServers: {
      vision: visionMcp,
    },
    maxSteps: 10,
  });

  // Create parent orchestrator agent with subagents
  const orchestrator = new Agent({
    name: "orchestrator",
    description: "Coordinates specialized subagents to accomplish complex tasks.",
    model,
    mcpServers: {
      vision: visionMcp,
    },
    subagents: [explorerAgent, operatorAgent, analystAgent],
    maxSteps: 25,
    systemPrompt: `You are the Vision Orchestrator, coordinating specialized subagents:

Available subagents:
1. @explorer - Read-only exploration of files and screen (screenshot, OCR, grep, list files)
2. @operator - Computer control (click, type, keys, scroll, run commands)
3. @analyst - Analysis and insights (code review, system health, recommendations)

When a task requires multiple capabilities, delegate to the appropriate subagent using the 'task' tool.
For example:
- "Find all TODOs in the codebase" → delegate to @explorer
- "Open Chrome and navigate to github.com" → delegate to @operator  
- "Is the system healthy?" → delegate to @analyst

Always report what subagents you used and what they accomplished.`,
  });

  // Create a session for multi-turn conversation
  const session = new Session({
    agent: orchestrator,
    contextWindow: runtime.contextWindow,
    retry: {
      maxRetries: 2,
      initialDelayMs: 300,
      maxDelayMs: 2000,
      backoffMultiplier: 2,
    },
  });

  // Demo tasks
  const tasks = [
    "Check the Vision system health and report status",
    "Explore the current directory structure",
    "What would you need to do to open Notepad and type 'Hello from Vision'?",
  ];

  for (const task of tasks) {
    console.log(`\n📝 Task: ${task}\n`);
    console.log("🤖 Orchestrator: ");

    let stepCount = 0;
    for await (const event of session.send(task)) {
      switch (event.type) {
        case "text.delta":
          process.stdout.write(event.text);
          break;
        case "tool.start":
          if (event.toolName === "task") {
            console.log(`\n📤 Delegating to subagent...`);
          } else {
            stepCount++;
            console.log(`\n🔧 [Step ${stepCount}] ${event.toolName}`);
          }
          break;
        case "step.done":
          console.log(`\n✅ Step complete`);
          break;
        case "done":
          console.log(`\n\n🎉 Task complete!`);
          break;
        case "error":
          console.error(`\n❌ Error: ${event.error.message}`);
          break;
      }
    }

    console.log("\n" + "=".repeat(50));
  }

  // Interactive mode for more tasks
  console.log("\n💬 Enter your own task (or 'exit'): ");
  process.stdin.on("data", async (data) => {
    const input = data.toString().trim();
    if (input.toLowerCase() === "exit") {
      process.exit(0);
    }

    console.log(`\n📝 Task: ${input}\n`);
    console.log("🤖 Orchestrator: ");

    for await (const event of session.send(input)) {
      if (event.type === "text.delta") {
        process.stdout.write(event.text);
      }
    }
    console.log("\n" + "=".repeat(50));
    console.log("\n💬 Enter another task (or 'exit'): ");
  });
}

main().catch(console.error);
