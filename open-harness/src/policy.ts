import { readFile } from "node:fs/promises";

export interface PolicyFile {
  denyTools?: string[];
  allowTools?: string[];
  denyInputRegex?: string[];
  highRiskInputRegex?: string[];
}

export interface PolicyDecision {
  allowed: boolean;
  reason: string;
  risk: "LOW" | "MEDIUM" | "HIGH";
}

export class ToolPolicy {
  private denyTools = new Set<string>();
  private allowTools = new Set<string>();
  private denyRegex: RegExp[] = [];
  private highRiskRegex: RegExp[] = [];

  constructor(file?: PolicyFile) {
    if (!file) return;
    (file.denyTools || []).forEach((tool) => this.denyTools.add(tool));
    (file.allowTools || []).forEach((tool) => this.allowTools.add(tool));
    this.denyRegex = (file.denyInputRegex || []).map((item) => new RegExp(item, "i"));
    this.highRiskRegex = (file.highRiskInputRegex || []).map((item) => new RegExp(item, "i"));
  }

  static async load(filePath: string): Promise<ToolPolicy> {
    try {
      const raw = await readFile(filePath, "utf8");
      const parsed = JSON.parse(raw) as PolicyFile;
      return new ToolPolicy(parsed);
    } catch {
      return new ToolPolicy();
    }
  }

  evaluate(toolName: string, input: unknown): PolicyDecision {
    const serialized = JSON.stringify(input) || "";

    if (this.denyTools.has(toolName)) {
      return { allowed: false, reason: "Tool is denied by policy", risk: "HIGH" };
    }

    if (this.allowTools.size > 0 && !this.allowTools.has(toolName)) {
      return { allowed: false, reason: "Tool is not in allow list", risk: "HIGH" };
    }

    if (this.denyRegex.some((pattern) => pattern.test(serialized))) {
      return { allowed: false, reason: "Input matched deny regex", risk: "HIGH" };
    }

    if (
      toolName === "bash" ||
      toolName.includes("execute") ||
      this.highRiskRegex.some((pattern) => pattern.test(serialized))
    ) {
      return { allowed: true, reason: "Potentially destructive", risk: "HIGH" };
    }

    if (toolName.includes("write") || toolName.includes("delete") || toolName.includes("edit")) {
      return { allowed: true, reason: "State-changing tool", risk: "MEDIUM" };
    }

    return { allowed: true, reason: "Read-only/low-impact", risk: "LOW" };
  }
}
