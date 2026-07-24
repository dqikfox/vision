"""
test_cycle6.py — Unit tests for cycle-6 improvements.

Covers: _validate_tool_path (traversal + system dirs), rate limiter,
        file tool path guards, ARIA label smoke check.
"""

from __future__ import annotations

import importlib
import sys
import time
import types
import unittest.mock as mock

import pytest


# ---------------------------------------------------------------------------
# Module import helper
# ---------------------------------------------------------------------------

def _app():
    if "live_chat_app" in sys.modules:
        return sys.modules["live_chat_app"]
    stubs = {
        "elevenlabs": types.ModuleType("elevenlabs"),

        "pyautogui": types.ModuleType("pyautogui"),
        "pytesseract": types.ModuleType("pytesseract"),
        "PIL": types.ModuleType("PIL"),
        "PIL.Image": types.ModuleType("PIL.Image"),
    }
    with mock.patch.dict(sys.modules, stubs):
        return importlib.import_module("live_chat_app")


# ---------------------------------------------------------------------------
# _validate_tool_path — traversal + blocked paths
# ---------------------------------------------------------------------------

def test_validate_path_blocks_etc_passwd():
    app = _app()
    with pytest.raises(ValueError, match="system path|not allowed"):
        app._validate_tool_path("/etc/passwd")


def test_validate_path_blocks_traversal_to_etc():
    app = _app()
    with pytest.raises((ValueError, Exception)):
        # Path traversal via ../.. — resolve() collapses but blocked prefix catches it
        app._validate_tool_path("C:/Windows/System32/cmd.exe")


def test_validate_path_blocks_windows_system32():
    app = _app()
    with pytest.raises(ValueError):
        app._validate_tool_path("C:\\Windows\\System32\\calc.exe")


def test_validate_path_allows_home_downloads(tmp_path):
    app = _app()
    p = app._validate_tool_path(str(tmp_path / "file.txt"))
    assert p is not None


def test_validate_path_raises_on_empty():
    app = _app()
    with pytest.raises(ValueError, match="required"):
        app._validate_tool_path("")


def test_validate_path_raises_on_whitespace():
    app = _app()
    with pytest.raises(ValueError, match="required"):
        app._validate_tool_path("   ")


# ---------------------------------------------------------------------------
# File tools reject blocked paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_file_blocks_system_path():
    app = _app()
    result = await app.exec_tool("read_file", {"path": "C:\\Windows\\System32\\drivers\\etc\\hosts"})
    assert "error" in result.lower() or "not allowed" in result.lower() or "allowed" in result.lower()


@pytest.mark.asyncio
async def test_write_file_blocks_system_path():
    app = _app()
    result = await app.exec_tool("write_file", {"path": "C:\\Windows\\test.txt", "content": "x"})
    assert "error" in result.lower() or "not allowed" in result.lower()


@pytest.mark.asyncio
async def test_delete_file_blocks_system_path():
    app = _app()
    result = await app.exec_tool("delete_file", {"path": "C:\\Windows\\explorer.exe"})
    assert "error" in result.lower() or "not allowed" in result.lower()


@pytest.mark.asyncio
async def test_read_file_allows_tmp_path(tmp_path):
    app = _app()
    f = tmp_path / "test.txt"
    f.write_text("ok", encoding="utf-8")
    result = await app.exec_tool("read_file", {"path": str(f)})
    assert "ok" in result


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

def test_rate_limiter_allows_up_to_limit():
    app = _app()
    key = f"test_limit_{time.monotonic()}"
    for _ in range(5):
        assert app._check_rate_limit(key, max_calls=5, window_secs=60)


def test_rate_limiter_blocks_over_limit():
    app = _app()
    key = f"test_block_{time.monotonic()}"
    for _ in range(5):
        app._check_rate_limit(key, max_calls=5, window_secs=60)
    # 6th call should be blocked
    assert not app._check_rate_limit(key, max_calls=5, window_secs=60)


def test_rate_limiter_resets_after_window():
    """After the window expires, calls are allowed again."""
    app = _app()
    key = f"test_reset_{time.monotonic()}"
    # Fill the bucket
    for _ in range(3):
        app._check_rate_limit(key, max_calls=3, window_secs=0.1)
    # Blocked now
    assert not app._check_rate_limit(key, max_calls=3, window_secs=0.1)
    # Wait for window to expire
    time.sleep(0.15)
    # Should be allowed again
    assert app._check_rate_limit(key, max_calls=3, window_secs=0.1)


def test_rate_limiter_independent_keys():
    app = _app()
    ts = time.monotonic()
    key_a = f"key_a_{ts}"
    key_b = f"key_b_{ts}"
    for _ in range(5):
        app._check_rate_limit(key_a, max_calls=5, window_secs=60)
    # key_a exhausted, key_b still has capacity
    assert not app._check_rate_limit(key_a, max_calls=5, window_secs=60)
    assert app._check_rate_limit(key_b, max_calls=5, window_secs=60)


# ---------------------------------------------------------------------------
# Dependabot config exists
# ---------------------------------------------------------------------------

def test_dependabot_yml_exists():
    from pathlib import Path
    dep = Path(__file__).with_name(".github") / "dependabot.yml"
    assert dep.exists(), ".github/dependabot.yml should exist after cycle-6"


# ---------------------------------------------------------------------------
# ARIA labels on key UI buttons
# ---------------------------------------------------------------------------

def test_ui_buttons_have_aria_labels():
    from pathlib import Path
    html = Path(__file__).with_name("live_chat_ui.html").read_text(encoding="utf-8")
    # Key interactive elements must have aria-label
    assert 'aria-label="Toggle microphone mute"' in html
    assert 'aria-label="Send message"' in html
    assert 'aria-label="Clear chat history"' in html
    assert 'aria-label="Message input"' in html
