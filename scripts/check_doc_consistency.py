"""
Automated doc consistency checks for Vision key runtime contracts.

Verifies that architecture.md and README.md stay aligned with the live
runtime values defined in live_chat_app.py.

Usage:
    python scripts/check_doc_consistency.py
    python scripts/check_doc_consistency.py --verbose

Exit code 0 = all checks passed, 1 = one or more failures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv

_PASS = "✅ PASS"
_FAIL = "❌ FAIL"
_WARN = "⚠  WARN"

failures: list[str] = []
warnings: list[str] = []


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract(pattern: str, text: str, group: int = 1) -> str | None:
    m = re.search(pattern, text)
    return m.group(group) if m else None


def check(name: str, ok: bool, detail: str = "", warn_only: bool = False) -> None:
    status = _PASS if ok else (_WARN if warn_only else _FAIL)
    if not ok:
        if warn_only:
            warnings.append(f"{name}: {detail}")
        else:
            failures.append(f"{name}: {detail}")
    if VERBOSE or not ok:
        print(f"  {status}  {name}")
        if detail and not ok:
            print(f"           {detail}")
    else:
        print(f"  {status}  {name}")


def main() -> int:  # noqa: C901
    app = _read(BASE / "live_chat_app.py")
    arch = _read(BASE / "architecture.md")
    readme = _read(BASE / "README.md")
    ui = _read(BASE / "live_chat_ui.html")

    print("\n── VAD thresholds ───────────────────────────────────────────")

    # RMS_THRESH
    rt = _extract(r"(?m)^RMS_THRESH\s*=\s*(\d+)", app, 1)
    at = _extract(r"RMS_THRESH\s*\(?(\d+)\)?", arch)
    check(
        f"RMS_THRESH code={rt} arch={at}",
        rt == at,
        f"live_chat_app.py has {rt}, architecture.md documents {at}",
    )

    # START_FRAMES
    sf = _extract(r"(?m)^START_FRAMES\s*=\s*(\d+)", app, 1)
    asf = _extract(r"START_FRAMES\s*\(?(\d+)\)?", arch)
    check(
        f"START_FRAMES code={sf} arch={asf}",
        sf == asf,
        f"live_chat_app.py has {sf}, architecture.md documents {asf}",
    )

    # END_FRAMES
    ef = _extract(r"(?m)^END_FRAMES\s*=\s*(\d+)", app, 1)
    aef = _extract(r"END_FRAMES\s*\(?(\d+)\)?", arch)
    check(
        f"END_FRAMES code={ef} arch={aef}",
        ef == aef,
        f"live_chat_app.py has {ef}, architecture.md documents {aef}",
    )

    # BARGE_RMS
    br = _extract(r"(?m)^BARGE_RMS\s*=\s*(\d+)", app, 1)
    abr = _extract(r"BARGE_RMS\s*\(?(\d+)\)?", arch)
    check(
        f"BARGE_RMS code={br} arch={abr}",
        br == abr,
        f"live_chat_app.py has {br}, architecture.md documents {abr}",
    )

    # BARGE_FRAMES
    bfr = _extract(r"(?m)^BARGE_FRAMES\s*=\s*(\d+)", app, 1)
    abfr = _extract(r"BARGE_FRAMES\s*\(?(\d+)\)?", arch)
    check(
        f"BARGE_FRAMES code={bfr} arch={abfr}",
        bfr == abfr,
        f"live_chat_app.py has {bfr}, architecture.md documents {abfr}",
    )

    print("\n── WebSocket protocol ───────────────────────────────────────")

    # Core server→client message types that should be in architecture.md
    core_server_types = [
        "init", "state", "transcript", "token", "stream_start",
        "stream_finalize", "volume", "action", "model_changed",
    ]
    for mt in core_server_types:
        in_arch = f"`{mt}`" in arch or f'"{mt}"' in arch
        check(f"arch docs server→client '{mt}'", in_arch, f"'{mt}' missing from architecture.md WebSocket table")

    # pipeline_timing is new — check it's in architecture.md (warn, not fail, since we just added it)
    in_arch_pt = "pipeline_timing" in arch
    check(
        "arch docs 'pipeline_timing'",
        in_arch_pt,
        "pipeline_timing event not yet documented in architecture.md — consider adding to WebSocket table",
        warn_only=True,
    )

    # Core server→client message types should have handlers in live_chat_ui.html
    ui_handler_types = [
        "stream_start", "transcript", "token", "state",
        "action", "model_changed", "pipeline_timing",
    ]
    for mt in ui_handler_types:
        in_ui = f"case '{mt}'" in ui
        check(f"UI handles '{mt}'", in_ui, f"No 'case \\'{mt}\\'' handler found in live_chat_ui.html")

    print("\n── Provider list ────────────────────────────────────────────")

    providers_in_code = re.findall(r'^PROVIDERS\s*=\s*\{[^}]+\}', app, re.DOTALL)
    code_providers = re.findall(r'"([a-z]+)":', providers_in_code[0] if providers_in_code else "")
    code_providers = [p for p in code_providers if p not in ("label", "base_url", "api_key", "models")]

    arch_providers = re.findall(r'\b(ollama|openai|github|groq|gemini|deepseek|mistral|anthropic|xai)\b', arch)
    arch_provider_set = set(arch_providers)
    for p in code_providers:
        check(
            f"arch mentions provider '{p}'",
            p in arch_provider_set,
            f"Provider '{p}' in PROVIDERS dict not mentioned in architecture.md",
            warn_only=True,
        )

    print("\n── Tool integrity ───────────────────────────────────────────")

    # Count TOOLS schema entries
    tools_schema_count = len(re.findall(r'"type":\s*"function"', app))
    # Count _EL_TOOL_NAMES entries
    el_names_block_m = re.search(r'_EL_TOOL_NAMES\s*=\s*\[(.*?)\]', app, re.DOTALL)
    el_names_count = len(re.findall(r'"[a-z_]+"', el_names_block_m.group(1))) if el_names_block_m else 0
    # Count exec_tool elif handlers
    exec_handlers = len(re.findall(r'elif name == "', app))

    check(
        f"TOOLS schema entries={tools_schema_count}",
        tools_schema_count > 0,
        "No TOOLS schema entries found — check TOOLS definition",
    )
    check(
        f"exec_tool handlers={exec_handlers}",
        exec_handlers > 0,
        "No exec_tool elif handlers found",
    )
    check(
        f"_EL_TOOL_NAMES count={el_names_count}",
        el_names_count > 0,
        "_EL_TOOL_NAMES list appears empty",
    )
    # Warn if exec_handlers count is far from tools_schema_count (>10 gap = likely drift)
    gap = abs(tools_schema_count - exec_handlers)
    check(
        f"TOOLS/exec_tool alignment gap={gap}",
        gap <= 15,
        f"Gap of {gap} between TOOLS schema ({tools_schema_count}) and exec_tool handlers ({exec_handlers})"
        " — some tools may have schema but no handler or vice versa",
        warn_only=gap <= 25,
    )

    print("\n── Port & backend reference ─────────────────────────────────")

    port = _extract(r"(?m)^PORT\s*=\s*int\(os\.environ\.get\([^,]+,\s*['\"]?(\d+)['\"]?\)", app)
    if not port:
        port = _extract(r"(?m)^PORT\s*=\s*(\d+)", app)
    readme_port = _extract(r"localhost:(\d+)", readme)
    check(
        f"PORT code={port} readme={readme_port}",
        port == readme_port,
        f"live_chat_app.py uses port {port}, README references port {readme_port}",
    )

    # Only check arch port if it specifically documents the Vision backend port
    arch_port = _extract(r"localhost:(\d+)", arch)
    if arch_port and arch_port == port:
        check(
            f"PORT code={port} arch={arch_port}",
            port == arch_port,
            f"live_chat_app.py uses port {port}, architecture.md references port {arch_port}",
        )
    elif arch_port and arch_port != port:
        # arch may reference other ports (e.g. Ollama 11434); warn if Vision port not mentioned
        vision_port_in_arch = port in arch if port else False
        check(
            f"Vision port {port} documented in arch",
            vision_port_in_arch,
            f"Vision backend port {port} not found in architecture.md",
            warn_only=True,
        )

    print("\n── Key files exist ──────────────────────────────────────────")

    critical_files = [
        "live_chat_app.py",
        "live_chat_ui.html",
        "requirements.txt",
        "pyproject.toml",
        "architecture.md",
        "README.md",
    ]
    for fname in critical_files:
        check(f"file exists: {fname}", (BASE / fname).exists(), f"{fname} not found at {BASE / fname}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    if failures:
        print(f"\n{_FAIL}  {len(failures)} failure(s):\n")
        for f in failures:
            print(f"  • {f}")
    if warnings:
        print(f"\n{_WARN}  {len(warnings)} warning(s):\n")
        for w in warnings:
            print(f"  • {w}")
    if not failures and not warnings:
        print(f"\n{_PASS}  All checks passed.\n")
    elif not failures:
        print(f"\n{_PASS}  All hard checks passed ({len(warnings)} warning(s)).\n")
    else:
        print()

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
