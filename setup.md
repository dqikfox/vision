# Setup Guide

## 1. Python Dependencies

```bash
pip install fastapi uvicorn websockets sounddevice numpy scipy
pip install pyautogui pytesseract elevenlabs openai httpx pillow
```

Tesseract OCR (for read_screen tool):
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Install to default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Add to PATH or set in code: `pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`

## 2. Ollama (local models)

```bash
# Install: https://ollama.ai
ollama pull llama3.2      # 2GB — recommended, fast
ollama pull dolphin3      # 5GB — uncensored
ollama pull qwen2.5:14b   # 9GB — higher quality
ollama serve              # starts on port 11434
```

## 3. Environment Variables

Create `.env` or set in your shell / launch bat:

```
ELEVENLABS_API_KEY=sk_5f2c93b54654c98...   # Required for STT + TTS
OPENAI_API_KEY=sk-...                        # Optional: OpenAI provider
GITHUB_TOKEN=ghp_...                         # Optional: GitHub Copilot provider
```

## 4. Launch

```bash
cd C:\Users\msiul\.copilot
set ELEVENLABS_API_KEY=sk_...
python live_chat_app.py
```

Or double-click **Live Chat** on desktop.

## 5. First Run Checklist

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

**OpenAI/GitHub not working:**
- Enter API key in model picker → Save
- Or set environment variable before launching
