#!/usr/bin/env node
import { access } from "node:fs/promises";
import { constants } from "node:fs";
import { join } from "node:path";
import { config as loadDotenv } from "dotenv";
import { checkVisionHealth } from "./preflight.js";
import { loadRuntimeConfig } from "./runtime.js";

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
  } else {
    if (runtime.openaiApiKey && runtime.openaiApiKey.trim().length > 0) {
      results.push(ok("OpenAI key", "OPENAI_API_KEY is configured"));
    } else {
      results.push(fail("OpenAI key", "OPENAI_API_KEY is missing"));
    }
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
