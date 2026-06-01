import { mkdir, appendFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import type { SessionEvent } from "@openharness/core";

export interface TelemetryContext {
  sessionId: string;
  model: string;
  provider: string;
}

export class JsonlTelemetry {
  private readonly fullPath: string;
  private directoryReady: Promise<void> | null = null;
  private writeChain: Promise<void> = Promise.resolve();

  constructor(private readonly filePath: string, private readonly enabled: boolean) {
    this.fullPath = resolve(this.filePath);
  }

  private ensureDirectory(): Promise<void> {
    if (!this.directoryReady) {
      this.directoryReady = mkdir(dirname(this.fullPath), { recursive: true }).then(() => undefined);
    }
    return this.directoryReady;
  }

  private queueWrite(record: Record<string, unknown>) {
    if (!this.enabled) return;
    this.writeChain = this.writeChain
      .catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`⚠️ Prior telemetry write failed: ${message}`);
      })
      .then(async () => {
        await this.ensureDirectory();
        await appendFile(this.fullPath, `${JSON.stringify(record)}\n`, "utf8");
      })
      .catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`⚠️ Telemetry write failed: ${message}`);
      });
  }

  logEvent(event: SessionEvent, context: TelemetryContext): void {
    const base = {
      ts: new Date().toISOString(),
      sessionId: context.sessionId,
      model: context.model,
      provider: context.provider,
      type: event.type,
    };

    switch (event.type) {
      case "tool.start":
        this.queueWrite({ ...base, toolName: event.toolName, toolCallId: event.toolCallId });
        return;
      case "tool.done":
        this.queueWrite({ ...base, toolName: event.toolName, toolCallId: event.toolCallId });
        return;
      case "retry":
        this.queueWrite({ ...base, attempt: event.attempt, maxRetries: event.maxRetries, delayMs: event.delayMs });
        return;
      case "turn.done":
        this.queueWrite({
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
        this.queueWrite({ ...base, message: event.error.message });
        return;
      default:
        return;
    }
  }

  async flush(): Promise<void> {
    await this.writeChain;
  }
}
