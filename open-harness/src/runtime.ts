import { createOpenAI } from "@ai-sdk/openai";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export type ModelProvider = "ollama" | "openai" | "openclaw" | "lmstudio";

export interface RuntimeConfig {
  provider: ModelProvider;
  model: string;
  modelFallbacks: string[];
  ollamaHost: string;
  ollamaPort: string;
  ollamaApiKey: string;
  providerBaseUrl?: string;
  providerApiKey?: string;
  openaiApiKey?: string;
  openclawBaseUrl: string;
  openclawApiKey?: string;
  lmStudioBaseUrl: string;
  lmStudioApiKey: string;
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

function normalizeBaseUrl(value: string, suffix = "/v1"): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  return trimmed.endsWith(suffix) ? trimmed : `${trimmed}${suffix}`;
}

function readOpenClawConfig(): { baseUrl?: string; token?: string } {
  const configPath = join(homedir(), ".openclaw", "openclaw.json");
  if (!existsSync(configPath)) return {};

  try {
    const config = JSON.parse(readFileSync(configPath, "utf8")) as {
      gateway?: {
        auth?: { token?: string };
        bind?: string;
        port?: number | string;
      };
      token?: string;
      api_key?: string;
      bearer_token?: string;
    };

    const token = config.gateway?.auth?.token || config.token || config.api_key || config.bearer_token;
    const port = config.gateway?.port || 18789;
    const bind = config.gateway?.bind;
    const host = !bind || bind === "loopback" ? "127.0.0.1" : bind;

    return {
      baseUrl: `http://${host}:${port}/v1`,
      token,
    };
  } catch {
    return {};
  }
}

function resolveProvider(rawProvider: string | undefined): ModelProvider {
  const normalized = (rawProvider || "ollama").toLowerCase().replace(/[-_ ]/g, "");
  if (normalized === "openai") return "openai";
  if (normalized === "openclaw") return "openclaw";
  if (normalized === "lmstudio") return "lmstudio";
  return "ollama";
}

export function loadRuntimeConfig(): RuntimeConfig {
  const provider = resolveProvider(process.env.MODEL_PROVIDER);
  const openClawConfig = readOpenClawConfig();
  const openclawBaseUrl = normalizeBaseUrl(
    process.env.OPENCLAW_BASE_URL ||
      process.env.OPENCLAW_GATEWAY_URL ||
      openClawConfig.baseUrl ||
      "http://127.0.0.1:18789/v1"
  );
  const openclawApiKey =
    process.env.OPENCLAW_API_KEY ||
    process.env.OPENCLAW_GATEWAY_TOKEN ||
    process.env.OPENCLAW_TOKEN ||
    openClawConfig.token;
  const lmStudioBaseUrl = normalizeBaseUrl(process.env.LMSTUDIO_BASE_URL || "http://127.0.0.1:1234/v1");
  const lmStudioApiKey = process.env.LMSTUDIO_API_KEY || "lm-studio";

  const providerDefaults: Record<ModelProvider, string> = {
    ollama: process.env.OLLAMA_MODEL || "kimi-k2.5:cloud",
    openai: process.env.OPENAI_MODEL || "gpt-4.1",
    openclaw: process.env.OPENCLAW_MODEL || "openclaw/default",
    lmstudio: process.env.LMSTUDIO_MODEL || "local-model",
  };

  const providerBaseUrl: Record<ModelProvider, string | undefined> = {
    ollama: `http://${process.env.OLLAMA_HOST || "127.0.0.1"}:${process.env.OLLAMA_PORT || "11434"}/v1`,
    openai: undefined,
    openclaw: openclawBaseUrl,
    lmstudio: lmStudioBaseUrl,
  };

  const providerApiKey: Record<ModelProvider, string | undefined> = {
    ollama: process.env.OLLAMA_API_KEY || "ollama",
    openai: process.env.OPENAI_API_KEY,
    openclaw: openclawApiKey,
    lmstudio: lmStudioApiKey,
  };

  return {
    provider,
    model:
      process.env.MODEL_NAME ||
      providerDefaults[provider],
    modelFallbacks: toList(process.env.MODEL_FALLBACKS),
    ollamaHost: process.env.OLLAMA_HOST || "127.0.0.1",
    ollamaPort: process.env.OLLAMA_PORT || "11434",
    ollamaApiKey: process.env.OLLAMA_API_KEY || "ollama",
    providerBaseUrl: providerBaseUrl[provider],
    providerApiKey: providerApiKey[provider],
    openaiApiKey: process.env.OPENAI_API_KEY,
    openclawBaseUrl,
    openclawApiKey,
    lmStudioBaseUrl,
    lmStudioApiKey,
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

  const openAiCompatible = createOpenAI({
    baseURL: config.providerBaseUrl,
    apiKey: config.providerApiKey,
    name: config.provider,
  });

  return openAiCompatible.chat(config.model);
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
