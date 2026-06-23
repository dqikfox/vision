"""
test_cycle17.py — Structural tests for cycle-17 improvements

Tests verify:
1. muted/mode assignments protected by _global_state_lock in WebSocket handler
2. set_state() protects runtime_state with _global_state_lock
3. transcribe() initializes path=None before use; guards os.unlink with 'if path'
4. broadcast() wraps individual sends in asyncio.wait_for(timeout=5.0)
5. max_examples bounded to 10,000 in both /api/rag/export-training and tool handler
"""

import re


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


APP = "live_chat_app.py"


# ---------------------------------------------------------------------------
# 1. muted/mode assignments under _global_state_lock
# ---------------------------------------------------------------------------


def test_mute_handler_uses_lock():
    """'muted = msg.get(...)' in t == 'mute' block must be inside _global_state_lock."""
    src = _read(APP)
    # Find the 't == "mute"' block and verify the lock wraps the assignment
    block = re.search(
        r'if t == "mute".*?elif t == "mode"',
        src,
        re.DOTALL,
    )
    assert block is not None, "Could not find 't == mute' block"
    assert "_global_state_lock" in block.group(), (
        "muted assignment in 't == mute' block must use _global_state_lock"
    )


def test_mode_handler_uses_lock():
    """'mode = msg.get(...)' in t == 'mode' block must be inside _global_state_lock."""
    src = _read(APP)
    block = re.search(
        r'elif t == "mode".*?elif t == "text"',
        src,
        re.DOTALL,
    )
    assert block is not None, "Could not find 't == mode' block"
    assert "_global_state_lock" in block.group(), (
        "mode assignment in 't == mode' block must use _global_state_lock"
    )


def test_set_mute_handler_uses_lock():
    """'muted = msg.get(...)' in t == 'set_mute' block must be inside _global_state_lock."""
    src = _read(APP)
    block = re.search(
        r'elif t == "set_mute".*?elif t == "set_continuous"',
        src,
        re.DOTALL,
    )
    assert block is not None, "Could not find 't == set_mute' block"
    assert "_global_state_lock" in block.group(), (
        "muted assignment in 't == set_mute' block must use _global_state_lock"
    )


def test_set_mode_handler_uses_lock():
    """'mode = msg.get(...)' in t == 'set_mode' block must be inside _global_state_lock."""
    src = _read(APP)
    block = re.search(
        r'elif t == "set_mode".*?elif t == "clear"',
        src,
        re.DOTALL,
    )
    assert block is not None, "Could not find 't == set_mode' block"
    assert "_global_state_lock" in block.group(), (
        "mode assignment in 't == set_mode' block must use _global_state_lock"
    )


# ---------------------------------------------------------------------------
# 2. set_state() protects runtime_state
# ---------------------------------------------------------------------------


def test_set_state_locks_runtime_state():
    """set_state() must acquire _global_state_lock before assigning runtime_state."""
    src = _read(APP)
    fn = re.search(
        r"async def set_state\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None, "set_state() not found"
    body = fn.group()
    lock_pos = body.find("_global_state_lock")
    assign_pos = body.find("runtime_state =")
    assert lock_pos != -1, "set_state() must reference _global_state_lock"
    assert assign_pos != -1, "set_state() must assign runtime_state"
    assert lock_pos < assign_pos, (
        "Lock must be acquired before runtime_state assignment in set_state()"
    )


# ---------------------------------------------------------------------------
# 3. transcribe() path safety
# ---------------------------------------------------------------------------


def test_transcribe_path_initialized_to_none():
    """transcribe() must initialize 'path' to None before the try block."""
    src = _read(APP)
    fn = re.search(
        r"async def transcribe\(.*?(?=\nasync def |\n# ──)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "transcribe() not found"
    body = fn.group()
    assert "path: str | None = None" in body or "path = None" in body, (
        "transcribe() must initialise path=None before creating the temp file"
    )


def test_transcribe_path_assigned_before_write():
    """path should be assigned from f.name before wavfile.write to avoid undefined path on write error."""
    src = _read(APP)
    fn = re.search(
        r"async def transcribe\(.*?(?=\nasync def |\n# ──)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    path_assign_pos = body.find("path = f.name")
    write_pos = body.find("wavfile.write(path")
    assert path_assign_pos != -1, "path = f.name not found in transcribe()"
    assert write_pos != -1, "wavfile.write(path, ...) not found — should use 'path' not 'f.name'"
    assert path_assign_pos < write_pos, (
        "path must be assigned before wavfile.write so cleanup can run on write failure"
    )


def test_transcribe_unlink_guarded():
    """os.unlink in transcribe() finally block must be conditional on 'if path'."""
    src = _read(APP)
    fn = re.search(
        r"async def transcribe\(.*?(?=\nasync def |\n# ──)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # find the finally block
    finally_block = re.search(r"finally:.*", body, re.DOTALL)
    assert finally_block is not None, "No finally block in transcribe()"
    finally_text = finally_block.group()
    assert "if path:" in finally_text or "if path\n" in finally_text, (
        "os.unlink in finally block must be guarded by 'if path:'"
    )


# ---------------------------------------------------------------------------
# 4. broadcast() per-client send timeout
# ---------------------------------------------------------------------------


def test_broadcast_send_has_timeout():
    """broadcast() must use asyncio.wait_for with a timeout for each WS send."""
    src = _read(APP)
    fn = re.search(
        r"async def broadcast\(.*?(?=\nasync def set_state)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "broadcast() not found"
    body = fn.group()
    assert "asyncio.wait_for" in body, (
        "broadcast() must use asyncio.wait_for to timeout slow WS sends"
    )
    # Verify a numeric timeout
    timeout_match = re.search(r"wait_for\(.*?timeout=(\d+\.?\d*)", body, re.DOTALL)
    assert timeout_match is not None, "asyncio.wait_for must specify a numeric timeout"
    timeout_val = float(timeout_match.group(1))
    assert 1.0 <= timeout_val <= 30.0, (
        f"broadcast() send timeout should be between 1 and 30 seconds, got {timeout_val}"
    )


def test_broadcast_catches_timeout_error():
    """broadcast() must catch asyncio.TimeoutError to remove slow/hung clients."""
    src = _read(APP)
    fn = re.search(
        r"async def broadcast\(.*?(?=\nasync def set_state)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "TimeoutError" in body or "asyncio.TimeoutError" in body, (
        "broadcast() must explicitly catch asyncio.TimeoutError (or Exception superset)"
    )


# ---------------------------------------------------------------------------
# 5. max_examples bounded in both call sites
# ---------------------------------------------------------------------------


def test_api_rag_export_max_examples_bounded():
    """api_rag_export_training endpoint must cap max_examples to avoid OOM."""
    src = _read(APP)
    ep = re.search(
        r"async def api_rag_export_training\(.*?(?=\n@app\.|\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert ep is not None, "api_rag_export_training not found"
    body = ep.group()
    assert "10_000" in body or "10000" in body, (
        "api_rag_export_training must cap max_examples at 10,000"
    )
    assert "min(" in body, "Should use min() to cap the value"


def test_tool_handler_max_examples_bounded():
    """kb_export_training_data tool handler must cap max_examples."""
    src = _read(APP)
    block = re.search(
        r'elif name == "kb_export_training_data".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None, "kb_export_training_data handler not found"
    body = block.group()
    assert "10_000" in body or "10000" in body, (
        "kb_export_training_data tool must cap max_examples at 10,000"
    )
    assert "min(" in body, "Should use min() to cap the value"
