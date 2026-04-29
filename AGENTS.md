# Repository Guidelines

## Project Structure & Module Organization

Vision is a Windows-first accessibility operator. The main Python runtime lives at the repository root, with `live_chat_app.py` as the FastAPI/WebSocket backend and `vision_mcp_server.py`, `vision_rag.py`, `voice_toggle.py`, and `elite_*.py` modules supporting tools, memory, safety, metrics, and provider behavior. Tests are root-level `test_*.py` files with fixtures in `conftest.py`. Runtime docs and images are in `docs/`; scripts are in `scripts/` and root PowerShell launchers such as `launch_vision.ps1`. TypeScript subprojects live in `open-harness/` and `copilot-voice/`. Avoid committing generated caches, logs, screenshots, `.pw_profile/`, `openJdk-25/`, or large local data snapshots unless required.

## Build, Test, and Development Commands

Set up Python dependencies with:

```powershell
python -m pip install -r requirements.txt
python -m pip install -e ".[dev]"
```

Run the operator with `python live_chat_app.py`; the launcher path is `.\launch_vision.ps1`. Use `python -m pytest` for the full suite, or targeted checks such as `python test_tools.py` and `python test_vision.py`. Before submitting Python changes, run `ruff format .`, `ruff check .`, and `pyright` when type signatures change. CI also runs Bandit and Trivy security scans. For `open-harness/`, use `npm install`, `npm run typecheck`, `npm run build`, and `npm start`.

## Coding Style & Naming Conventions

Python targets 3.11+ with 4-space indentation, double quotes, Ruff formatting, Black-compatible wrapping, and strict typing from `pyproject.toml`. Name Python modules and functions in `snake_case`, classes in `PascalCase`, and constants in `UPPER_SNAKE_CASE`. Preserve `elite_*` helper boundaries instead of folding unrelated concerns into `live_chat_app.py`. TypeScript uses ES modules and `camelCase` functions under `src/`.

## Testing Guidelines

Use pytest with `pytest-asyncio`; mark slow or integration tests with the configured `slow` and `integration` markers. New Python tests should follow `test_<feature>.py` naming and cover handler behavior, safety checks, async flows, and failure paths. Coverage is configured for `live_chat_app` and related runtime modules; do not lower coverage without documenting why.

## Commit & Pull Request Guidelines

Recent history uses concise subjects with prefixes such as `feat:`, `fix:`, `docs:`, and `refactor:`. Keep commits scoped and describe behavior, not tooling noise. PRs should include a summary, validation commands, linked issues or docs, and screenshots for UI changes to `live_chat_ui.html`, `vision_command_center.html`, or docs imagery.

## Security & Configuration Tips

Do not commit real secrets from `.env`, provider keys, logs, or local memory dumps. Treat `chat_events.log`, `memory.json`, `.rag/`, and curated `data/` snapshots as sensitive unless the change explicitly requires them. Prefer `.env.example`-style documentation for new configuration.
