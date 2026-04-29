import { mkdir, appendFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import type { SessionEvent } from "@openharness/core";

export interface TelemetryContext {
  sessionId: string;
  model: string;
  provider: string;
}

export class JsonlTelemetry {
  constructor(private readonly filePath: string, private readonly enabled: boolean) {}

  private async write(record: Record<string, unknown>) {
    if (!this.enabled) return;
    const fullPath = resolve(this.filePath);
    await mkdir(dirname(fullPath), { recursive: true });
    await appendFile(fullPath, `${JSON.stringify(record)}\n`, "utf8");
  }

  async logEvent(event: SessionEvent, context: TelemetryContext): Promise<void> {
    const base = {
      ts: new Date().toISOString(),
      sessionId: context.sessionId,
      model: context.model,
      provider: context.provider,
      type: event.type,
    };

    switch (event.type) {
      case "tool.start":
        await this.write({ ...base, toolName: event.toolName, toolCallId: event.toolCallId });
        return;
      case "tool.done":
        await this.write({ ...base, toolName: event.toolName, toolCallId: event.toolCallId });
        return;
      case "retry":
        await this.write({ ...base, attempt: event.attempt, maxRetries: event.maxRetries, delayMs: event.delayMs });
        return;
      case "turn.done":
        await this.write({
          ...base,
          turnNumber: event.turnNumber,
          usage: {
            inputTokens: event.usage.inputTokens,
            outputTokens: event.usage.outputTokens,
            totalTokens: event.usage.totalTokens,
          },
        });
        return;
      case "error":
        await this.write({ ...base, message: event.error.message });
        return;
      default:
        await this.write(base);
    }
  }
}
