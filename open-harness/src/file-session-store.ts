import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import type { ModelMessage } from "ai";
import type { SessionStore } from "@openharness/core";

interface PersistedSession {
  schemaVersion: 1;
  updatedAt: string;
  messages: ModelMessage[];
}

export class JsonFileSessionStore implements SessionStore {
  constructor(private readonly filePath: string) {}

  async load(_sessionId: string): Promise<ModelMessage[] | undefined> {
    try {
      const raw = await readFile(this.filePath, "utf8");
      const parsed = JSON.parse(raw) as PersistedSession;
      if (!Array.isArray(parsed.messages)) return undefined;
      return parsed.messages;
    } catch {
      return undefined;
    }
  }

  async save(_sessionId: string, messages: ModelMessage[]): Promise<void> {
    const fullPath = resolve(this.filePath);
    await mkdir(dirname(fullPath), { recursive: true });

    const payload: PersistedSession = {
      schemaVersion: 1,
      updatedAt: new Date().toISOString(),
      messages,
    };

    await writeFile(fullPath, `${JSON.stringify(payload)}\n`, "utf8");
  }
}
