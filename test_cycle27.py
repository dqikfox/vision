"""
test_cycle27.py — Structural tests for cycle-27 improvements

Tests verify:
1. handle_input WS tasks use _tracked_task (not bare asyncio.create_task)
2. _make_tool_handler snapshots _main_loop to avoid TOCTOU shutdown race
3. voice_cli _tts_worker has no compound semicolon statements
"""

import re

APP = "live_chat_app.py"
CLI = "voice_cli.py"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. handle_input WS dispatch — must use _tracked_task
# ---------------------------------------------------------------------------


def test_handle_input_dispatch_uses_tracked_task():
    src = _read(APP)
    bare = list(re.finditer(r"asyncio\.create_task\(handle_input\(", src))
    assert not bare, (
        f"Found {len(bare)} bare asyncio.create_task(handle_input(...)) calls — "
        "must use _tracked_task() so exceptions are logged"
    )


def test_handle_input_tracked_task_count():
    src = _read(APP)
    tracked = list(re.finditer(r"_tracked_task\(handle_input\(", src))
    assert len(tracked) >= 2, (
        f"Expected at least 2 _tracked_task(handle_input(...)) in WS handler "
        f"(message + input msg types), found {len(tracked)}"
    )


# ---------------------------------------------------------------------------
# 2. _make_tool_handler — snapshot _main_loop to avoid TOCTOU race
# ---------------------------------------------------------------------------


def test_make_tool_handler_snapshots_main_loop():
    src = _read(APP)
    fn = re.search(
        r"def _make_tool_handler\(.*?(?=\ndef |\nclass |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_make_tool_handler not found"
    body = fn.group()
    # Must assign _main_loop to a local variable before using it
    assert "loop = _main_loop" in body or "local_loop = _main_loop" in body, (
        "_make_tool_handler must snapshot _main_loop to a local variable "
        "to avoid TOCTOU race during server shutdown"
    )


def test_make_tool_handler_handles_runtime_error():
    src = _read(APP)
    fn = re.search(
        r"def _make_tool_handler\(.*?(?=\ndef |\nclass |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "RuntimeError" in body, (
        "_make_tool_handler must catch RuntimeError from run_coroutine_threadsafe "
        "on a closed/None event loop"
    )


def test_make_tool_handler_no_bare_main_loop_in_run():
    src = _read(APP)
    fn = re.search(
        r"def _make_tool_handler\(.*?(?=\ndef |\nclass |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # run_coroutine_threadsafe must NOT use _main_loop directly (use snapshot)
    assert "run_coroutine_threadsafe(exec_tool" in body, "exec_tool dispatch must exist"
    # The direct _main_loop reference in the run call should be gone
    assert "run_coroutine_threadsafe(exec_tool(tool_name, params), _main_loop)" not in body, (
        "run_coroutine_threadsafe must use a local snapshot of _main_loop, "
        "not the global directly"
    )


# ---------------------------------------------------------------------------
# 3. voice_cli _tts_worker — no compound semicolon statements
# ---------------------------------------------------------------------------


def test_tts_worker_no_compound_statements():
    src = _read(CLI)
    fn = re.search(
        r"def _tts_worker\(.*?(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_tts_worker not found in voice_cli.py"
    body = fn.group()
    # Look for semicolon on non-comment lines
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert ";" not in stripped, (
            f"_tts_worker contains compound statement: {stripped!r} — "
            "split onto separate lines for clarity"
        )
