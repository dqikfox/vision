import { createOpenAI } from "@ai-sdk/openai";

export type ModelProvider = "ollama" | "openai";

export interface RuntimeConfig {
  provider: ModelProvider;
  model: string;
  modelFallbacks: string[];
  ollamaHost: string;
  ollamaPort: string;
  ollamaApiKey: string;
  openaiApiKey?: string;
  visionBaseUrl: string;
  visionMcpScript: string;
  visionMcpPython: string;
  maxSteps: number;
  contextWindow: number;
  reservedTokens: number;
  autoApproveUnsafe: boolean;
  sessionPersist: boolean;
  sessionDir: string;
  sessionId: string;
  telemetryEnabled: boolean;
  telemetryPath: string;
  policyPath: string;
}

function toInt(value: string | undefined, fallback: number): number {
  if (!value) return fallback;
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function toBool(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  const normalized = value.trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes";
}

function toList(value: string | undefined): string[] {
  if (!value) return [];
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function loadRuntimeConfig(): RuntimeConfig {
  const providerEnv = (process.env.MODEL_PROVIDER || "ollama").toLowerCase();
  const provider: ModelProvider = providerEnv === "openai" ? "openai" : "ollama";

  return {
    provider,
    model:
      process.env.MODEL_NAME ||
      process.env.OLLAMA_MODEL ||
      process.env.OPENAI_MODEL ||
      "kimi-k2.5:cloud",
    modelFallbacks: toList(process.env.MODEL_FALLBACKS),
    ollamaHost: process.env.OLLAMA_HOST || "127.0.0.1",
    ollamaPort: process.env.OLLAMA_PORT || "11434",
    ollamaApiKey: process.env.OLLAMA_API_KEY || "ollama",
    openaiApiKey: process.env.OPENAI_API_KEY,
    visionBaseUrl: process.env.VISION_BASE_URL || "http://localhost:8765",
    visionMcpScript: process.env.VISION_MCP_SCRIPT || "..\\vision_mcp_server.py",
    visionMcpPython: process.env.VISION_MCP_PYTHON || "python",
    maxSteps: toInt(process.env.AGENT_MAX_STEPS, 30),
    contextWindow: toInt(process.env.AGENT_CONTEXT_WINDOW, 128000),
    reservedTokens: toInt(process.env.AGENT_RESERVED_TOKENS, 16000),
    autoApproveUnsafe: toBool(process.env.VISION_AUTO_APPROVE_UNSAFE, false),
    sessionPersist: toBool(process.env.SESSION_PERSIST, true),
    sessionDir: process.env.SESSION_DIR || ".sessions",
    sessionId: process.env.SESSION_ID || "default",
    telemetryEnabled: toBool(process.env.TELEMETRY_ENABLED, true),
    telemetryPath: process.env.TELEMETRY_PATH || ".logs/vision-agent.jsonl",
    policyPath: process.env.POLICY_PATH || ".openharness-policy.json",
  };
}

export function createLanguageModel(config: RuntimeConfig) {
  if (config.provider === "openai") {
    const openai = createOpenAI({
      apiKey: config.openaiApiKey,
      name: "openai",
    });
    return openai.chat(config.model);
  }

  const ollama = createOpenAI({
    baseURL: `http://${config.ollamaHost}:${config.ollamaPort}/v1`,
    apiKey: config.ollamaApiKey,
    name: "ollama",
  });

  return ollama.chat(config.model);
}

export function getVisionMcpServerConfig(config: RuntimeConfig) {
  return {
    type: "stdio" as const,
    command: config.visionMcpPython,
    args: [config.visionMcpScript],
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1",
      VISION_BASE_URL: config.visionBaseUrl,
    },
    cwd: process.cwd(),
  };
}
