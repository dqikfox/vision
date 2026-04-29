# Setup Guide

## Option A: Vision Standalone (Local WebSocket)

### 1. Python Dependencies

```bash
pip install fastapi uvicorn websockets sounddevice numpy scipy
pip install pyautogui pytesseract elevenlabs openai httpx pillow
ollama --version  # Check Ollama is installed
```

Tesseract OCR (for read_screen tool):
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Install to default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Vision auto-detects common Windows install paths; if you use a custom location, add it to PATH or set `TESSERACT_CMD`

## 2. Ollama (local models)

```bash
# Install: https://ollama.ai
ollama pull qwen2.5:0.5b  # lightweight local model
ollama pull llama3.2:3b   # stronger local general model
ollama serve              # starts on port 11434
```

If your local Ollama store lives outside the default location, set `OLLAMA_MODELS` before starting the server.
Example used in this project:

```bash
set OLLAMA_MODELS=F:\models
```

## 3. Environment Variables

Create `.env` or set in your shell / launch bat:

```
ELEVENLABS_API_KEY=sk_5f2c93b54654c98...   # Required for STT + TTS
OPENAI_API_KEY=sk-...                        # Optional: OpenAI provider
GITHUB_TOKEN=ghp_...                         # Optional: GitHub Copilot provider
ANTHROPIC_API_KEY=sk-ant-...                 # Optional: Anthropic provider
DEEPSEEK_API_KEY=sk-...                      # Optional: DeepSeek provider
GROQ_API_KEY=gsk_...                         # Optional: Groq provider + fast Whisper fallback
MISTRAL_API_KEY=...                          # Optional: Mistral provider
GEMINI_API_KEY=...                           # Optional: Google Gemini provider
XAI_API_KEY=xai-...                          # Optional: xAI provider
```

## 4. Launch Vision

```bash
cd C:\project\vision
set ELEVENLABS_API_KEY=sk_...
set ELEVENLABS_WIDGET_AGENT_ID=agent_0701knwqnqy9e1aa3a3drdh30cva
python live_chat_app.py
```

Or double-click **Live Chat** on desktop.

Browser opens at `http://localhost:8765`.

### 4b. ElevenLabs widget-first voice setup

The UI includes an ElevenLabs widget in the **AGENT** panel for the fastest browser voice path.

Requirements:
- `ELEVENLABS_API_KEY` must be valid for syncing tools/prompt to ElevenLabs
- `ELEVENLABS_WIDGET_AGENT_ID` should point at your public widget agent
- That agent must have **authentication disabled** in ElevenLabs widget settings

Sync the live Vision tool set and operator prompt into the widget agent:

```bash
python setup_el_agent_tools.py
```

After launch:
1. Open `http://localhost:8765`
2. Open the **AGENT** panel
3. Click **SHOW / HIDE WIDGET**
4. Start talking to the ElevenLabs widget

The page injects a runtime operator prompt and registers Vision client tools so widget-triggered actions can execute through the local Vision backend.

---

## Option B: Vision with OpenClaw Gateway (Recommended)

OpenClaw provides a unified control plane for agents, channels (Slack, Teams, WhatsApp, etc.), and multi-agent orchestration.

### 1. Install OpenClaw (Node.js + CLI)

**Windows (PowerShell)**
```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

**macOS / Linux / WSL2**
```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

Verify:
```bash
node --version          # Should be 24+ or 22.14+
openclaw --version      # Should be 2026.4.9 or later
```

### 2. Configure OpenClaw (Interactive)

```bash
openclaw onboard --install-daemon
```

The wizard walks you through:
1. Model provider selection (Anthropic, OpenAI, Google, etc.)
2. API key configuration
3. Gateway settings (port 18789 is default)
4. Daemon/service install (Windows: Scheduled Task + Startup folder)

### 2b. Configure OpenClaw (Non-Interactive / Automation)

```bash
openclaw onboard --non-interactive --accept-risk --install-daemon
```

Note: Requires an API key env var to be pre-set (e.g., `OPENAI_API_KEY=sk-...`).

### 3. Verify Gateway is Running

```bash
openclaw gateway status
```

You should see:
```
Service: Scheduled Task (registered)
Listening: 127.0.0.1:18789
Dashboard: http://127.0.0.1:18789/
RPC probe: ok
```

### 4. Open OpenClaw Dashboard

```bash
openclaw dashboard
```

This opens the Control UI where you can:
- Chat with the configured agent
- Set up additional channels (Slack, Telegram, etc.)
- Configure tools and plugins

### 5. Launch Vision with OpenClaw Active

With the OpenClaw gateway running in the background, start Vision normally:

```bash
cd C:\project\vision
python live_chat_app.py
```

Vision will now:
- Integrate with OpenClaw's tool ecosystem
- Participate in multi-agent workflows
- Use OpenClaw's authentication and channel routing (if configured)

## Option A — First Run Checklist

- [ ] Microphone is set as default recording device
- [ ] Speakers/headphones connected (preferably headphones to avoid echo)
- [ ] Ollama is running (`ollama serve`)
- [ ] ELEVENLABS_API_KEY is set
- [ ] Browser opens at http://localhost:8765
- [ ] Green "connected" dot appears in top-right
- [ ] Orb turns blue ("Listening")
- [ ] Speak — orb should turn red ("Recording")
- [ ] Wait for purple ("Speaking") — AI responds

## 6. Troubleshooting

**No audio from AI:**
- Check ELEVENLABS_API_KEY is correct
- Check internet connection (ElevenLabs is cloud-based)
- Try slow internet mode: set TTS_MODEL = "eleven_flash_v2_5"
- If you switch TTS to `LOCAL`, Vision will prefer **Microsoft Ava** when it is installed on Windows

**ElevenLabs widget loads but tools do not fire:**
- Re-run `python setup_el_agent_tools.py`
- Verify `ELEVENLABS_API_KEY` is valid (`python test_keys.py`)
- Verify the widget agent is public and auth is disabled
- Verify `ELEVENLABS_WIDGET_AGENT_ID` points at the intended ElevenLabs agent

**AI doesn't hear me:**
- Lower RMS_THRESH in live_chat_app.py (try 150 or 100)
- Check mic is selected as default Windows recording device
- Run: `python -c "import sounddevice; print(sounddevice.query_devices())"`

**OCR not working (operator mode):**
- Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH

**Ollama models not showing:**
- Ensure Ollama is running: `ollama serve`
- Check: `curl http://localhost:11434/api/tags`
- Click ⟳ Refresh in model picker

## Option B — Troubleshooting OpenClaw

**Gateway won't start:**
```bash
openclaw doctor                        # Full diagnostics
openclaw gateway status --json         # JSON output for scripting
```

**Service installation issues (native Windows):**
- On native Windows, if Scheduled Task creation is blocked, OpenClaw falls back to a Startup-folder login item
- Check: `C:\Users\{username}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\OpenClaw Gateway.cmd`

**WSL2 + Windows combo issues:**
- For best stability, install and run OpenClaw inside WSL2
- See: `https://docs.openclaw.ai/platforms/windows` for WSL2 setup

**Use the `/openclaw-getting-started` Copilot skill** for guided setup.
