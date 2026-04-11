import * as vscode from "vscode";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { ChildProcess, spawn } from "node:child_process";

const TRANSCRIBE_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions";
const TRANSCRIBE_MODEL = "whisper-large-v3-turbo";

type RecorderState = "idle" | "recording" | "processing";

let activeRecorder: RecorderController | undefined;

class RecorderController {
  private process: ChildProcess | undefined;
  private outputPath: string | undefined;

  async start(): Promise<string> {
    const tempFile = path.join(os.tmpdir(), `copilot-voice-${Date.now()}.wav`);
    const candidates = this.buildRecordingCandidates(tempFile);

    let lastError: Error | undefined;
    for (const { command, args } of candidates) {
      try {
        this.process = spawn(command, args, {
          stdio: ["pipe", "ignore", "pipe"],
          windowsHide: true,
        });

        await new Promise<void>((resolve, reject) => {
          if (!this.process) {
            reject(new Error("Recording process did not start."));
            return;
          }

          let settled = false;

          const cleanup = () => {
            this.process?.off("spawn", onSpawn);
            this.process?.off("error", onError);
            this.process?.off("exit", onExit);
            this.process?.off("close", onClose);
          };

          const settleResolve = () => {
            if (settled) {
              return;
            }
            settled = true;
            cleanup();
            resolve();
          };

          const settleReject = (error: Error) => {
            if (settled) {
              return;
            }
            settled = true;
            cleanup();
            reject(error);
          };

          const onSpawn = () => settleResolve();
          const onError = (error: Error) => settleReject(error);
          const onExit = (code: number | null, signal: NodeJS.Signals | null) => {
            settleReject(new Error(`Recording process exited before spawn (code=${code}, signal=${signal ?? "none"}).`));
          };
          const onClose = (code: number | null, signal: NodeJS.Signals | null) => {
            settleReject(new Error(`Recording process closed before spawn (code=${code}, signal=${signal ?? "none"}).`));
          };

          this.process.once("spawn", onSpawn);
          this.process.once("error", onError);
          this.process.once("exit", onExit);
          this.process.once("close", onClose);
        });

        // Spawn succeeded
        this.outputPath = tempFile;
        return tempFile;
      } catch (err) {
        const e = err instanceof Error ? err : new Error(String(err));
        if ((e as NodeJS.ErrnoException).code === "ENOENT") {
          lastError = new Error(`'${command}' not found. ${this.installHint()}`);
          this.process = undefined;
          continue; // try next candidate
        }
        throw e;
      }
    }

    throw lastError ?? new Error("No audio recording tool found.");
  }

  async stop(): Promise<string | undefined> {
    if (!this.process || !this.outputPath) {
      return undefined;
    }

    const proc = this.process;
    const filePath = this.outputPath;

    await new Promise<void>((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) {
          return;
        }
        settled = true;
        resolve();
      };

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
        setTimeout(() => {
          if (!proc.killed) {
            proc.kill("SIGKILL");
          }
        }, 800);
      }
    });

    this.process = undefined;
    this.outputPath = undefined;

    return filePath;
  }

  private buildRecordingCandidates(outputFile: string): Array<{ command: string; args: string[] }> {
    const soxArgs = ["-d", "-c", "1", "-r", "16000", outputFile];
    if (process.platform === "win32") {
      return [
        // FFmpeg via DirectShow (requires ffmpeg in PATH)
        { command: "ffmpeg", args: ["-y", "-f", "dshow", "-i", "audio=default", "-ac", "1", "-ar", "16000", outputFile] },
        // SoX fallback (e.g. installed via Chocolatey or bundled with Audacity tools)
        { command: "sox", args: soxArgs },
      ];
    }
    return [{ command: "sox", args: soxArgs }];
  }

  private installHint(): string {
    if (process.platform === "win32") {
      return "Install FFmpeg (https://ffmpeg.org/download.html) or SoX (choco install sox.portable) and add to PATH.";
    }
    if (process.platform === "darwin") {
      return "Install SoX with: brew install sox";
    }
    return "Install SoX with: sudo apt install sox";
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const recorder = new RecorderController();
  activeRecorder = recorder;
  let state: RecorderState = "idle";
  let isHandlingToggle = false;
  const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.command = "copilotVoice.toggleRecording";

  const renderState = () => {
    if (state === "recording") {
      statusBarItem.text = "$(vm-record) Recording… (press Ctrl+Shift+Alt+V to stop)";
      statusBarItem.tooltip = "Recording — click or press Ctrl+Shift+Alt+V to stop";
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
    statusBarItem.tooltip = "Click or press Ctrl+Shift+Alt+V to start recording";
    statusBarItem.backgroundColor = undefined;
  };

  const setState = (next: RecorderState) => {
    state = next;
    renderState();
  };

  renderState();
  statusBarItem.show();

  const toggleDisposable = vscode.commands.registerCommand("copilotVoice.toggleRecording", async () => {
    if (isHandlingToggle) {
      void vscode.window.showInformationMessage("Copilot Voice is already handling a recording action.");
      return;
    }
    isHandlingToggle = true;
    try {
      if (state === "recording") {
        setState("processing");
        void vscode.window.showInformationMessage("$(sync~spin) Transcribing speech…");
        const audioPath = await recorder.stop();
        if (!audioPath) {
          throw new Error("Recording stopped before audio was captured.");
        }
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
      void vscode.window.showInformationMessage("$(vm-record) Recording started — press Ctrl+Shift+Alt+V to stop.");
    } catch (error) {
      setState("idle");
      const message = error instanceof Error ? error.message : String(error);
      void vscode.window.showErrorMessage(`Copilot Voice error: ${message}`);
    } finally {
      isHandlingToggle = false;
    }
  });

  context.subscriptions.push(statusBarItem, toggleDisposable);
}

export async function deactivate(): Promise<void> {
  if (!activeRecorder) {
    return;
  }
  await activeRecorder.stop();
  activeRecorder = undefined;
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

  const controller = new AbortController();
  const timeoutMs = 25000;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(TRANSCRIBE_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: formData,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Transcription timed out after 25 seconds. Please try again.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }

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
