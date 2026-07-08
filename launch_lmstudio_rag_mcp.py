"""Launch the LM Studio RAG filesystem MCP with env-aware path resolution."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
MAX_INDEXABLE_FILES = 7000
CURATED_SUBDIR = "vision-corpus"
CURATED_ROOT_FILES = (
    "README.md",
    "DOCUMENTATION_INDEX.md",
    "architecture.md",
    "PROJECT.md",
    "HIVE.md",
    "AGENTS.md",
    "components.md",
    "setup.md",
    "live_chat_app.py",
    "vision_mcp_server.py",
    "vision_rag.py",
    "vision_rag_integration.py",
    "launch_lmstudio_rag_mcp.py",
)


def _legacy_rag_workspace_root() -> Path:
    """Return the historical LM Studio workspace root."""
    if os.name == "nt":
        return Path(r"F:\rag-v1")
    return Path.home() / "rag-v1"


def _default_rag_workspace() -> Path:
    """Return the platform fallback path for the LM Studio RAG workspace."""
    return _legacy_rag_workspace_root() / CURATED_SUBDIR


def _curated_sources() -> list[Path]:
    """Return the curated repo files mirrored into the LM Studio corpus."""
    files: list[Path] = []
    for relative in CURATED_ROOT_FILES:
        candidate = BASE / relative
        if candidate.exists():
            files.append(candidate)
    files.extend(sorted((BASE / "docs").glob("*.md")))
    files.extend(sorted((BASE / ".github" / "skills").glob("*/SKILL.md")))
    files.extend(sorted((BASE / ".github" / "agents").glob("*.md")))
    files.extend(sorted((BASE / ".archon" / "workflows").glob("*.yaml")))
    files.extend(sorted((BASE / ".vscode").glob("*.json")))
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for file_path in files:
        if file_path not in seen:
            unique_files.append(file_path)
            seen.add(file_path)
    return unique_files


def _sync_curated_workspace(workspace: Path) -> int:
    """Rebuild the curated LM Studio workspace from a compact set of repo files."""
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    copied = 0
    for source in _curated_sources():
        destination = workspace / source.relative_to(BASE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1
    return copied


def _count_files(root: Path, limit: int = MAX_INDEXABLE_FILES + 1) -> int:
    """Count files under a directory up to the configured indexing threshold."""
    count = 0
    try:
        for _ in root.rglob("*"):
            if _.is_file():
                count += 1
                if count >= limit:
                    break
    except OSError:
        return limit
    return count


def _auto_curated_workspace(configured: Path) -> Path | None:
    """Redirect oversized LM Studio workspaces to a curated sibling corpus."""
    normalized = configured.expanduser()
    if normalized.name.lower() == CURATED_SUBDIR:
        return None
    if _count_files(normalized) <= MAX_INDEXABLE_FILES:
        return None
    root = normalized.parent if normalized.name.lower() == "data" else normalized
    return root / CURATED_SUBDIR


def _resolve_rag_workspace() -> tuple[Path, str]:
    """Resolve the workspace path and describe where it came from."""
    configured = os.environ.get("RAG_PLUGIN_WORKSPACE", "").strip()
    if configured:
        configured_path = Path(configured).expanduser()
        curated = _auto_curated_workspace(configured_path)
        if curated is not None:
            return curated, "RAG_PLUGIN_WORKSPACE (auto-curated)"
        return configured_path, "RAG_PLUGIN_WORKSPACE"
    return _default_rag_workspace(), "platform fallback"


def main() -> int:
    """Start the MCP filesystem server for the resolved LM Studio workspace."""
    workspace, source = _resolve_rag_workspace()
    if source in {"platform fallback", "RAG_PLUGIN_WORKSPACE (auto-curated)"}:
        copied = _sync_curated_workspace(workspace)
        print(f"Using curated LM Studio corpus at {workspace} ({copied} files).", file=sys.stderr)
    if not workspace.exists():
        print(
            f"LM Studio RAG workspace not found: {workspace} (source: {source}). "
            "Set RAG_PLUGIN_WORKSPACE to the correct plugin workspace path before starting MCP.",
            file=sys.stderr,
        )
        return 1

    command = ["npx", "-y", "@modelcontextprotocol/server-filesystem", str(workspace)]
    try:
        result = subprocess.run(command, check=False, shell=(os.name == "nt"))
    except FileNotFoundError:
        print("Unable to start lmstudio-rag MCP because 'npx' is not installed or not on PATH.", file=sys.stderr)
        return 1
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
