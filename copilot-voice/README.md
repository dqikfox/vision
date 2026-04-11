# Copilot Voice Input 🎤

VSCode extension for voice input into GitHub Copilot Chat via the Groq Whisper API.

## Features

- Hotkey `Ctrl+Shift+Alt+V` (`Cmd+Shift+Alt+V` on macOS) — start / stop recording
- Transcribed text is inserted into the Copilot Chat input box — edit before sending
- Status-bar icon shows current state: `idle` / `recording` / `processing`
- Cross-platform: Windows, macOS, Linux

## Requirements

### Groq API key

1. Sign up at `https://console.groq.com`
2. Create an API key
3. Set it in VS Code settings: `copilotVoice.groqApiKey`

### Audio recording utility

- **Windows** — install [FFmpeg](https://ffmpeg.org/download.html) and add it to `PATH`
- **macOS** — install [SoX](https://sox.sourceforge.net/): `brew install sox`
- **Linux** — install SoX: `sudo apt install sox`

## Settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `copilotVoice.groqApiKey` | `string` | `""` | Groq API key for Whisper transcription |
| `copilotVoice.language` | `string` | `"en"` | Recognition language code (`en`, `ru`, etc.) |

## Usage

1. Press `Ctrl+Shift+Alt+V` or click the 🎤 icon in the status bar
2. Speak into your microphone
3. Press `Ctrl+Shift+Alt+V` again to stop
4. The transcribed text appears in the Copilot Chat input box
5. Edit if needed and press Enter to send

## Build from source

```bash
cd copilot-voice
npm install
npm run compile
```

Press `F5` in VS Code to launch the extension in debug mode.
