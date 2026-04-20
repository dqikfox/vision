"""Generate a machine-readable context brain for the Vision repository."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / ".archon" / "artifacts" / "project_context.json"
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".archon",
}
TRACKED_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".html", ".css", ".json", ".ps1"}


@dataclass(slots=True)
class CatalogItem:
    """Describe a reusable repo surface such as a skill, agent, or workflow."""

    name: str
    path: str
    description: str


def _read_text(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def _rel(path: Path) -> str:
    """Return a repo-relative POSIX path."""
    return path.relative_to(REPO_ROOT).as_posix()


def _clean_scalar(value: str) -> str:
    """Normalize a YAML-like scalar from simple frontmatter or headers."""
    return value.strip().strip("'\"")


def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Parse the simple frontmatter used by repo skills and agents."""
    lines = _read_text(path).splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _clean_scalar(value)
    return data


def _parse_workflow_header(path: Path) -> dict[str, str]:
    """Parse top-level name and description fields from an Archon workflow."""
    lines = _read_text(path).splitlines()
    header: dict[str, str] = {}
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("name:"):
            header["name"] = _clean_scalar(line.split(":", 1)[1])
        elif line.startswith("description:"):
            remainder = line.split(":", 1)[1].strip()
            if remainder == "|":
                idx += 1
                description_lines: list[str] = []
                while idx < len(lines):
                    block_line = lines[idx]
                    if block_line.startswith("  "):
                        description_lines.append(block_line[2:].strip())
                        idx += 1
                        continue
                    if not block_line.strip():
                        idx += 1
                        continue
                    break
                header["description"] = " ".join(part for part in description_lines if part)
                continue
            header["description"] = _clean_scalar(remainder)
        elif line.startswith("nodes:"):
            break
        idx += 1
    return header


def _collect_skills() -> list[dict[str, str]]:
    """Collect repo-local Copilot skills."""
    items: list[CatalogItem] = []
    for path in sorted(REPO_ROOT.glob(".github/skills/*/SKILL.md")):
        frontmatter = _parse_frontmatter(path)
        items.append(
            CatalogItem(
                name=frontmatter.get("name", path.parent.name),
                path=_rel(path),
                description=frontmatter.get("description", ""),
            )
        )
    return [asdict(item) for item in items]


def _collect_agents() -> list[dict[str, str]]:
    """Collect repo-local custom agents."""
    items: list[CatalogItem] = []
    for path in sorted(REPO_ROOT.glob(".github/agents/*.agent.md")):
        frontmatter = _parse_frontmatter(path)
        items.append(
            CatalogItem(
                name=frontmatter.get("name", path.stem),
                path=_rel(path),
                description=frontmatter.get("description", ""),
            )
        )
    return [asdict(item) for item in items]


def _collect_archon_workflows() -> list[dict[str, Any]]:
    """Collect repo-local Archon workflows and their bash validation steps."""
    items: list[dict[str, Any]] = []
    for path in sorted(REPO_ROOT.glob(".archon/workflows/**/*.yaml")):
        header = _parse_workflow_header(path)
        bash_steps = re.findall(r"^\s+bash:\s*(.+)$", _read_text(path), flags=re.MULTILINE)
        items.append(
            {
                "name": header.get("name", path.stem),
                "path": _rel(path),
                "description": header.get("description", ""),
                "bash_steps": bash_steps,
            }
        )
    return items


def _collect_mcp_servers() -> list[dict[str, str]]:
    """Collect workspace MCP server declarations."""
    mcp_path = REPO_ROOT / ".vscode" / "mcp.json"
    if not mcp_path.exists():
        return []

    payload = json.loads(_read_text(mcp_path))
    servers: list[dict[str, str]] = []
    for name, config in sorted(payload.get("servers", {}).items()):
        server_type = str(config.get("type", ""))
        target = ""
        if server_type == "http":
            target = str(config.get("url", ""))
        elif server_type == "stdio":
            target = str(config.get("command", ""))
        servers.append(
            {
                "name": name,
                "type": server_type,
                "target": target,
                "description": str(config.get("description", "")),
            }
        )
    return servers


def _collect_file_stats() -> dict[str, int]:
    """Count tracked file types across the repo."""
    counts: Counter[str] = Counter()
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() in TRACKED_SUFFIXES:
            counts[path.suffix.lower()] += 1
    return dict(sorted(counts.items()))


def _extract_validation_commands() -> list[str]:
    """Extract the documented validation shortlist and Archon bash validations."""
    commands: list[str] = []

    doc_index = REPO_ROOT / "DOCUMENTATION_INDEX.md"
    if doc_index.exists():
        match = re.search(r"## Validation Shortlist.*?```powershell(.*?)```", _read_text(doc_index), flags=re.DOTALL)
        if match:
            commands.extend(line.strip() for line in match.group(1).splitlines() if line.strip())

    for workflow in _collect_archon_workflows():
        commands.extend(str(step).strip() for step in workflow.get("bash_steps", []) if str(step).strip())

    deduped: list[str] = []
    seen: set[str] = set()
    for command in commands:
        if command not in seen:
            deduped.append(command)
            seen.add(command)
    return deduped


def build_context_brain(repo_root: Path | None = None) -> dict[str, Any]:
    """Build the repo's machine-readable context brain."""
    root = repo_root or REPO_ROOT
    if root != REPO_ROOT:
        raise ValueError("build_context_brain currently supports the Vision repo root only.")

    archon_workflows = _collect_archon_workflows()
    mcp_servers = _collect_mcp_servers()

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "project": {
            "name": "vision",
            "root": str(root),
            "mission": "Universal accessibility operator and home-ops assistant",
            "primary_runtime": "FastAPI + WebSocket backend in live_chat_app.py",
        },
        "entrypoints": {
            "backend": "live_chat_app.py",
            "frontend": "live_chat_ui.html",
            "mcp_bridge": "vision_mcp_server.py",
            "docs_index": "DOCUMENTATION_INDEX.md",
            "always_on_instructions": ".github/copilot-instructions.md",
        },
        "catalog": {
            "skills": _collect_skills(),
            "agents": _collect_agents(),
        },
        "automation": {
            "archon_config": ".archon/config.yaml" if (root / ".archon" / "config.yaml").exists() else "",
            "archon_workflows": archon_workflows,
            "validation_commands": _extract_validation_commands(),
        },
        "integration": {
            "mcp_servers": mcp_servers,
            "external_harness_entry": "vision_mcp_server.py",
            "context_brain_output": ".archon/artifacts/project_context.json",
        },
        "refresh": {
            "primary_order": [
                ".github/copilot-instructions.md",
                "DOCUMENTATION_INDEX.md",
                "README.md",
                "architecture.md",
                "vision_mcp_server.py",
                ".archon/config.yaml",
                ".archon/workflows/vision-repo-maintenance.yaml",
            ],
            "recommended_skill": "vision-context-brain",
            "recommended_council_skill": "vision-cognitive-council",
            "notes": [
                "Refresh from the context brain before broad tasks or after compaction.",
                "For broad, risky, or ambiguous work, use the cognitive council after the initial refresh.",
                "Prefer repo customizations and workflows before inventing new process layers.",
                "Use the MCP bridge for external harnesses instead of rebuilding the Vision API surface.",
            ],
        },
        "stats": {
            "file_counts_by_suffix": _collect_file_stats(),
            "skill_count": len(_collect_skills()),
            "agent_count": len(_collect_agents()),
            "archon_workflow_count": len(archon_workflows),
            "mcp_server_count": len(mcp_servers),
        },
    }


def _write_output(payload: dict[str, Any], output_path: Path) -> None:
    """Write the context brain JSON to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    """CLI entrypoint for generating the Vision context brain."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to .archon/artifacts/project_context.json when not using --stdout.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print the context brain JSON to stdout.")
    args = parser.parse_args()

    payload = build_context_brain()
    output_path = args.output or DEFAULT_OUTPUT

    if args.stdout:
        print(json.dumps(payload, indent=2))
        if args.output is not None:
            _write_output(payload, output_path)
        return 0

    _write_output(payload, output_path)
    print(f"Vision context brain written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
