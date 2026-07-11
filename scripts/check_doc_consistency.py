"""
scripts/check_doc_consistency.py
=================================
Lightweight doc-vs-code consistency checker for the Vision operator.

Checks:
  1. Tool names registered in TOOLS list (live_chat_app.py) vs tools
     mentioned in docs/ markdown files.
  2. FastAPI route paths defined in live_chat_app.py vs those referenced
     in docs/ markdown files.
  3. Provider names in PROVIDERS dict vs docs/ markdown files.

Exit code 0 = no drift found (or only warnings).
Exit code 1 = one or more drift items detected.

Usage:
    python scripts/check_doc_consistency.py [--strict]

--strict: exit 1 if any tool/route is in code but NOT in docs (default:
          only exit 1 if something is in docs but REMOVED from code).
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = REPO_ROOT / "live_chat_app.py"
DOCS_DIR = REPO_ROOT / "docs"
PROJECT_FILE = REPO_ROOT / "PROJECT.md"


# ── Extraction helpers ─────────────────────────────────────────────────────────


def extract_tool_names(src: str) -> list[str]:
    """Parse TOOLS list from source and return all tool name strings."""
    # Find the TOOLS = [...] assignment via AST
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "TOOLS" for t in node.targets):
            continue
        names: list[str] = []
        for item in ast.walk(node.value):
            if (
                isinstance(item, ast.Constant)
                and isinstance(item.value, str)
                and re.fullmatch(r"[a-z][a-z0-9_]{1,40}", item.value)
            ):
                names.append(item.value)
        return names
    return []


def extract_route_paths(src: str) -> list[str]:
    """Return all @app.get/@app.post path strings."""
    return re.findall(r'@app\.(?:get|post|put|delete|patch)\("(/[^"]*)"', src)


def extract_provider_names(src: str) -> list[str]:
    """Return provider keys from PROVIDERS dict (first-level string keys)."""
    match = re.search(r"PROVIDERS\s*[:=]\s*\{", src)
    if not match:
        return []
    # Grab everything between the opening { and matching }
    depth = 0
    start = match.end() - 1
    end = start
    for i, ch in enumerate(src[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    block = src[start : end + 1]
    return re.findall(r'"([a-z][a-z0-9_]{1,20})"\s*:', block)


def load_docs_text() -> str:
    """Return concatenated text of all docs/ markdown files + PROJECT.md."""
    parts: list[str] = []
    if DOCS_DIR.is_dir():
        for p in sorted(DOCS_DIR.glob("**/*.md")):
            parts.append(p.read_text(encoding="utf-8", errors="ignore"))
    if PROJECT_FILE.is_file():
        parts.append(PROJECT_FILE.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


# ── Drift detection ────────────────────────────────────────────────────────────


def check_drift(
    label: str,
    code_items: list[str],
    docs_text: str,
    strict: bool,
) -> list[str]:
    """
    Return a list of drift messages.

    Default mode: flag items mentioned in docs that are GONE from code.
    Strict mode: also flag items in code that are never mentioned in docs.
    """
    drift: list[str] = []

    # Extract all backtick-wrapped identifiers from docs
    doc_refs: set[str] = set(re.findall(r"`([a-z][a-z0-9_/]{1,50})`", docs_text))

    # Items referenced in docs but absent from code (regression check)
    code_set = set(code_items)
    for ref in doc_refs:
        # Only check refs that look like tool/route/provider names (not prose)
        if re.fullmatch(r"[a-z][a-z0-9_]{2,40}", ref) and ref not in code_set:
            # Avoid false positives on common prose words
            _prose_words = {
                "the",
                "and",
                "for",
                "with",
                "from",
                "that",
                "this",
                "not",
                "are",
                "was",
                "has",
                "can",
                "will",
                "get",
                "set",
                "run",
                "use",
                "true",
                "false",
                "none",
                "main",
                "env",
                "key",
                "log",
                "api",
                "str",
                "int",
                "bool",
                "list",
                "dict",
                "any",
                "type",
                "path",
            }
            if ref not in _prose_words:
                drift.append(f"  [{label}] '{ref}' is referenced in docs but no longer exists in code")

    # Strict: items in code not mentioned anywhere in docs
    if strict:
        for item in code_items:
            if item not in docs_text:
                drift.append(f"  [{label}] '{item}' exists in code but is not mentioned in any doc")

    return drift


# ── Main ───────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Vision doc consistency checker")
    parser.add_argument("--strict", action="store_true", help="Flag code items missing from docs")
    args = parser.parse_args()

    if not APP_FILE.is_file():
        print(f"ERROR: cannot find {APP_FILE}")
        return 1

    src = APP_FILE.read_text(encoding="utf-8", errors="ignore")
    docs_text = load_docs_text()

    tool_names = extract_tool_names(src)
    route_paths = extract_route_paths(src)
    provider_names = extract_provider_names(src)

    print("Vision Doc Consistency Check")
    print(f"  App file : {APP_FILE.name}")
    print(f"  Tools    : {len(tool_names)} found")
    print(f"  Routes   : {len(route_paths)} found")
    print(f"  Providers: {len(provider_names)} found")
    print(f"  Docs     : {len(docs_text):,} chars scanned")
    print()

    drift: list[str] = []

    # Default checks (always run): flag doc references that vanished from code
    drift.extend(check_drift("tools", tool_names, docs_text, strict=False))
    drift.extend(check_drift("routes", route_paths, docs_text, strict=False))
    drift.extend(check_drift("providers", provider_names, docs_text, strict=False))

    # Check duplicate tool names
    seen: set[str] = set()
    for name in tool_names:
        if name in seen:
            drift.append(f"  [tools] Duplicate tool name: '{name}'")
        seen.add(name)

    # Check duplicate routes
    seen_routes: set[str] = set()
    for path in route_paths:
        if path in seen_routes:
            drift.append(f"  [routes] Duplicate route path: '{path}'")
        seen_routes.add(path)

    # Strict-mode: also flag code items missing from docs
    if args.strict:
        drift.extend(check_drift("tools", tool_names, docs_text, strict=True))
        drift.extend(check_drift("routes", route_paths, docs_text, strict=True))
        drift.extend(check_drift("providers", provider_names, docs_text, strict=True))

    # Summary
    if drift:
        print("⚠  Drift detected:")
        for item in drift:
            print(item)
        print()
        return 1
    else:
        print("✅ No drift detected")
        print(
            f"   {len(tool_names)} tools, {len(route_paths)} routes, {len(provider_names)} providers — all consistent"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
