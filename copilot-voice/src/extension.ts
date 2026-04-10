import * as vscode from "vscode";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { ChildProcess, spawn } from "node:child_process";

const TRANSCRIBE_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions";
const TRANSCRIBE_MODEL = "whisper-large-v3-turbo";

type RecorderState = "idle" | "recording" | "processing";

class RecorderController {
  private process: ChildProcess | undefined;
  private outputPath: string | undefined;

  async start(): Promise<string> {
    const tempFile = path.join(os.tmpdir(), `copilot-voice-${Date.now()}.wav`);
    const { command, args } = this.buildRecordingCommand(tempFile);

    this.process = spawn(command, args, {
      stdio: ["pipe", "ignore", "pipe"],
      windowsHide: true,
    });

    this.outputPath = tempFile;

    await new Promise<void>((resolve, reject) => {
      if (!this.process) {
        reject(new Error("Recording process did not start."));
        return;
      }

      this.process.once("spawn", () => resolve());
      this.process.once("error", (error) => reject(error));
    });

    return tempFile;
  }

  async stop(): Promise<string> {
    if (!this.process || !this.outputPath) {
      throw new Error("Recording is not running.");
    }

    const proc = this.process;
    const filePath = this.outputPath;

    await new Promise<void>((resolve) => {
      const finish = () => resolve();

      proc.once("exit", () => finish());
      proc.once("close", () => finish());

      if (process.platform === "win32") {
        proc.stdin?.write("q\n");
        proc.stdin?.end();
        setTimeout(() => {
          if (!proc.killed) {
            proc.kill();
          }
        }, 800);
      } else {
        proc.kill("SIGINT");
      }
    });

    this.process = undefined;
    this.outputPath = undefined;

    return filePath;
  }

  private buildRecordingCommand(outputFile: string): { command: string; args: string[] } {
    if (process.platform === "win32") {
      return {
        command: "ffmpeg",
        args: ["-y", "-f", "dshow", "-i", "audio=default", "-ac", "1", "-ar", "16000", outputFile],
      };
    }

    return {
      command: "sox",
      args: ["-d", "-c", "1", "-r", "16000", outputFile],
    };
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const recorder = new RecorderController();
  let state: RecorderState = "idle";
  const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.command = "copilotVoice.toggleRecording";

  const renderState = () => {
    if (state === "recording") {
      statusBarItem.text = "$(vm-record) Recording… (press Ctrl+Shift+M to stop)";
      statusBarItem.tooltip = "Recording — click or press Ctrl+Shift+M to stop";
      statusBarItem.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
      return;
    }

    if (state === "processing") {
      statusBarItem.text = "$(sync~spin) Transcribing…";
      statusBarItem.tooltip = "Sending audio to Groq Whisper";
      statusBarItem.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
      return;
    }

    statusBarItem.text = "$(unmute) Copilot Voice";
    statusBarItem.tooltip = "Click or press Ctrl+Shift+M to start recording";
    statusBarItem.backgroundColor = undefined;
  };

  const setState = (next: RecorderState) => {
    state = next;
    renderState();
  };

  renderState();
  statusBarItem.show();

  const toggleDisposable = vscode.commands.registerCommand("copilotVoice.toggleRecording", async () => {
    try {
      if (state === "recording") {
        setState("processing");
        void vscode.window.showInformationMessage("$(sync~spin) Transcribing speech…");
        const audioPath = await recorder.stop();
        const text = await transcribeAudio(audioPath);
        await safeInsertIntoCopilotChat(text);
        await fs.unlink(audioPath).catch(() => undefined);
        setState("idle");
        void vscode.window.showInformationMessage(`$(check) Transcribed: "${text.slice(0, 80)}${text.length > 80 ? "…" : ""}"`);
        return;
      }

      if (state === "processing") {
        void vscode.window.showWarningMessage("Still transcribing previous recording, please wait.");
        return;
      }

      await recorder.start();
      setState("recording");
      void vscode.window.showInformationMessage("$(vm-record) Recording started — press Ctrl+Shift+M to stop.");
    } catch (error) {
      setState("idle");
      const message = error instanceof Error ? error.message : String(error);
      void vscode.window.showErrorMessage(`Copilot Voice error: ${message}`);
    }
  });

  context.subscriptions.push(statusBarItem, toggleDisposable);
}

export function deactivate(): void {
  // No-op.
}

async function transcribeAudio(audioPath: string): Promise<string> {
  const config = vscode.workspace.getConfiguration("copilotVoice");
  const apiKey = config.get<string>("groqApiKey", "").trim();
  const language = config.get<string>("language", "en").trim();

  if (!apiKey) {
    throw new Error("Set copilotVoice.groqApiKey in VS Code settings.");
  }

  const fileBuffer = await fs.readFile(audioPath);
  const formData = new FormData();
  formData.set("model", TRANSCRIBE_MODEL);
  formData.set("language", language);
  formData.set("response_format", "json");
  formData.set("file", new Blob([fileBuffer], { type: "audio/wav" }), path.basename(audioPath));

  const response = await fetch(TRANSCRIBE_ENDPOINT, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`Groq API request failed: ${response.status} ${details}`);
  }

  const payload = (await response.json()) as { text?: string };
  const text = (payload.text ?? "").trim();

  if (!text) {
    throw new Error("Transcription returned empty text.");
  }

  return text;
}

async function safeInsertIntoCopilotChat(text: string): Promise<void> {
  await vscode.commands.executeCommand("workbench.action.chat.open");

  const candidates = [
    { command: "workbench.action.chat.input.setText", argument: text },
    { command: "github.copilot.chat.setInput", argument: text },
  ];

  for (const candidate of candidates) {
    try {
      await vscode.commands.executeCommand(candidate.command, candidate.argument);
      return;
    } catch {
      // Try next command id.
    }
  }

  await vscode.env.clipboard.writeText(text);
  void vscode.window.showInformationMessage(
    "Transcribed text copied to clipboard. Paste into Copilot Chat input.",
  );
}
