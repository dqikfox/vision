#!/usr/bin/env node
import { access } from "node:fs/promises";
import { constants } from "node:fs";
import { join } from "node:path";
import { config as loadDotenv } from "dotenv";
import { checkVisionHealth } from "./preflight.js";
import { loadRuntimeConfig, type RuntimeConfig } from "./runtime.js";

loadDotenv({ path: ".env" });

interface CheckResult {
  name: string;
  ok: boolean;
  details: string;
}

function ok(name: string, details: string): CheckResult {
  return { name, ok: true, details };
}

function fail(name: string, details: string): CheckResult {
  return { name, ok: false, details };
}

async function checkMcpScript(scriptPath: string): Promise<CheckResult> {
  const resolved = join(process.cwd(), scriptPath);
  try {
    await access(resolved, constants.F_OK);
    return ok("MCP script", `Found at ${resolved}`);
  } catch {
    return fail("MCP script", `Not found at ${resolved}`);
  }
}

async function fetchOllamaModels(host: string, port: string): Promise<{ base: string; names: string[]; error?: string }> {
  const base = `http://${host}:${port}`;

  try {
    const tagsRes = await fetch(`${base}/api/tags`);
    if (!tagsRes.ok) {
      return { base, names: [], error: `Endpoint ${base}/api/tags returned ${tagsRes.status}` };
    }

    const tagsJson = (await tagsRes.json()) as { models?: Array<{ name?: string }> };
    const names = (tagsJson.models || []).map((m) => m.name || "").filter(Boolean);

    return { base, names };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { base, names: [], error: `Connection failed: ${message}` };
  }
}

async function checkOllama(host: string, port: string, model: string): Promise<CheckResult> {
  const { base, names, error } = await fetchOllamaModels(host, port);

  if (error) {
    return fail("Ollama", error);
  }

  if (names.length === 0) {
    return fail("Ollama", `Connected to ${base}, but no models are installed`);
  }

  if (!names.includes(model)) {
    return fail(
      "Ollama model",
      `Model '${model}' not found. Available: ${names.slice(0, 10).join(", ")}${names.length > 10 ? ", ..." : ""}`
    );
  }

  return ok("Ollama", `Connected to ${base}; model '${model}' is available`);
}

async function fetchOpenAiCompatibleModels(
  baseUrl: string,
  apiKey: string | undefined
): Promise<{ names: string[]; status?: number; error?: string }> {
  const headers: Record<string, string> = {};
  if (apiKey && apiKey.trim().length > 0) {
    headers.Authorization = `Bearer ${apiKey}`;
  }

  try {
    const modelsRes = await fetch(`${baseUrl.replace(/\/$/, "")}/models`, { headers });
    if (!modelsRes.ok) {
      return { names: [], status: modelsRes.status, error: `Endpoint returned ${modelsRes.status}` };
    }

    const modelsJson = (await modelsRes.json()) as { data?: Array<{ id?: string; name?: string }> };
    const names = (modelsJson.data || [])
      .map((model) => model.id || model.name || "")
      .filter(Boolean);

    return { names, status: modelsRes.status };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { names: [], error: `Connection failed: ${message}` };
  }
}

async function checkOpenAiCompatibleProvider(runtime: RuntimeConfig): Promise<CheckResult[]> {
  const providerLabel = runtime.provider === "lmstudio" ? "LM Studio" : "OpenClaw";
  const baseUrl = runtime.providerBaseUrl || "";
  const apiKey = runtime.providerApiKey;
  const results: CheckResult[] = [];

  if (!baseUrl) {
    return [fail(providerLabel, "Provider base URL is not configured")];
  }

  if (runtime.provider === "openclaw" && (!apiKey || apiKey.trim().length === 0)) {
    results.push(fail("OpenClaw token", "No OPENCLAW_GATEWAY_TOKEN/OPENCLAW_API_KEY or ~/.openclaw token found"));
  }

  const { names, status, error } = await fetchOpenAiCompatibleModels(baseUrl, apiKey);
  if (error) {
    results.push(fail(providerLabel, `${baseUrl}/models failed: ${error}`));
    return results;
  }

  if (names.length === 0) {
    results.push(fail(providerLabel, `${baseUrl}/models returned ${status ?? "ok"} but no model ids`));
    return results;
  }

  const modelFound = names.includes(runtime.model);
  if (!modelFound) {
    results.push(
      fail(
        `${providerLabel} model`,
        `Model '${runtime.model}' not found. Available: ${names.slice(0, 10).join(", ")}${names.length > 10 ? ", ..." : ""}`
      )
    );
  } else {
    results.push(ok(providerLabel, `Connected to ${baseUrl}; model '${runtime.model}' is available`));
  }

  if (runtime.modelFallbacks.length > 0) {
    const missing = runtime.modelFallbacks.filter((model) => !names.includes(model));
    if (missing.length > 0) {
      results.push(fail("Fallback models", `Missing: ${missing.join(", ")}`));
    } else {
      results.push(ok("Fallback models", `${runtime.modelFallbacks.length} fallback model(s) available`));
    }
  }

  return results;
}

function printResults(results: CheckResult[]): boolean {
  console.log("\n🩺 Vision Open Harness Health Check\n");

  for (const result of results) {
    const icon = result.ok ? "✅" : "❌";
    console.log(`${icon} ${result.name}: ${result.details}`);
  }

  const allOk = results.every((r) => r.ok);
  console.log("");
  if (allOk) {
    console.log("🎉 All checks passed.");
  } else {
    console.log("⚠️ One or more checks failed. Fix the failures above and rerun `npm run health`.");
  }

  return allOk;
}

async function main() {
  const runtime = loadRuntimeConfig();
  const results: CheckResult[] = [];

  results.push(ok("Provider", `${runtime.provider} (${runtime.model})`));
  results.push(await checkMcpScript(runtime.visionMcpScript));

  const vision = await checkVisionHealth(runtime.visionBaseUrl);
  if (vision.ok) {
    results.push(ok("Vision API", `${runtime.visionBaseUrl}/api/health reachable (${vision.status})`));
  } else {
    results.push(fail("Vision API", vision.message));
  }

  if (runtime.provider === "ollama") {
    results.push(await checkOllama(runtime.ollamaHost, runtime.ollamaPort, runtime.model));
    if (runtime.modelFallbacks.length > 0) {
      const { names } = await fetchOllamaModels(runtime.ollamaHost, runtime.ollamaPort);
      const missing = runtime.modelFallbacks.filter((m) => !names.includes(m));
      if (missing.length > 0) {
        results.push(fail("Fallback models", `Missing: ${missing.join(", ")}`));
      } else {
        results.push(ok("Fallback models", `${runtime.modelFallbacks.length} fallback model(s) available`));
      }
    }
  } else if (runtime.provider === "openai") {
    if (runtime.openaiApiKey && runtime.openaiApiKey.trim().length > 0) {
      results.push(ok("OpenAI key", "OPENAI_API_KEY is configured"));
    } else {
      results.push(fail("OpenAI key", "OPENAI_API_KEY is missing"));
    }
  } else {
    results.push(...(await checkOpenAiCompatibleProvider(runtime)));
  }

  try {
    const ragStatusRes = await fetch(`${runtime.visionBaseUrl.replace(/\/$/, "")}/api/rag/status`);
    if (ragStatusRes.ok) {
      const ragStatus = (await ragStatusRes.json()) as { indexed?: boolean; source_root?: string; chunks_indexed?: number };
      if (ragStatus.indexed) {
        results.push(
          ok(
            "Vision RAG",
            `Indexed (${ragStatus.chunks_indexed || 0} chunks) from ${ragStatus.source_root || "unknown source"}`
          )
        );
      } else {
        results.push(fail("Vision RAG", "RAG index not built yet (run kb_index or POST /api/rag/index)"));
      }
    } else {
      results.push(fail("Vision RAG", `/api/rag/status returned ${ragStatusRes.status}`));
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    results.push(fail("Vision RAG", `Failed to query /api/rag/status: ${message}`));
  }

  const success = printResults(results);
  process.exitCode = success ? 0 : 1;
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`❌ Health check failed: ${message}`);
  process.exitCode = 1;
});
