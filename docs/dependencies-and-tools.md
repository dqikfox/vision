# Vision Dependencies and Tools

This document records the dependencies, external tools, local services, and configuration notes needed to run or extend the Vision workspace.

## Runtime Requirements

| Tool | Version requirement | Purpose | Configuration notes |
| --- | ---: | --- | --- |
| Windows | Windows 11 recommended | Primary supported operating system for desktop control, launcher scripts, OCR, audio, and PowerShell automation. | Most launcher paths and helper scripts assume native Windows paths. |
| Python | `>=3.11` from `pyproject.toml`; workspace settings currently point at Python 3.14 | Runs the FastAPI backend, voice/audio pipeline, computer-control tools, MCP bridge, tests, and helper scripts. | `.vscode/settings.json` currently pins `python.defaultInterpreterPath` to `C:\Users\CHANN0$\AppData\Local\Python\pythoncore-3.14-64\python.exe`. |
| Node.js | `24+` or `22.14+` for OpenClaw; `>=22.0.0` for `open-harness` | Runs OpenClaw, MCP servers launched through `npx`, OpenHarness integrations, and TypeScript helper projects. | Keep Node on PATH for `npx`, OpenClaw, MCP server startup, and package scripts. |
| PowerShell | PowerShell 7 preferred; Windows PowerShell works for many tasks | Runs launchers, OpenClaw helpers, VS Code tasks, and desktop shortcuts. | Launcher scripts commonly use `-NoProfile -ExecutionPolicy Bypass`. |
| Ollama | Current Ollama CLI/server | Local model provider for Vision and OpenClaw workflows. | Default port is `11434`. `vision_command_center_config.json` currently uses `127.0.0.1:11434`, localhost-only origins, and `F:\models` as the model store. |
| Tesseract OCR | Current UB Mannheim Windows build | Enables `read_screen` and OCR-based operator workflows through `pytesseract`. | Install to `C:\Program Files\Tesseract-OCR\tesseract.exe`, add to PATH, or set `TESSERACT_CMD`. |
| OpenClaw | `2026.4.9` or later per setup docs | Gateway and control plane for OpenAI-compatible model routing, agent workflows, and Copilot integration. | Gateway default port is `18789`; token is read from `%USERPROFILE%\.openclaw\openclaw.json`. |
| GitHub Copilot CLI | Installed and on PATH when using Copilot through OpenClaw | Lets `scripts\copilot-openclaw.ps1` launch Copilot CLI against the OpenClaw gateway. | The helper exports `COPILOT_PROVIDER_TYPE`, `COPILOT_PROVIDER_BASE_URL`, `COPILOT_PROVIDER_API_KEY`, and `COPILOT_MODEL`. |
| Git | Current Git for Windows | Repository history, MCP git server, and development workflow. | `.vscode/mcp.json` defines a git MCP server through `npx @modelcontextprotocol/server-git`. |
| Docker Desktop | Current Docker Compose v2 | Optional containerized Archon stack and PostgreSQL/Caddy profiles. | Used by `Archon\docker-compose.yml`; optional profiles include `with-db`, `cloud`, and `auth`. |
| .NET SDK | Current SDK that can build SQL projects | Builds the `sql` and `abc` SQL project tasks from VS Code. | `.vscode/tasks.json` calls `dotnet build` for `sql\sql.sqlproj` and `abc\abc.sqlproj`. |
| Browser | Edge or Chrome preferred | Hosts the Vision UI, Command Center, Playwright automation, and ElevenLabs widget. | `launch_vision.ps1` prefers app-window mode for Edge or Chrome when opening `http://localhost:8765`. |

## Python Dependencies

The top-level Python project is declared as `vision-accessibility-operator` in `pyproject.toml`.

| Package | Version requirement | Purpose | Notes |
| --- | ---: | --- | --- |
| `fastapi` | `>=0.115` in `requirements.txt`; `>=0.104` in `pyproject.toml` | HTTP API, WebSocket backend, Command Center endpoints. | Prefer the stricter `requirements.txt` floor for current installs. |
| `uvicorn` | `>=0.30` in `requirements.txt`; `>=0.24` in `pyproject.toml` | ASGI server for `live_chat_app:app`. | `launch_vision.ps1` starts it on port `8765`. |
| `websockets` | `>=12.0` | Real-time UI and voice/operator communication. | Used by the local web UI and command routing. |
| `httpx` | `>=0.27.0` in `requirements.txt`; `>=0.25` in `pyproject.toml` | Async HTTP client for providers and local services. | Used for model/provider and gateway calls. |
| `numpy` | `>=1.26` in `requirements.txt`; `>=1.24` in `pyproject.toml` | Audio processing and numeric helpers. | Paired with `scipy` and `sounddevice`. |
| `scipy` | `>=1.12` in `requirements.txt`; `>=1.11` in `pyproject.toml` | Audio signal processing. | Required for voice features. |
| `sounddevice` | `>=0.4.7` in `requirements.txt`; `>=0.4` in `pyproject.toml` | Microphone and speaker device access. | Windows audio devices must be available and configured. |
| `pyautogui` | `>=0.9.54` in `requirements.txt`; `>=0.9` in `pyproject.toml` | Desktop control: mouse, keyboard, and screen automation. | Windows permissions and display state can affect automation. |
| `pytesseract` | `>=0.3.10` in `requirements.txt`; `>=0.3` in `pyproject.toml` | Python wrapper for Tesseract OCR. | Requires native Tesseract installed separately. |
| `pygetwindow` | `>=0.0.9` | Window discovery and targeting. | Listed in `requirements.txt`. |
| `pillow` | `>=10.0` in `requirements.txt`; `>=10` in `pyproject.toml` | Image capture and processing. | Used by OCR and UI/image tooling. |
| `openai` | `>=1.50.0` in `requirements.txt`; `>=2.30` in `pyproject.toml` | OpenAI-compatible provider integration. | Version drift exists; test provider behavior when changing this dependency. |
| `anthropic` | `>=0.50.0` in `requirements.txt`; `>=0.25` in `pyproject.toml` | Anthropic provider integration. | Requires `ANTHROPIC_API_KEY`. |
| `ollama` | `>=0.3.0` in `requirements.txt`; `>=0.1` in `pyproject.toml` | Python client for local Ollama models. | Requires Ollama server running. |
| `elevenlabs` | `>=2.0.0` in `requirements.txt`; `>=2.42` in `pyproject.toml` | Cloud voice, TTS, and ElevenLabs widget/tool sync. | Requires `ELEVENLABS_API_KEY`; widget mode also uses `ELEVENLABS_WIDGET_AGENT_ID`. |
| `huggingface_hub` | `>=0.24.0` | Optional model and artifact access. | Listed in `requirements.txt`. |
| `mcp[cli]` | `>=1.0.0` | Model Context Protocol server/client tooling. | Used by `vision_mcp_server.py` and local MCP workflows. |
| `ddgs` | `>=6.0` | Web/search helper dependency. | Listed in `requirements.txt`. |
| `markdownify` | `>=0.11.6` | Converts fetched HTML into Markdown. | Useful for web research and fetch workflows. |
| `pyperclip` | `>=1.8.2` | Clipboard integration. | Used by desktop/operator workflows. |
| `keyring` | `>=25.0` | Secure-ish local credential access where supported. | Do not commit secrets stored or retrieved through this package. |
| `keyboard` | `>=0.13.5` | Hotkeys and keyboard event helpers. | May require elevated permissions for some global hooks. |
| `psutil` | `>=5.9.8` in `requirements.txt`; `>=5.9` in `pyproject.toml` | Process and system monitoring. | Used by launch/doctor/runtime health features. |
| `nvidia-ml-py` / `pynvml` | `>=12.560.30` in `requirements.txt`; `pynvml>=12.5` in `pyproject.toml` | NVIDIA GPU telemetry. | Requires NVIDIA driver/NVML support. |
| `plyer` | `>=2.1.0` | Desktop notifications and platform helpers. | Listed in `requirements.txt`. |
| `playwright` | `>=1.44.0` | Browser automation. | Install browser binaries separately with `python -m playwright install` when needed. |
| `pywin32` | `>=306` | Windows API integration. | Windows-only dependency. |
| `pyttsx3` | `>=2.90` | Local text-to-speech fallback. | Useful when cloud TTS is unavailable. |

Optional Python dependencies documented in `requirements.txt`:

| Package | Purpose | Notes |
| --- | --- | --- |
| `faster-whisper>=1.0.0` | Local Whisper speech-to-text fallback. | Commented out by default. |
| `ctranslate2>=3.20.0` | GPU-accelerated Whisper runtime. | Commented out by default. |

## Python Development Tools

| Tool | Version requirement | Purpose | Configuration notes |
| --- | ---: | --- | --- |
| `pytest` | `>=7.4` | Test runner. | Configured in `pyproject.toml`; default test path is the repo root. |
| `pytest-asyncio` | `>=0.21` | Async test support. | `asyncio_mode = "auto"`. |
| `pytest-cov` | `>=4.1` | Coverage reporting. | Coverage targets include `live_chat_app`; HTML output goes to `htmlcov`. |
| `ruff` | `>=0.4` in dev deps; pre-commit uses `v0.9.1` | Linting and formatting. | `line-length = 120`, `target-version = "py311"`. |
| `pyright` | `>=1.1` | Type checking. | VS Code uses Pylance/Pyright in basic mode. |
| `mypy` | External tool configured in VS Code and `pyproject.toml` | Strict type checking. | `pyproject.toml` has strict settings, but VS Code passes `--ignore-missing-imports --no-strict-optional`. |
| `pylint` | External tool configured in VS Code | Additional Python linting. | Project disables selected warnings in `pyproject.toml`; VS Code passes extra disables. |
| `flake8` | External tool configured in VS Code | Legacy lint checks. | Uses `.flake8`. |
| `black` | Configured in `pyproject.toml` | Formatter reference for compatible tools. | `line-length = 100`, `target-version = py311`. |
| `isort` | Configured in `pyproject.toml` | Import sorting. | Uses Black profile and line length `100`. |
| `bandit` | `>=1.7` in dev deps | Security linting. | Excludes tests and skips selected rules. |
| `pre-commit` | Current; hooks pinned in `.pre-commit-config.yaml` | Runs formatting and hygiene checks before commits. | Hooks include Ruff, trailing whitespace, EOF fixer, YAML check, merge-conflict check, and private-key detection. |

## JavaScript and TypeScript Dependencies

### Top-level package

| Package | Version requirement | Purpose | Notes |
| --- | ---: | --- | --- |
| `@ai-sdk/anthropic` | `^3.0.71` | Anthropic provider support for AI SDK workflows. | Top-level `package.json`. |
| `@ai-sdk/openai` | `^3.0.53` | OpenAI-compatible provider support. | Used by OpenHarness-style integrations. |
| `@openharness/core` | `^0.6.2` | Agent harness integration. | Also used by `open-harness`. |
| `ai` | `^6.0.168` | Vercel AI SDK core utilities. | Top-level and nested harness dependency. |

### `open-harness`

| Package | Version requirement | Purpose | Notes |
| --- | ---: | --- | --- |
| Node.js | `>=22.0.0` | Runtime for TypeScript harness scripts. | Declared in `open-harness\package.json`. |
| `@openharness/core` | `^0.6.2` | Harness runtime. | Integrates Vision over MCP. |
| `@ai-sdk/openai` | `^3.0.53` | OpenAI-compatible gateway calls. | Used with OpenClaw/OpenAI-compatible endpoints. |
| `ai` | `^6.0.168` | AI SDK primitives. | Harness support. |
| `zod` | `^4.3.6` | Runtime schemas and validation. | Harness config/tool validation. |
| `dotenv` | `^16.4.5` | Loads `.env`. | Avoid committing real `.env` files. |
| `typescript` | `^5.6.0` | TypeScript compiler. | `npm run typecheck` uses `tsc --noEmit`. |
| `tsx` | `^4.19.0` | Runs TypeScript directly. | Used by `npm run start` and helper scripts. |
| `@types/node` | `^22.0.0` | Node type definitions. | Development dependency. |

### `copilot-voice`

| Package | Version requirement | Purpose | Notes |
| --- | ---: | --- | --- |
| VS Code | `^1.95.0` | Extension host runtime. | Declared in `engines.vscode`. |
| `typescript` | `^5.8.3` | Builds the extension. | `npm run compile` runs `tsc -p ./`. |
| `@types/node` | `^22.15.3` | Node type definitions. | Development dependency. |
| `@types/vscode` | `^1.95.0` | VS Code extension API types. | Development dependency. |
| Groq API | Provider API, no npm package listed | Whisper transcription backend for the voice extension. | Extension setting `copilotVoice.groqApiKey`; optional Vision forwarding via `copilotVoice.visionUrl`. |

### `Archon`

| Tool/package | Version requirement | Purpose | Notes |
| --- | ---: | --- | --- |
| Bun | `^1.3.0` | Archon workspace runtime and package manager. | `Archon\package.json` uses Bun workspaces. |
| `@anthropic-ai/claude-agent-sdk` | `^0.2.74` | Claude agent SDK integration. | Archon dependency. |
| `typescript` | `^5.3.0` | TypeScript build/checks. | Archon dev dependency. |
| `eslint` | `^9.39.1` | Linting. | Used by `bun run lint`. |
| `prettier` | `^3.7.4` | Formatting. | Used by Archon format scripts. |
| `husky` | `^9.1.7` | Git hooks. | `prepare` script installs hooks. |
| `lint-staged` | `^15.2.0` | Pre-commit staged-file checks. | Archon-only workflow. |

## Azure and Foundry Workflow Dependencies

| Component | Version requirement | Purpose | Configuration notes |
| --- | ---: | --- | --- |
| `agent_workflow` Python packages | See `agent_workflow\requirements.txt` | Microsoft Agent Framework and Foundry content-collaboration workflow. | Install order matters: agentserver packages first, then `agent-framework-*==1.0.0rc6`. |
| `azure-ai-agentserver-agentframework` | `==1.0.0b16` | Agent server integration. | Pinned beta package. |
| `azure-ai-agentserver-core` | `==1.0.0b16` | Agent server core. | Pinned beta package. |
| `agent-dev-cli` | `==0.0.1b260316` | Agent development CLI. | Pins `agent-framework-core` to an older RC before later override. |
| `agent-framework-core` | `==1.0.0rc6` | Microsoft Agent Framework core. | Installed after agentserver packages. |
| `agent-framework-foundry` | `==1.0.0rc6` | Foundry integration. | Requires Azure credentials/config. |
| `agent-framework-openai` | `==1.0.0rc6` | OpenAI provider integration for Agent Framework. | Requires provider credentials. |
| `azure-identity` | `>=1.15.0` | Azure authentication. | Used by Foundry/Azure flows. |
| Azure Developer CLI (`azd`) | Current | Azure sample provisioning and deployment. | `azure-search-openai-demo\azure.yaml` and `install-azd.ps1` indicate this is expected for the sample. |
| Azure CLI (`az`) | Current | Azure login and resource operations. | Common prerequisite for Azure/Foundry workflows. |

## Nested Sample: `azure-search-openai-demo`

This directory is a separate Azure sample with its own dependency set.

| Tool/package | Version requirement | Purpose | Notes |
| --- | ---: | --- | --- |
| Python | `3.10` according to the sample `pyproject.toml` | Backend, scripts, Azure Functions sample code. | Separate from Vision's Python 3.11+/3.14 runtime. |
| `ruff` | `>=0.14.2` in `requirements-dev.txt` | Linting. | Sample uses a different Ruff floor than top-level Vision. |
| `black` | `>=26.1.0` in `requirements-dev.txt` | Formatting. | Sample config line length is `120`. |
| `pytest`, `pytest-asyncio`, `pytest-cov` | Unpinned in `requirements-dev.txt` | Tests and coverage. | Sample-specific. |
| `playwright`, `pytest-playwright` | Unpinned in `requirements-dev.txt` | Browser tests. | Requires browser install step. |
| `pre-commit`, `pip-tools`, `diff_cover` | Unpinned | Dev workflow and dependency maintenance. | Sample-specific. |
| `ty` | `==0.0.21` | Type checking. | Configured in the sample `pyproject.toml`. |
| `axe-playwright-python` | Unpinned | Accessibility checks. | Sample-specific browser accessibility testing. |

## MCP Servers

Workspace MCP servers are configured in `.vscode\mcp.json`.

| Server | Transport | Command | Purpose | Configuration notes |
| --- | --- | --- | --- | --- |
| `github` | HTTP | `https://api.githubcopilot.com/mcp/` | GitHub issues, PRs, repos, and code search. | Requires Copilot/GitHub authentication in the client. |
| `filesystem` | stdio | `npx -y @modelcontextprotocol/server-filesystem ${workspaceFolder}` | Read/write access to the Vision workspace. | Scoped to the workspace folder. |
| `lmstudio-rag` | stdio | `python launch_lmstudio_rag_mcp.py` | Reads the LM Studio RAG/plugin workspace. | Uses `RAG_PLUGIN_WORKSPACE`; falls back to `F:\rag-v1` on Windows and `~/rag-v1` elsewhere. |
| `fetch` | stdio | `npx -y @modelcontextprotocol/server-fetch` | Fetches URLs as Markdown or raw HTML. | Requires Node and network access. |
| `git` | stdio | `npx -y @modelcontextprotocol/server-git ${workspaceFolder}` | Git history, diffs, and repo state. | Requires Git and Node. |
| `memory` | stdio | `npx -y @modelcontextprotocol/server-memory` | Persistent knowledge graph memory. | Storage location is server-managed. |
| `sequential-thinking` | stdio | `npx -y @modelcontextprotocol/server-sequential-thinking` | Structured multi-step reasoning. | Requires Node. |
| `puppeteer` | stdio | `npx -y @modelcontextprotocol/server-puppeteer` | Browser automation, screenshots, and extraction. | Requires browser dependencies. |
| `vision-local` | stdio | `python vision_mcp_server.py` | Local FastMCP bridge for Vision health, memory, models, and tool execution. | Sets `VISION_BASE_URL=http://localhost:8765`. |
| `brave-search` | stdio | `npx -y @modelcontextprotocol/server-brave-search` | Brave Search API access. | Requires `BRAVE_API_KEY`. |

## Services and Ports

| Service | Default address | Purpose | Configuration notes |
| --- | --- | --- | --- |
| Vision backend | `http://localhost:8765` | FastAPI app, WebSocket backend, operator UI, and Command Center. | `launch_vision.ps1` starts `uvicorn live_chat_app:app --host 127.0.0.1 --port 8765` unless `VISION_HOST` is set. |
| Vision Command Center | `http://localhost:8765/command-center` | Runtime health, docs, workflows, routines, and diagnostics UI. | Controlled by `vision_command_center_config.json`. |
| Ollama | `http://127.0.0.1:11434` | Local model server. | Launcher can switch between local-only and LAN modes; keep local-only unless LAN access is needed. |
| OpenClaw gateway | `http://127.0.0.1:18789/v1` or tailnet endpoint | OpenAI-compatible gateway for models and Copilot workflows. | `scripts\copilot-openclaw.ps1` derives local URL from OpenClaw config; VS Code custom model currently points to `https://msi.tail886dbb.ts.net/v1`. |
| Debugpy | `localhost:5678` | Python debugger listener. | VS Code task `Vision: Start debugpy listener (5678)`. |
| Archon app | `${PORT:-3000}` | Optional Archon web/server stack. | Docker Compose maps host port to the same container port. |
| PostgreSQL for Archon | `127.0.0.1:${POSTGRES_PORT:-5432}` | Optional local Archon database. | Enabled with Docker Compose profile `with-db`. |
| Archon auth service | `${AUTH_SERVICE_PORT:-9000}` internal expose | Optional Caddy forward-auth service. | Enabled with Docker Compose profile `auth`. |
| Caddy | `80`, `443`, `443/udp` | Optional HTTPS reverse proxy for Archon cloud profile. | Requires `DOMAIN` in Archon `.env`. |

## Environment Variables and Secrets

Use `.env.example` as the non-secret template. Do not commit real `.env` values.

| Variable | Required? | Purpose | Notes |
| --- | --- | --- | --- |
| `GITHUB_TOKEN` | Optional/provider-specific | GitHub Models or GitHub provider access. | Also useful for GitHub workflows depending on tool/client. |
| `OPENAI_API_KEY` | Optional/provider-specific | OpenAI provider access. | Required for OpenAI-backed models. |
| `ELEVENLABS_API_KEY` | Optional for app, required for ElevenLabs voice/tool sync | ElevenLabs TTS, STT, and widget setup. | `setup_el_agent_tools.py` expects this for syncing tools. |
| `ELEVENLABS_WIDGET_AGENT_ID` | Optional | Public ElevenLabs widget agent ID. | Needed for widget-first browser voice flow. |
| `GROQ_API_KEY` | Optional | Groq provider and fast Whisper fallback. | Also used by `copilot-voice` when configured. |
| `ANTHROPIC_API_KEY` | Optional | Anthropic provider access. | Used directly or through OpenClaw workflows. |
| `DEEPSEEK_API_KEY` | Optional | DeepSeek provider access. | Provider-specific. |
| `MISTRAL_API_KEY` | Optional | Mistral provider access. | Provider-specific. |
| `GEMINI_API_KEY` | Optional | Google Gemini provider access. | Provider-specific. |
| `XAI_API_KEY` | Optional | xAI provider access. | Provider-specific. |
| `BRAVE_API_KEY` | Optional | Brave Search MCP server. | Referenced in `.vscode\mcp.json`. |
| `VISION_HOST` | Optional | Backend bind host. | Defaults to `127.0.0.1`; set `0.0.0.0` only for same-network access. |
| `VISION_ALLOWED_ORIGINS` | Recommended for LAN/browser use | Trusted browser origins. | Configure before exposing Vision beyond localhost. |
| `VISION_TOOL_TOKEN` | Recommended for LAN/tool access | Protects tool execution endpoints. | Use before same-network mobile access. |
| `VISION_BASE_URL` | Optional | Base URL for clients/MCP harnesses. | `vision-local` MCP sets this to `http://localhost:8765`. |
| `OLLAMA_HOST` | Managed by launcher unless overridden | Ollama bind/listen address. | Derived from `vision_command_center_config.json`. |
| `OLLAMA_ORIGINS` | Managed by launcher unless overridden | Browser origins allowed by Ollama. | Defaults to localhost Vision origins. |
| `OLLAMA_MODELS` | Managed by launcher unless overridden | Ollama model library path. | Current default is `F:\models`. |
| `OPENCLAW_GATEWAY_TOKEN` | Managed by helper script | Auth token for OpenClaw gateway. | `scripts\copilot-openclaw.ps1` reads it from `%USERPROFILE%\.openclaw\openclaw.json` and persists it as a user env var. |
| `COPILOT_PROVIDER_TYPE` | Managed by helper script | Tells Copilot CLI to use OpenAI-compatible provider mode. | Set to `openai`. |
| `COPILOT_PROVIDER_BASE_URL` | Managed by helper script | Copilot CLI provider base URL. | Usually `http://127.0.0.1:18789/v1`. |
| `COPILOT_PROVIDER_API_KEY` | Managed by helper script | Copilot CLI API key/token. | Set from the OpenClaw gateway token. |
| `COPILOT_MODEL` | Managed by helper script | Model used by Copilot CLI. | Set to `openclaw/default`. |
| `RAG_PLUGIN_WORKSPACE` | Optional | LM Studio RAG/plugin workspace path. | Falls back to `F:\rag-v1` on Windows and `~/rag-v1` elsewhere. |

## VS Code Tooling

Recommended extensions are declared in `.vscode\extensions.json`.

| Extension | Purpose | Notes |
| --- | --- | --- |
| `ms-python.python`, `ms-python.vscode-pylance`, `ms-python.debugpy` | Python editing, language server, and debugging. | Python interpreter is pinned in workspace settings. |
| `charliermarsh.ruff`, `ms-python.pylint`, `ms-python.flake8`, `ms-python.mypy-type-checker`, `ms-python.isort` | Python linting, formatting, import sorting, and type checks. | Multiple linters are configured; Ruff is the default formatter. |
| `ms-toolsai.jupyter` | Notebook support. | Useful for experiments and analysis. |
| `github.copilot-chat` | Copilot chat and custom OpenAI-compatible model settings. | Workspace defines `openclaw/default` under custom OAI models. |
| `eamodio.gitlens` | Git insights. | Enabled in workspace settings. |
| `usernamehw.errorlens`, `gruntfuggly.todo-tree`, `aaron-bond.better-comments` | Inline diagnostics and code annotations. | Tags and colors are configured in settings. |
| `humao.rest-client` | Manual HTTP API checks. | Shared variables include `vision_base` and `ollama_base`. |
| `mikestead.dotenv` | `.env` editing support. | Do not commit secrets. |
| `redhat.vscode-yaml`, `davidanson.vscode-markdownlint` | YAML and Markdown quality. | Markdown lint disables long-line, inline HTML, and first-heading rules. |
| `warm3snow.vscode-ollama`, `technovangelist.ollamamodelfile` | Ollama and Modelfile support. | Useful for `Modelfile.ultronv2`. |
| `ms-vscode.powershell`, `tyriar.windows-terminal` | PowerShell and terminal integration. | Important for launcher scripts. |

## Launchers, Scripts, and Local Tools

| File/tool | Purpose | Configuration notes |
| --- | --- | --- |
| `launch_vision.ps1` | Main launcher for Python package checks, Ollama startup, Vision backend startup, health checks, and UI opening. | Reads `vision_command_center_config.json`; writes `vision_launch.log` and `vision_error.log`. |
| `vision_master_launcher.ps1` | Higher-level launcher for the full Vision experience. | Delegates core startup to `launch_vision.ps1`. |
| `scripts\copilot-openclaw.ps1` | Configures and verifies Copilot CLI through OpenClaw. | Reads OpenClaw token from `%USERPROFILE%\.openclaw\openclaw.json`; `-Verify` checks `/v1/models`. |
| `openclaw-elite.ps1` and related `openclaw-elite-*` files | OpenClaw/Vision helper launchers and configurations. | Models include `openclaw/default`, fast, power, and local presets in `openclaw-elite-config.json`. |
| `vision_mcp_server.py` | Repo-local FastMCP bridge. | Uses `VISION_BASE_URL` to call the running backend. |
| `hive_tools\context_mapper.py` | Generates machine-readable repo context. | README command writes `.archon\artifacts\project_context.json`. |
| `setup_el_agent_tools.py` | Syncs Vision tools and prompt into ElevenLabs widget agent. | Requires valid `ELEVENLABS_API_KEY` and widget-agent setup. |
| `Modelfile.ultronv2` | Ollama Modelfile for `qikfox/ultronv2`. | Created with `ollama create qikfox/ultronv2 -f C:\project\vision\Modelfile.ultronv2`. |
| `create_desktop_shortcut.ps1` and `create-openclaw-elite-shortcut.ps1` | Windows shortcut helpers. | Use when creating one-click local launchers. |
| `rag_launch.bat`, `rag_tool.py`, `vision_rag.py`, `vision_rag_integration.py` | Local RAG helper surface. | Coordinate with `RAG_PLUGIN_WORKSPACE` and local model/search services. |

## Configuration Files

| File | Purpose | Notes |
| --- | --- | --- |
| `requirements.txt` | Main install list for the current Vision runtime. | Most up-to-date install floor for several packages. |
| `pyproject.toml` | Project metadata and tool configuration. | Some runtime dependency floors differ from `requirements.txt`; reconcile before packaging/releasing. |
| `.env.example` | Safe template for provider credentials. | Copy to `.env`; never commit real secrets. |
| `vision_command_center_config.json` | Non-secret launcher and Command Center profile. | Controls UI behavior, Ollama access mode, origins, and model path. |
| `.vscode\settings.json` | Workspace editor, lint, test, REST, Copilot, and OpenClaw model settings. | Contains machine-specific Python paths and custom model URL. |
| `.vscode\tasks.json` | Runnable backend, test, debug, OpenClaw, and SQL project tasks. | Useful for repeatable VS Code actions. |
| `.vscode\mcp.json` | MCP server definitions. | Requires Node, Python, Git, and any provider-specific keys. |
| `.pre-commit-config.yaml` | Git hook definitions. | Hooks are pinned separately from `pyproject.toml` dev dependencies. |
| `Archon\docker-compose.yml` | Optional container stack for Archon. | Supports SQLite default, PostgreSQL, Caddy, and auth profiles. |
| `agent_workflow\.env.template` | Template for Microsoft Agent Framework workflow settings. | Keep separate from top-level `.env`. |

## Known Version Drift

The project currently has overlapping dependency declarations:

| Dependency | `requirements.txt` | `pyproject.toml` | Practical note |
| --- | ---: | ---: | --- |
| Python | Not declared | `>=3.11` | README badges/settings indicate Python 3.14 is used locally. |
| `fastapi` | `>=0.115` | `>=0.104` | Prefer `requirements.txt` for local runtime installs. |
| `uvicorn` | `>=0.30` | `>=0.24` | Prefer `requirements.txt`. |
| `httpx` | `>=0.27.0` | `>=0.25` | Prefer `requirements.txt`. |
| `numpy` | `>=1.26` | `>=1.24` | Prefer `requirements.txt`. |
| `scipy` | `>=1.12` | `>=1.11` | Prefer `requirements.txt`. |
| `openai` | `>=1.50.0` | `>=2.30` | This is a meaningful mismatch; provider behavior should be tested before standardizing. |
| `anthropic` | `>=0.50.0` | `>=0.25` | Prefer `requirements.txt` unless packaging requires otherwise. |
| `ollama` | `>=0.3.0` | `>=0.1` | Prefer `requirements.txt`. |
| `elevenlabs` | `>=2.0.0` | `>=2.42` | This is a meaningful mismatch; check the live code path before changing. |
| NVIDIA telemetry | `nvidia-ml-py>=12.560.30` | `pynvml>=12.5` | These package names overlap in purpose; keep imports aligned with installed package. |

Before turning this workspace into a distributable package, standardize dependency floors in one source of truth and regenerate lock files.

## Quick Verification Commands

Run these from `C:\project\VISION` after installing dependencies:

```powershell
python --version
python -m pip install -r requirements.txt
python -m py_compile live_chat_app.py
python test_tools.py
python test_vision.py
.\launch_vision.ps1 -NoBrowser
```

For service checks:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8765/api/health
Invoke-WebRequest -UseBasicParsing http://localhost:11434/api/tags
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\copilot-openclaw.ps1 -Verify
```

