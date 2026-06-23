"""
test_cycle18.py — Structural tests for cycle-18 improvements

Tests verify:
1. voice_cli.py _speak_eleven() uses -ArgumentList for fname (no f-string injection)
2. _set_request_lane_busy() uses threading.Lock (_request_lane_lock)
3. ElevenLabs audio stream (out) initialised to None; close guarded by 'if out is not None'
4. write_file tool uses asyncio.wait_for timeout + _tool_err
5. Voice supervisor uses exponential backoff (capped at 30s)
6. live_chat_ui.html voice radio shortName wrapped in escHtml()
"""

import re


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


APP = "live_chat_app.py"
CLI = "voice_cli.py"
UI = "live_chat_ui.html"


# ---------------------------------------------------------------------------
# 1. voice_cli.py _speak_eleven — no f-string fname injection
# ---------------------------------------------------------------------------


def test_speak_eleven_no_fname_fstring():
    """_speak_eleven() must not interpolate fname directly into the PowerShell string."""
    src = _read(CLI)
    fn = re.search(
        r"def _speak_eleven\(.*?(?=\ndef |\nclass |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_speak_eleven() not found"
    body = fn.group()
    # Old pattern: f"$p.Open([uri]'{fname}')"
    assert "uri]'{fname}'" not in body, (
        "_speak_eleven() must not interpolate fname into PowerShell URI string"
    )


def test_speak_eleven_uses_argument_list():
    """_speak_eleven() PowerShell fallback must pass fname via -ArgumentList."""
    src = _read(CLI)
    fn = re.search(
        r"def _speak_eleven\(.*?(?=\ndef |\nclass |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "-ArgumentList" in body, (
        "_speak_eleven() must use -ArgumentList to pass the filename safely"
    )
    assert "$args[0]" in body, (
        "_speak_eleven() PowerShell script must reference $args[0] for the filename"
    )


# ---------------------------------------------------------------------------
# 2. _set_request_lane_busy — threading.Lock
# ---------------------------------------------------------------------------


def test_request_lane_lock_defined():
    """_request_lane_lock must be defined as threading.Lock() at module level."""
    src = _read(APP)
    assert "_request_lane_lock" in src, "_request_lane_lock must be defined"
    assert "threading.Lock()" in src, "_request_lane_lock must be a threading.Lock()"


def test_set_request_lane_busy_uses_lock():
    """_set_request_lane_busy() must acquire _request_lane_lock."""
    src = _read(APP)
    fn = re.search(
        r"def _set_request_lane_busy\(.*?(?=\ndef |\nasync def |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_set_request_lane_busy not found"
    body = fn.group()
    assert "_request_lane_lock" in body, (
        "_set_request_lane_busy() must use _request_lane_lock"
    )
    assert "with _request_lane_lock:" in body, (
        "_set_request_lane_busy() must acquire lock via context manager"
    )


# ---------------------------------------------------------------------------
# 3. ElevenLabs audio stream — None guard on out.close()
# ---------------------------------------------------------------------------


def test_eleven_out_initialized_to_none():
    """The sd.OutputStream variable must be initialised to None before creation."""
    src = _read(APP)
    # We look for the pattern: out: sd.OutputStream | None = None
    assert "out: sd.OutputStream | None = None" in src, (
        "ElevenLabs out stream must be typed and initialised to None before sd.OutputStream()"
    )


def test_eleven_out_close_guarded():
    """out.close() must be guarded by 'if out is not None:' to avoid NameError."""
    src = _read(APP)
    # Find the ElevenLabs stream section
    region = re.search(
        r"out: sd\.OutputStream.*?(?=\nasync def |\n# ──)",
        src,
        re.DOTALL,
    )
    assert region is not None, "ElevenLabs out stream section not found"
    body = region.group()
    assert "if out is not None:" in body, (
        "out.close() must be guarded by 'if out is not None:'"
    )


# ---------------------------------------------------------------------------
# 4. write_file — asyncio.wait_for timeout + _tool_err
# ---------------------------------------------------------------------------


def test_write_file_uses_wait_for():
    """write_file tool handler must use asyncio.wait_for with a timeout."""
    src = _read(APP)
    block = re.search(
        r'elif name == "write_file".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None, "write_file handler not found"
    body = block.group()
    assert "asyncio.wait_for" in body, (
        "write_file must use asyncio.wait_for to timeout long writes"
    )
    timeout_match = re.search(r"wait_for\(.*?timeout=(\d+\.?\d*)", body, re.DOTALL)
    assert timeout_match is not None, "asyncio.wait_for must specify numeric timeout"
    assert float(timeout_match.group(1)) >= 5.0, "write_file timeout should be ≥5s"


def test_write_file_uses_tool_err():
    """write_file tool handler must use _tool_err() for error reporting."""
    src = _read(APP)
    block = re.search(
        r'elif name == "write_file".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "_tool_err(" in body, (
        'write_file must use _tool_err() not bare f"Error writing {fpath}: {e}"'
    )


# ---------------------------------------------------------------------------
# 5. Voice supervisor — exponential backoff
# ---------------------------------------------------------------------------


def test_voice_supervisor_has_backoff():
    """_voice_supervisor() must implement exponential backoff on crash."""
    src = _read(APP)
    fn = re.search(
        r"async def _voice_supervisor\(.*?(?=\n    async def |\n    _tracked_task)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_voice_supervisor not found"
    body = fn.group()
    # Should have a growing backoff
    assert "backoff" in body, "_voice_supervisor() must use a 'backoff' variable"
    assert "backoff * 2" in body or "backoff *= 2" in body, (
        "backoff must double on each crash"
    )


def test_voice_supervisor_backoff_capped():
    """_voice_supervisor() backoff must be capped to prevent runaway sleep."""
    src = _read(APP)
    fn = re.search(
        r"async def _voice_supervisor\(.*?(?=\n    async def |\n    _tracked_task)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "min(" in body, "backoff must be capped with min()"
    cap_match = re.search(r"min\(.*?(\d+)\.0", body)
    assert cap_match is not None, "backoff cap value must be a float"
    cap_val = int(cap_match.group(1))
    assert 10 <= cap_val <= 60, f"backoff cap should be 10–60s, got {cap_val}"


def test_voice_supervisor_resets_backoff_on_clean_exit():
    """_voice_supervisor() must reset backoff after a successful voice_loop() run."""
    src = _read(APP)
    fn = re.search(
        r"async def _voice_supervisor\(.*?(?=\n    async def |\n    _tracked_task)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "backoff = 2" in body or "backoff = 1" in body, (
        "_voice_supervisor() must reset backoff to initial value after clean voice_loop exit"
    )


# ---------------------------------------------------------------------------
# 6. UI — voice radio shortName wrapped in escHtml()
# ---------------------------------------------------------------------------


def test_voice_radio_short_name_escaped():
    """Voice radio option labels must use escHtml(shortName) to prevent XSS."""
    src = _read(UI)
    # Must not have raw ${shortName} in template literal
    assert "${shortName}" not in src, (
        "Voice radio label must use escHtml(shortName), not bare ${shortName}"
    )
    assert "${escHtml(shortName)}" in src, (
        "Voice radio label must use escHtml(shortName) to prevent XSS"
    )
