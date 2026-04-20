#!/usr/bin/env node
/**
 * Vision Open Harness - CLI Agent
 *
 * A command-line agent that connects to Vision via MCP
 * and provides computer control capabilities.
 *
 * Usage:
 *   npm run start:vision-agent
 *
 * Or with custom prompt:
 *   npx tsx src/vision-agent.ts "Click on the Chrome icon"
 */
import { Session, type ApproveFn } from "@openharness/core";
import { createVisionAgent } from "./agent.js";
import { JsonFileSessionStore } from "./file-session-store.js";
import { checkVisionHealth } from "./preflight.js";
import { ToolPolicy } from "./policy.js";
import { loadRuntimeConfig } from "./runtime.js";
import { JsonlTelemetry } from "./telemetry.js";
import { join } from "node:path";
import * as readline from "readline";
import { config } from "dotenv";

// Load environment variables
config({ path: ".env" });

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const SAFE_TOOLS = new Set([
  "vision_vision_health",
  "vision_vision_models",
  "vision_vision_screenshot",
  "vision_vision_ocr",
  "readFile",
  "listFiles",
  "grep",
]);

type Runtime = ReturnType<typeof loadRuntimeConfig>;

const HIGH_RISK_PATTERNS = [
  /del(ete)?\b/i,
  /remove\b/i,
  /format\b/i,
  /shutdown\b/i,
  /reboot\b/i,
  /kill\b/i,
  /rm\s+-rf\b/i,
  /Set-ExecutionPolicy\b/i,
];

function truncateInput(input: unknown): string {
  const raw = JSON.stringify(input, null, 2) || "{}";
  return raw.length > 360 ? `${raw.slice(0, 360)}...` : raw;
}

function isHighRisk(toolName: string, input: unknown): boolean {
  if (toolName === "bash" || toolName.includes("execute")) return true;
  const serialized = JSON.stringify(input) || "";
  return HIGH_RISK_PATTERNS.some((pattern) => pattern.test(serialized));
}

function createApproveCallback(runtime: Runtime, policy: ToolPolicy): ApproveFn {
  return async ({ toolName, input }) => {
    if (SAFE_TOOLS.has(toolName)) return true;
    if (runtime.autoApproveUnsafe) return true;

    const decision = policy.evaluate(toolName, input);
    if (!decision.allowed) {
      console.log(`\n⛔ Policy denied ${toolName}: ${decision.reason}`);
      return false;
    }

    const risk = decision.risk === "LOW" ? (isHighRisk(toolName, input) ? "HIGH" : "MEDIUM") : decision.risk;
    return new Promise((resolve) => {
      rl.question(
        `\n⚠️  Approve ${toolName}?\n   Risk: ${risk}\n   Reason: ${decision.reason}\n   Input: ${truncateInput(input)}\n   (y/n): `,
        (answer) => resolve(answer.trim().toLowerCase().startsWith("y"))
      );
    });
  };
}

function shouldRetryError(error: Error): boolean {
  const msg = error.message.toLowerCase();
  if (msg.includes("prompt too long") || msg.includes("max context length")) return false;
  if (msg.includes("bad request")) return false;
  return true;
}

function createSession(
  agent: Awaited<ReturnType<typeof createVisionAgent>>,
  runtime: Runtime,
  sessionStore: JsonFileSessionStore | undefined
): Session {
  return new Session({
    agent,
    contextWindow: runtime.contextWindow,
    reservedTokens: runtime.reservedTokens,
    sessionId: runtime.sessionId,
    sessionStore,
    retry: {
      maxRetries: 2,
      initialDelayMs: 300,
      maxDelayMs: 2000,
      backoffMultiplier: 2,
      isRetryable: shouldRetryError,
    },
  });
}

async function main() {
  const runtime = loadRuntimeConfig();
  const policy = await ToolPolicy.load(runtime.policyPath);
  const telemetry = new JsonlTelemetry(runtime.telemetryPath, runtime.telemetryEnabled);

  console.log("🦎 Vision Open Harness Agent");
  console.log("============================\n");
  console.log(`Provider: ${runtime.provider}`);
  console.log(`Model: ${runtime.model}`);
  console.log(`Vision: ${runtime.visionBaseUrl}`);
  console.log(`Session: ${runtime.sessionId}`);
  console.log(`Telemetry: ${runtime.telemetryEnabled ? runtime.telemetryPath : "disabled"}\n`);

  const preflight = await checkVisionHealth(runtime.visionBaseUrl);
  if (preflight.ok) {
    console.log(`✅ Vision preflight OK (${preflight.status ?? "n/a"})`);
  } else {
    console.log(`⚠️  Vision preflight warning: ${preflight.message}`);
    console.log("   Continuing anyway so MCP diagnostics can run.\n");
  }

  // Get prompt from command line or interactive input
  const prompt = process.argv[2];

  // Create agent with approval callback for safety
  let agent = await createVisionAgent({
    name: "vision-cli",
    model: runtime.model,
    visionBaseUrl: runtime.visionBaseUrl,
    maxSteps: runtime.maxSteps,
    approve: createApproveCallback(runtime, policy),
  });

  const fallbackModels = [...runtime.modelFallbacks];

  const sessionStore = runtime.sessionPersist
    ? new JsonFileSessionStore(join(runtime.sessionDir, `${runtime.sessionId}.json`))
    : undefined;

  let session = createSession(agent, runtime, sessionStore);

  if (runtime.sessionPersist) {
    const loaded = await session.load();
    if (loaded) {
      console.log("💾 Loaded persisted session context.");
    }
  }

  if (prompt) {
    // Single-shot mode
    console.log(`\n📝 Task: ${prompt}\n`);
    await runSession(session, prompt, telemetry, runtime, async () => {
      const next = fallbackModels.shift();
      if (!next) return false;
      console.log(`\n🛟 Switching model fallback -> ${next}`);
      runtime.model = next;
      agent = await createVisionAgent({
        name: "vision-cli",
        model: next,
        visionBaseUrl: runtime.visionBaseUrl,
        maxSteps: runtime.maxSteps,
        approve: createApproveCallback(runtime, policy),
      });
      const oldMessages = session.messages;
      session = createSession(agent, runtime, sessionStore);
      session.messages = oldMessages;
      return true;
    });
    rl.close();
  } else {
    // Interactive mode
    console.log("\n💬 Interactive mode (type 'exit' to quit)\n");
    await interactiveMode(
      session,
      telemetry,
      runtime,
      async () => {
        const next = fallbackModels.shift();
        if (!next) return false;
        console.log(`\n🛟 Switching model fallback -> ${next}`);
        runtime.model = next;
        agent = await createVisionAgent({
          name: "vision-cli",
          model: next,
          visionBaseUrl: runtime.visionBaseUrl,
          maxSteps: runtime.maxSteps,
          approve: createApproveCallback(runtime, policy),
        });
        const oldMessages = session.messages;
        session = createSession(agent, runtime, sessionStore);
        session.messages = oldMessages;
        return true;
      }
    );
  }
}

async function runSession(
  session: Session,
  prompt: string,
  telemetry: JsonlTelemetry,
  runtime: Runtime,
  tryFallback: () => Promise<boolean>
) {
  let stepCount = 0;

  for await (const event of session.send(prompt)) {
    await telemetry.logEvent(event, {
      sessionId: runtime.sessionId,
      model: runtime.model,
      provider: runtime.provider,
    });

    switch (event.type) {
      case "turn.start":
        console.log(`\n🧠 Turn ${event.turnNumber} start`);
        break;
      case "text.delta":
        process.stdout.write(event.text);
        break;
      case "tool.start":
        stepCount++;
        console.log(`\n🔧 [Step ${stepCount}] Calling: ${event.toolName}`);
        break;
      case "tool.done":
        if (event.output !== undefined) {
          console.log(`   Result: ${String(event.output).substring(0, 100)}...`);
        }
        break;
      case "step.done":
        console.log(`\n✅ Step ${event.stepNumber} complete (${event.usage?.totalTokens || 0} tokens)`);
        break;
      case "retry":
        console.log(`\n🔁 Retry ${event.attempt}/${event.maxRetries} after ${event.delayMs}ms: ${event.error.message}`);
        break;
      case "turn.done":
        console.log(`\n📊 Turn ${event.turnNumber} usage: ${event.usage.totalTokens || 0} tokens`);
        break;
      case "done":
        console.log(`\n\n🎉 Done! Result: ${event.result}, Tokens: ${event.totalUsage?.totalTokens || 0}`);
        break;
      case "error":
        console.error(`\n❌ Error: ${event.error.message}`);
        if (/prompt too long|max context length/i.test(event.error.message)) {
          session.messages = [];
          console.log("🧹 Session context was reset after overflow. You can retry now.");
          return;
        }
        if (/internal server error|failed after/i.test(event.error.message)) {
          const switched = await tryFallback();
          if (switched) {
            console.log("🔁 Retrying prompt with fallback model...");
            await runSession(session, prompt, telemetry, runtime, tryFallback);
            return;
          }
        }
        break;
    }
  }

  if (runtime.sessionPersist) {
    await session.save();
  }
}

async function interactiveMode(
  session: Session,
  telemetry: JsonlTelemetry,
  runtime: Runtime,
  tryFallback: () => Promise<boolean>
) {
  const askQuestion = (): Promise<string> => {
    return new Promise((resolve) => {
      rl.question("\n👤 You: ", (answer) => resolve(answer));
    });
  };

  while (true) {
    const input = await askQuestion();
    if (input.toLowerCase() === "exit" || input.toLowerCase() === "quit") {
      console.log("\n👋 Goodbye!");
      rl.close();
      break;
    }

    console.log("\n🤖 Agent: ");
    await runSession(session, input, telemetry, runtime, tryFallback);
  }
}

main().catch(console.error);
