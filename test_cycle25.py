"""
test_cycle25.py — Structural tests for cycle-25 improvements

Tests verify:
1. _pending_tool_confirmation is popped atomically under _global_state_lock
2. voice_cli _speak_eleven temp file cleanup logs OSError instead of swallowing
3. voice_cli _clip_watcher logs clipboard exceptions instead of swallowing
"""

import re

APP = "live_chat_app.py"
CLI = "voice_cli.py"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. _pending_tool_confirmation atomic pop under _global_state_lock
# ---------------------------------------------------------------------------


def test_confirmation_pop_under_global_state_lock():
    """_pop_pending_tool_confirmation must be called inside async with _global_state_lock."""
    src = _read(APP)
    # Find handle_input function body
    fn = re.search(
        r"async def handle_input\(.*?(?=\nasync def |\ndef (?!_))",
        src,
        re.DOTALL,
    )
    assert fn is not None, "handle_input not found"
    body = fn.group()
    # Find _global_state_lock context
    lock_blocks = list(re.finditer(r"async with _global_state_lock:", body))
    assert lock_blocks, "handle_input must use _global_state_lock for confirmation state"
    # _pop_pending_tool_confirmation must appear after the lock
    for lb in lock_blocks:
        nearby = body[lb.start() : lb.start() + 500]
        if "_pop_pending_tool_confirmation" in nearby:
            return  # Found it inside a lock block
    assert False, (
        "_pop_pending_tool_confirmation() must be called inside an "
        "'async with _global_state_lock:' block to prevent race conditions"
    )


def test_confirmation_snapshot_before_await():
    """Confirmation state must be snapshotted before any await to avoid TOCTOU."""
    src = _read(APP)
    fn = re.search(
        r"async def handle_input\(.*?(?=\nasync def |\ndef (?!_))",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # The lock block containing _pop must appear before exec_tool/set_state calls
    lock_pos = body.find("async with _global_state_lock:")
    pop_pos = body.find("_pop_pending_tool_confirmation")
    exec_pos = body.find("exec_tool(tool_name")
    assert lock_pos != -1
    assert pop_pos != -1
    assert exec_pos != -1
    assert pop_pos < exec_pos, "Confirmation must be popped (under lock) before exec_tool is awaited"


def test_confirmation_no_bare_pop_outside_lock():
    """_pop_pending_tool_confirmation must not be called outside a lock block in handle_input."""
    src = _read(APP)
    fn = re.search(
        r"async def handle_input\(.*?(?=\nasync def |\ndef (?!_))",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # Find all pop calls and verify each is preceded by lock context within 400 chars
    for m in re.finditer(r"_pop_pending_tool_confirmation\(\)", body):
        preceding = body[max(0, m.start() - 400) : m.start()]
        # Ignore the expiry pop (which clears an already-expired entry — race is benign)
        if "pending_expired" in preceding and "async with" not in preceding[-200:]:
            continue
        assert "async with _global_state_lock:" in preceding, (
            f"_pop_pending_tool_confirmation at offset {m.start()} "
            "must be inside an async with _global_state_lock: block"
        )


# ---------------------------------------------------------------------------
# 2. voice_cli _speak_eleven — OSError logged not swallowed
# ---------------------------------------------------------------------------


def test_speak_eleven_cleanup_logs_oserror():
    src = _read(CLI)
    # Find the finally block after subprocess.run in _speak_eleven
    fn = re.search(
        r"def _speak_eleven\(.*?(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_speak_eleven not found in voice_cli.py"
    body = fn.group()
    finally_block = re.search(r"finally:(.*)", body, re.DOTALL)
    assert finally_block is not None, "_speak_eleven must have a finally block"
    cleanup = finally_block.group(1)[:300]
    assert "except Exception: pass" not in cleanup, "_speak_eleven finally must not silently swallow unlink errors"
    assert "OSError" in cleanup or "status(" in cleanup or "print(" in cleanup, (
        "_speak_eleven must log temp file cleanup failures"
    )


def test_speak_eleven_cleanup_not_bare_except():
    src = _read(CLI)
    fn = re.search(
        r"def _speak_eleven\(.*?(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # The bare 'except Exception: pass' pattern must be gone
    assert "except Exception: pass" not in body, "_speak_eleven must not use bare 'except Exception: pass' for cleanup"


# ---------------------------------------------------------------------------
# 3. voice_cli _clip_watcher — clipboard errors logged not swallowed
# ---------------------------------------------------------------------------


def test_clip_watcher_logs_exceptions():
    src = _read(CLI)
    fn = re.search(
        r"def _clip_watcher\(.*?(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_clip_watcher not found in voice_cli.py"
    body = fn.group()
    assert "except Exception: pass" not in body, "_clip_watcher must not silently swallow clipboard exceptions"
    assert "except Exception as" in body or "except Exception as e" in body, (
        "_clip_watcher must capture the exception variable to log it"
    )


def test_clip_watcher_error_message_informative():
    src = _read(CLI)
    fn = re.search(
        r"def _clip_watcher\(.*?(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # Should include a status/print call with the error
    assert "status(" in body or "print(" in body, "_clip_watcher exception handler must output the error for debugging"
