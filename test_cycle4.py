"""
test_cycle4.py — Unit tests for cycle-4 improvements.

Covers: browser_open SSRF validation, execute_python large-output guard,
        /api/export/trace endpoint, bare-except cleanup in voice_cli.
"""

from __future__ import annotations

import importlib
import sys
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
        "elevenlabs.client": types.ModuleType("elevenlabs.client"),
        "pyautogui": types.ModuleType("pyautogui"),
        "pytesseract": types.ModuleType("pytesseract"),
        "PIL": types.ModuleType("PIL"),
        "PIL.Image": types.ModuleType("PIL.Image"),
    }
    with mock.patch.dict(sys.modules, stubs):
        return importlib.import_module("live_chat_app")


# ---------------------------------------------------------------------------
# browser_open — SSRF validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_browser_open_rejects_file_scheme():
    app = _app()
    result = await app.exec_tool("browser_open", {"url": "file:///etc/passwd"})
    assert "error" in result.lower() or "only http" in result.lower(), f"file:// should be blocked, got: {result!r}"


@pytest.mark.asyncio
async def test_browser_open_rejects_javascript_scheme():
    app = _app()
    result = await app.exec_tool("browser_open", {"url": "javascript:alert(1)"})
    assert "error" in result.lower() or "only http" in result.lower()


@pytest.mark.asyncio
async def test_browser_open_rejects_localhost():
    app = _app()
    result = await app.exec_tool("browser_open", {"url": "http://localhost/admin"})
    assert "blocked" in result.lower() or "ssrf" in result.lower() or "error" in result.lower()


@pytest.mark.asyncio
async def test_browser_open_rejects_127_0_0_1():
    app = _app()
    result = await app.exec_tool("browser_open", {"url": "http://127.0.0.1:8080/secret"})
    assert "blocked" in result.lower() or "ssrf" in result.lower() or "error" in result.lower()


@pytest.mark.asyncio
async def test_browser_open_allows_https(monkeypatch):
    """https://example.com should pass URL validation (browser call mocked)."""
    app = _app()

    async def _fake_goto(url, **kw):
        return None

    class _FakePage:
        goto = _fake_goto

    async def _fake_get_browser_page():
        return _FakePage()

    monkeypatch.setattr(app, "get_browser_page", _fake_get_browser_page)
    result = await app.exec_tool("browser_open", {"url": "https://example.com"})
    assert "opened" in result.lower() or "example.com" in result.lower()


# ---------------------------------------------------------------------------
# execute_python — large output guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_python_truncates_large_output():
    """Code that prints a lot should have output capped at 4000 chars."""
    app = _app()
    code = "print('x' * 10000)"
    result = await app.exec_tool("execute_python", {"code": code, "timeout": "10"})
    assert len(result) <= 4100, f"Output too long ({len(result)} chars)"


@pytest.mark.asyncio
async def test_execute_python_respects_timeout():
    """Infinite loop should time out, not hang forever."""
    app = _app()
    result = await app.exec_tool("execute_python", {"code": "while True: pass", "timeout": "2"})
    assert "timed out" in result.lower() or "timeout" in result.lower()


# ---------------------------------------------------------------------------
# /api/export/trace — trace export endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_trace_returns_404_when_no_log(tmp_path, monkeypatch):
    app = _app()
    fake_log = tmp_path / "missing_log.log"
    monkeypatch.setattr(app, "LOG_FILE", fake_log)
    resp = await app.api_export_trace()
    # Should return JSONResponse with 404 status when log doesn't exist
    assert hasattr(resp, "status_code")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_trace_returns_file_when_log_exists(tmp_path, monkeypatch):
    app = _app()
    log = tmp_path / "chat_events.log"
    log.write_text("event1\nevent2\n", encoding="utf-8")
    monkeypatch.setattr(app, "LOG_FILE", log)
    resp = await app.api_export_trace()
    # FileResponse — check media_type and path
    from fastapi.responses import FileResponse

    assert isinstance(resp, FileResponse)
    assert "text" in resp.media_type


# ---------------------------------------------------------------------------
# voice_cli — bare except cleanup (import-level smoke test)
# ---------------------------------------------------------------------------


def test_voice_cli_imports_without_syntax_error():
    """voice_cli.py should parse correctly after bare-except cleanup."""
    import ast
    from pathlib import Path

    src = Path(__file__).with_name("voice_cli.py").read_text(encoding="utf-8")
    tree = ast.parse(src)  # raises SyntaxError if broken
    # Check no bare 'except:' nodes remain (they have no exception type)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            # bare except: — fail
            raise AssertionError(f"Bare except: found at line {node.lineno} in voice_cli.py")
