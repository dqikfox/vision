"""
test_cycle3.py — Unit tests for cycle-3 improvements.

Covers: confirmation flow (required/expired/accept/cancel/conflict),
        kb_search score output, read_file/write_file/list_files async wiring,
        and clipboard async wiring.
"""

from __future__ import annotations

import asyncio
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
        "elevenlabs.client": types.ModuleType("elevenlabs"),
        "pyautogui": types.ModuleType("pyautogui"),
        "pytesseract": types.ModuleType("pytesseract"),
        "PIL": types.ModuleType("PIL"),
        "PIL.Image": types.ModuleType("PIL.Image"),
    }
    with mock.patch.dict(sys.modules, stubs):
        return importlib.import_module("live_chat_app")


# ---------------------------------------------------------------------------
# Confirmation flow tests
# ---------------------------------------------------------------------------

def _reset_confirmation(app):
    app._pending_tool_confirmation = None


def test_confirmation_required_for_delete_file():
    app = _app()
    _reset_confirmation(app)
    reason = app._tool_confirmation_reason("delete_file", {"path": "/tmp/x.txt"})
    assert reason is not None, "delete_file should require confirmation"


def test_confirmation_required_for_execute_python():
    app = _app()
    reason = app._tool_confirmation_reason("execute_python", {"code": "os.remove('x')"})
    assert reason is not None, "execute_python should require confirmation"


def test_confirmation_not_required_for_screenshot():
    app = _app()
    reason = app._tool_confirmation_reason("screenshot", {})
    assert reason is None, "screenshot should NOT require confirmation"


def test_set_pending_confirmation_returns_prompt():
    app = _app()
    _reset_confirmation(app)
    msg = app._set_pending_tool_confirmation("delete_file", {"path": "/tmp/x"}, "delete /tmp/x")
    assert "yes" in msg.lower() and "cancel" in msg.lower()
    assert app._pending_tool_confirmation is not None


def test_confirmation_not_expired_immediately():
    app = _app()
    _reset_confirmation(app)
    app._set_pending_tool_confirmation("delete_file", {"path": "/tmp/x"}, "delete /tmp/x")
    assert not app._pending_tool_confirmation_expired()


def test_confirmation_expired_after_timeout(monkeypatch):
    app = _app()
    _reset_confirmation(app)
    app._set_pending_tool_confirmation("delete_file", {"path": "/tmp/x"}, "delete /tmp/x")
    # Fake time: move created_at back by more than timeout
    timeout = app._CONFIRMATION_TIMEOUT_SECS
    app._pending_tool_confirmation["created_at"] = time.monotonic() - timeout - 1
    assert app._pending_tool_confirmation_expired()


def test_pop_pending_confirmation_clears_state():
    app = _app()
    _reset_confirmation(app)
    app._set_pending_tool_confirmation("kill_process", {"pid": "1234"}, "kill PID 1234")
    popped = app._pop_pending_tool_confirmation()
    assert popped is not None
    assert popped["name"] == "kill_process"
    assert app._pending_tool_confirmation is None


def test_confirmation_conflict_returns_existing_prompt():
    """Second set_pending while first is active returns conflict message."""
    app = _app()
    _reset_confirmation(app)
    app._set_pending_tool_confirmation("delete_file", {"path": "/tmp/a"}, "delete /tmp/a")
    msg2 = app._set_pending_tool_confirmation("kill_process", {"pid": "99"}, "kill PID 99")
    assert "pending" in msg2.lower() or "already" in msg2.lower()


# ---------------------------------------------------------------------------
# kb_search — BM25 score included in output
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kb_search_includes_score_in_output(monkeypatch):
    app = _app()

    fake_result = {
        "ok": True,
        "results": [
            {
                "rel_path": "docs/intro.md",
                "snippet": "intro snippet",
                "content": "intro content text",
                "score": 4.271,
            }
        ],
    }

    monkeypatch.setattr(app._rag_manager, "search", lambda **_kw: fake_result)

    output = await app.exec_tool("kb_search", {"query": "intro", "limit": "1"})
    assert "4.271" in output or "score" in output.lower(), (
        f"Expected score in output, got: {output!r}"
    )


@pytest.mark.asyncio
async def test_kb_search_empty_query_returns_error():
    app = _app()
    output = await app.exec_tool("kb_search", {"query": ""})
    assert "error" in output.lower() or "required" in output.lower()


@pytest.mark.asyncio
async def test_kb_search_no_results_returns_friendly_message(monkeypatch):
    app = _app()
    monkeypatch.setattr(app._rag_manager, "search", lambda **_kw: {"ok": True, "results": []})
    output = await app.exec_tool("kb_search", {"query": "nonexistent_term_xyz"})
    assert "no" in output.lower() or "match" in output.lower()


# ---------------------------------------------------------------------------
# File I/O handlers — async wiring (executor smoke test)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_file_returns_content(tmp_path):
    app = _app()
    f = tmp_path / "sample.txt"
    f.write_text("hello world", encoding="utf-8")
    result = await app.exec_tool("read_file", {"path": str(f), "encoding": "utf-8"})
    assert "hello world" in result


@pytest.mark.asyncio
async def test_write_file_creates_file(tmp_path):
    app = _app()
    f = tmp_path / "out.txt"
    result = await app.exec_tool("write_file", {"path": str(f), "content": "written", "encoding": "utf-8"})
    assert "written" in result.lower() or "7" in result
    assert f.read_text(encoding="utf-8") == "written"


@pytest.mark.asyncio
async def test_list_files_returns_entries(tmp_path):
    app = _app()
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "subdir").mkdir()
    result = await app.exec_tool("list_files", {"path": str(tmp_path), "pattern": "*"})
    assert "a.txt" in result
    assert "subdir" in result


# ---------------------------------------------------------------------------
# Clipboard handlers — async wiring (mock pyperclip)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_clipboard_calls_pyperclip_paste(monkeypatch):
    app = _app()
    fake_clip = types.ModuleType("pyperclip")
    fake_clip.paste = lambda: "clipboard_value"
    fake_clip.copy = lambda t: None
    monkeypatch.setitem(sys.modules, "pyperclip", fake_clip)
    result = await app.exec_tool("get_clipboard", {})
    assert "clipboard_value" in result


@pytest.mark.asyncio
async def test_set_clipboard_calls_pyperclip_copy(monkeypatch):
    app = _app()
    copied: list[str] = []
    fake_clip = types.ModuleType("pyperclip")
    fake_clip.paste = lambda: ""
    fake_clip.copy = lambda t: copied.append(t)
    monkeypatch.setitem(sys.modules, "pyperclip", fake_clip)
    result = await app.exec_tool("set_clipboard", {"text": "hello"})
    assert copied == ["hello"]
    assert "copied" in result.lower() or "hello" in result
