import {
  Agent,
  type ApproveFn,
  createBashTool,
  createFsTools,
  NodeFsProvider,
  NodeShellProvider,
} from "@openharness/core";
import {
  createLanguageModel,
  getVisionMcpServerConfig,
  loadRuntimeConfig,
} from "./runtime.js";

/**
 * Configuration options for creating a Vision-enabled agent.
 */
export interface VisionAgentConfig {
  /** Agent name (default: "vision-operator") */
  name?: string;
  /** Model to use for configured provider */
  model?: string;
  /** Vision base URL (default: http://localhost:8765) */
  visionBaseUrl?: string;
  /** Maximum steps per execution (default: 30) */
  maxSteps?: number;
  /** System prompt override */
  systemPrompt?: string;
  /** Enable tool approval callback */
  approve?: ApproveFn;
}

/**
 * Creates an Open Harness agent with Vision MCP tools.
 * 
 * The agent can control your computer through Vision's accessibility tools:
 * - Screen reading and OCR
 * - Mouse clicks and keyboard input
 * - Screenshot capture
 * - Application launching
 */
export async function createVisionAgent(
  config: VisionAgentConfig = {}
): Promise<Agent> {
  const runtime = loadRuntimeConfig();
  const {
    name = "vision-operator",
    model = runtime.model,
    visionBaseUrl = runtime.visionBaseUrl,
    maxSteps = runtime.maxSteps,
    systemPrompt,
    approve,
  } = config;

  const fsTools = createFsTools(new NodeFsProvider({ cwd: process.cwd() }));
  const bashTools = createBashTool(new NodeShellProvider({ cwd: process.cwd() }));

  const modelConfig = {
    ...runtime,
    model,
    visionBaseUrl,
    maxSteps,
  };

  const agent = new Agent({
    name,
    model: createLanguageModel(modelConfig),
    systemPrompt: systemPrompt || getDefaultSystemPrompt(),
    tools: {
      ...fsTools,
      ...bashTools,
    },
    maxSteps,
    approve,
    mcpServers: {
      vision: getVisionMcpServerConfig(modelConfig),
    },
  });

  return agent;
}

function getDefaultSystemPrompt(): string {
  return `You are Vision Operator, an AI assistant that helps users control their computer through accessibility tools.

You have access to the following capabilities via the Vision MCP server:
- Computer control: click, type, press keys, scroll, take screenshots
- Screen reading: OCR to read text from the screen
- System information: check health status, available models
- File operations: read, write, edit files (with local filesystem tools)
- Command execution: run shell commands (with bash tool)

When helping users:
1. Always confirm destructive actions before executing
2. Use screenshots and OCR to understand the current screen state
3. Explain what you're doing step by step
4. Handle errors gracefully and suggest alternatives

The user may have mobility limitations, so be patient and thorough in your assistance.`;
}
