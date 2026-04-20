"""Launch the LM Studio RAG filesystem MCP with env-aware path resolution."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _default_rag_workspace() -> Path:
    """Return the platform fallback path for the LM Studio RAG workspace."""
    if os.name == "nt":
        return Path(r"F:\rag-v1")
    return Path.home() / "rag-v1"


def _resolve_rag_workspace() -> tuple[Path, str]:
    """Resolve the workspace path and describe where it came from."""
    configured = os.environ.get("RAG_PLUGIN_WORKSPACE", "").strip()
    if configured:
        return Path(configured).expanduser(), "RAG_PLUGIN_WORKSPACE"
    return _default_rag_workspace(), "platform fallback"


def main() -> int:
    """Start the MCP filesystem server for the resolved LM Studio workspace."""
    workspace, source = _resolve_rag_workspace()
    if not workspace.exists():
        print(
            f"LM Studio RAG workspace not found: {workspace} (source: {source}). "
            "Set RAG_PLUGIN_WORKSPACE to the correct plugin workspace path before starting MCP.",
            file=sys.stderr,
        )
        return 1

    command = ["npx", "-y", "@modelcontextprotocol/server-filesystem", str(workspace)]
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError:
        print("Unable to start lmstudio-rag MCP because 'npx' is not installed or not on PATH.", file=sys.stderr)
        return 1
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
