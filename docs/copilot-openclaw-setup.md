# Copilot + OpenClaw Setup

This workspace is configured to use the remote OpenClaw gateway as an OpenAI-compatible model source for GitHub Copilot Chat.

## Endpoints

- Copilot Chat / CLI base URL: `https://msi.tail886dbb.ts.net/v1`
- Model id: `openclaw/default`
- Token source: `%USERPROFILE%\.openclaw\openclaw.json`

## VS Code

1. Open `C:\project\vision` in VS Code.
2. Sign in to GitHub Copilot.
3. Open the chat model picker.
4. Select `OpenClaw Default` if it appears.

If the custom model does not appear in stable VS Code, use VS Code Insiders. The workspace already defines `github.copilot.chat.customOAIModels` in `.vscode/settings.json`.

## Important Limitation

Per current VS Code docs, BYOK/custom OpenAI-compatible models apply to Copilot Chat. They do not replace normal inline completions.

## VS Code Tasks

- `Vision: Verify OpenClaw API`
- `Vision: Copilot CLI via OpenClaw`
