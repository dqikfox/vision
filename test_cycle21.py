"""
test_cycle21.py — Structural tests for cycle-21 improvements

Tests verify:
1. live_chat_ui.html ws.onmessage wraps JSON.parse in try-catch
2. Unreachable second 'except Exception' block removed from Ollama CLI list
3. _activate_provider() validates provider is in PROVIDERS before switching
"""

import re

import pytest


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


APP = "live_chat_app.py"
UI = "live_chat_ui.html"


# ---------------------------------------------------------------------------
# 1. UI — ws.onmessage wraps JSON.parse in try-catch
# ---------------------------------------------------------------------------


def test_ws_onmessage_has_try_catch():
    """ws.onmessage must wrap JSON.parse in try-catch to survive malformed frames."""
    src = _read(UI)
    # Find the onmessage handler block
    block = re.search(
        r"ws\.onmessage\s*=.*?(?=\n\s*\n|\n\s*ws\.|\nfunction )",
        src,
        re.DOTALL,
    )
    assert block is not None, "ws.onmessage handler not found"
    body = block.group()
    assert "try" in body, "ws.onmessage must wrap JSON.parse in a try block"
    assert "catch" in body, "ws.onmessage must have a catch handler for parse errors"


def test_ws_onmessage_not_bare_parse():
    """ws.onmessage must not call JSON.parse without error handling."""
    src = _read(UI)
    # The old bare one-liner pattern must be gone
    assert "=> handleMsg(JSON.parse(e.data));" not in src, (
        "ws.onmessage must not call JSON.parse without a try-catch wrapper"
    )


def test_ws_onmessage_logs_parse_error():
    """ws.onmessage catch block must log the error (console.error or write_log)."""
    src = _read(UI)
    block = re.search(
        r"ws\.onmessage\s*=.*?(?=\n\s*\n|\n\s*ws\.|\nfunction )",
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "console.error" in body or "console.warn" in body, (
        "ws.onmessage catch block must log the parse error for debugging"
    )


# ---------------------------------------------------------------------------
# 2. Ollama CLI list — no unreachable except block
# ---------------------------------------------------------------------------


def test_ollama_cli_list_no_duplicate_except():
    """Ollama CLI list try block must have exactly one except clause."""
    src = _read(APP)
    # Find the try block that calls run_in_executor(_list_via_cli)
    try_block = re.search(
        r"try:\s+return await loop\.run_in_executor\(None, _list_via_cli\).*?(?=\n\s*\n|\n\nasync def |\n\ndef )",
        src,
        re.DOTALL,
    )
    assert try_block is not None, "try block calling _list_via_cli not found"
    body = try_block.group()
    except_count = body.count("except Exception")
    assert except_count == 1, (
        f"Expected exactly 1 'except Exception' block, found {except_count}"
    )


def test_ollama_cli_no_bare_except_after_named():
    """The bare 'except Exception:' with no body after a named one must be removed."""
    src = _read(APP)
    # The dead-code pattern: except Exception as e: ... return [] \n except Exception: \n return []
    dead_pattern = re.search(
        r"except Exception as e:.*?return \[\]\s+except Exception:\s+return \[\]",
        src,
        re.DOTALL,
    )
    assert dead_pattern is None, (
        "Found unreachable 'except Exception: return []' block after named except handler"
    )


# ---------------------------------------------------------------------------
# 3. _activate_provider() — provider validation
# ---------------------------------------------------------------------------


def test_activate_provider_validates_provider():
    """_activate_provider() must reject unknown provider names before mutating state."""
    src = _read(APP)
    fn = re.search(
        r"async def _activate_provider\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_activate_provider() not found"
    body = fn.group()
    assert "not in PROVIDERS" in body or "PROVIDERS" in body, (
        "_activate_provider() must check that provider is a known PROVIDERS key"
    )


def test_activate_provider_returns_early_on_unknown():
    """_activate_provider() must return early (not mutate state) for unknown providers."""
    src = _read(APP)
    fn = re.search(
        r"async def _activate_provider\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # 'not in PROVIDERS' should appear BEFORE the _global_state_lock block
    providers_check_pos = body.find("not in PROVIDERS")
    lock_pos = body.find("_global_state_lock")
    assert providers_check_pos != -1, "PROVIDERS membership check not found"
    assert lock_pos != -1, "_global_state_lock block not found"
    assert providers_check_pos < lock_pos, (
        "Provider validation must occur before acquiring _global_state_lock"
    )


def test_activate_provider_logs_unknown():
    """_activate_provider() must log unknown provider names for debugging."""
    src = _read(APP)
    fn = re.search(
        r"async def _activate_provider\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "write_log" in body or "print(" in body, (
        "_activate_provider() must log unknown provider names"
    )
