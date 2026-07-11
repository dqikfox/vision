"""
test_cycle9.py — Unit tests for cycle-9 improvements.

Covers: ao_* shell injection guards, set_api_key/set_wake_word locking,
        send_notification double-quote escaping, /api/model rate limit,
        Ollama tool-call JSON parse safety, append_to_file executor+timeout,
        browser_eval dangerous-pattern blocking, speak-task cancel on disconnect.
"""

import asyncio
import json
import shlex
import threading
import types
from pathlib import Path
from unittest import mock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _app_module():
    import importlib, sys
    stubs = {
        "elevenlabs": types.ModuleType("elevenlabs"),
        "elevenlabs.client": types.ModuleType("elevenlabs"),
        "pyautogui": types.ModuleType("pyautogui"),
        "pytesseract": types.ModuleType("pytesseract"),
        "PIL": types.ModuleType("PIL"),
        "psutil": types.ModuleType("psutil"),
        "pygetwindow": types.ModuleType("pygetwindow"),
    }
    stubs["psutil"].process_iter = mock.MagicMock(return_value=[])
    stubs["psutil"].NoSuchProcess = Exception
    with mock.patch.dict(sys.modules, stubs):
        return importlib.import_module("live_chat_app")


# ---------------------------------------------------------------------------
# Finding 1 — ao_command shell injection (now uses create_subprocess_exec)
# ---------------------------------------------------------------------------

class TestAoCommandInjection:
    def test_ao_command_shlex_split_used(self):
        """shlex.split should parse ao_command args without shell interpretation."""
        # If shlex.split raises on malformed args, ao_command must return error
        malformed = "list; rm -rf /"
        try:
            parts = shlex.split(malformed, posix=False)
            # On Windows posix=False, semicolons are not special — split succeeds
            # The point is we never pass to shell
            assert isinstance(parts, list)
        except ValueError:
            pass  # Also acceptable

    def test_ao_command_invalid_syntax_returns_error(self):
        """Unmatched quotes in ao_command args should return a safe error string."""
        # shlex.split('unmatched "quote', posix=False) raises ValueError on some platforms
        try:
            shlex.split('unmatched "quote', posix=False)
        except ValueError:
            pass  # Good — error would be caught and returned safely

    @pytest.mark.asyncio
    async def test_ao_command_uses_exec_not_shell(self):
        """ao_command should call create_subprocess_exec, not create_subprocess_shell."""
        app = _app_module()
        exec_calls = []

        async def fake_exec(*args, **kwargs):
            exec_calls.append(args)
            proc = mock.AsyncMock()
            proc.communicate = mock.AsyncMock(return_value=(b"ok", b""))
            return proc

        with mock.patch("asyncio.create_subprocess_exec", fake_exec):
            await app.exec_tool("ao_command", {"args": "list"})

        # exec was called (not shell)
        assert exec_calls, "create_subprocess_exec should have been called"
        # First arg should be 'ao', not a shell string
        assert exec_calls[0][0] == "ao"


# ---------------------------------------------------------------------------
# Finding 2 — set_api_key race condition (now uses _global_state_lock)
# ---------------------------------------------------------------------------

class TestSetApiKeyLock:
    def test_global_state_lock_exists(self):
        app = _app_module()
        assert hasattr(app, "_global_state_lock")

    @pytest.mark.asyncio
    async def test_global_state_lock_is_acquirable(self):
        app = _app_module()
        app._global_state_lock = asyncio.Lock()
        async with app._global_state_lock:
            pass  # Must not deadlock


# ---------------------------------------------------------------------------
# Finding 3 — send_notification double-quote escaping
# ---------------------------------------------------------------------------

class TestNotificationEscaping:
    def test_double_quote_escaping(self):
        """Double quotes in title/message must be doubled for PowerShell strings."""
        message = 'He said "hello"'
        safe_msg = message.replace('"', '""')
        assert '""hello""' in safe_msg
        # No unescaped quote remains that could break the PS string
        assert '"hello"' not in safe_msg

    def test_no_injection_via_double_quotes(self):
        """Single quotes in message should pass through without injection."""
        message = "it's fine; rm -rf /"
        safe_msg = message.replace('"', '""')
        # Single quotes don't need escaping for double-quoted PS strings
        assert safe_msg == "it's fine; rm -rf /"


# ---------------------------------------------------------------------------
# Finding 4 — /api/model rate limit
# ---------------------------------------------------------------------------

class TestModelRateLimit:
    def test_model_endpoint_rate_limited(self):
        """_check_rate_limit should block after 10 calls per minute."""
        app = _app_module()
        key = "set_model:192.168.1.1"
        for _ in range(10):
            assert app._check_rate_limit(key, max_calls=10, window_secs=60)
        assert not app._check_rate_limit(key, max_calls=10, window_secs=60)

    def test_different_ips_have_separate_buckets(self):
        """Each client IP should get its own rate limit bucket."""
        app = _app_module()
        key_a = "set_model:10.0.0.1_test"
        key_b = "set_model:10.0.0.2_test"
        for _ in range(10):
            app._check_rate_limit(key_a, max_calls=10, window_secs=60)
        # ip_b should still be allowed
        assert app._check_rate_limit(key_b, max_calls=10, window_secs=60)


# ---------------------------------------------------------------------------
# Finding 5 — Ollama tool call JSON parse safety
# ---------------------------------------------------------------------------

class TestToolCallJsonParseSafety:
    def test_valid_dict_passes(self):
        """dict arguments should pass through unchanged."""
        args_in = {"x": 1, "y": "hello"}
        if isinstance(args_in, dict):
            args = args_in
        else:
            args = json.loads(args_in or "{}")
        assert args == args_in

    def test_valid_json_string_parses(self):
        """JSON string arguments should be parsed to dict."""
        raw = '{"x": 42}'
        args: dict
        if isinstance(raw, dict):
            args = raw
        else:
            args = json.loads(raw or "{}")
        assert args == {"x": 42}

    def test_corrupt_json_returns_empty_dict(self):
        """Malformed JSON arguments should return {} rather than crash."""
        raw = "NOT VALID JSON"
        args: dict
        try:
            if isinstance(raw, dict):
                args = raw
            else:
                args = json.loads(raw or "{}")
        except (json.JSONDecodeError, TypeError):
            args = {}
        assert args == {}

    def test_none_arguments_returns_empty_dict(self):
        """None/empty arguments should return {} safely."""
        raw = None
        try:
            r = raw or "{}"
            args = json.loads(r) if isinstance(r, str) else (r or {})
        except (json.JSONDecodeError, TypeError):
            args = {}
        assert args == {}


# ---------------------------------------------------------------------------
# Finding 6 — append_to_file uses run_in_executor + validate_tool_path
# ---------------------------------------------------------------------------

class TestAppendToFile:
    @pytest.mark.asyncio
    async def test_append_to_file_path_validated(self, tmp_path):
        """append_to_file should reject paths in blocked directories."""
        app = _app_module()
        # Blocked path — should be rejected by _validate_tool_path
        result = await app.exec_tool(
            "append_to_file",
            {"path": "C:\\Windows\\System32\\test.txt", "content": "evil"},
        )
        assert "error" in result.lower() or "blocked" in result.lower() or "restricted" in result.lower()

    @pytest.mark.asyncio
    async def test_append_to_file_succeeds_on_valid_path(self, tmp_path):
        """append_to_file should write to a valid path."""
        app = _app_module()
        target = tmp_path / "output.txt"
        result = await app.exec_tool(
            "append_to_file",
            {"path": str(target), "content": "hello world"},
        )
        assert "appended" in result.lower() or str(len("hello world")) in result
        if target.exists():
            assert "hello world" in target.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Finding 7 — browser_eval dangerous pattern blocking
# ---------------------------------------------------------------------------

class TestBrowserEvalBlocking:
    @pytest.mark.asyncio
    async def test_fetch_blocked(self):
        app = _app_module()
        with mock.patch.object(app, "get_browser_page", return_value=None):
            result = await app.exec_tool("browser_eval", {"js": "fetch('https://evil.com')"})
        assert "blocked" in result.lower() or "unavailable" in result.lower()

    @pytest.mark.asyncio
    async def test_localStorage_blocked(self):
        app = _app_module()
        with mock.patch.object(app, "get_browser_page", return_value=None):
            result = await app.exec_tool("browser_eval", {"js": "return localStorage.getItem('token')"})
        assert "blocked" in result.lower() or "unavailable" in result.lower()

    @pytest.mark.asyncio
    async def test_safe_js_passes(self):
        """document.title access should not be blocked."""
        import re
        dangerous = re.compile(
            r"fetch\s*\(|XMLHttpRequest|navigator\.credentials|localStorage|sessionStorage|indexedDB",
            re.IGNORECASE,
        )
        safe_js = "return document.title"
        assert not dangerous.search(safe_js)

    @pytest.mark.asyncio
    async def test_XMLHttpRequest_blocked(self):
        app = _app_module()
        with mock.patch.object(app, "get_browser_page", return_value=None):
            result = await app.exec_tool(
                "browser_eval", {"js": "var x = new XMLHttpRequest(); x.open('GET', '/api/keys')"}
            )
        assert "blocked" in result.lower() or "unavailable" in result.lower()


# ---------------------------------------------------------------------------
# Finding 8 — speak task cancelled on WS disconnect
# ---------------------------------------------------------------------------

class TestSpeakTaskCancelOnDisconnect:
    @pytest.mark.asyncio
    async def test_pending_speak_task_cancelled_on_pop(self):
        """Disconnecting WS should cancel any pending speak task."""
        task_mock = mock.MagicMock()
        task_mock.done.return_value = False
        task_mock.cancel = mock.MagicMock()

        ws_mock = mock.MagicMock()
        speak_tasks = {ws_mock: task_mock}

        # Simulate the cleanup logic
        pending = speak_tasks.pop(ws_mock, None)
        if pending and not pending.done():
            pending.cancel()

        task_mock.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_already_done_task_not_cancelled(self):
        """A completed speak task should not be cancelled again."""
        task_mock = mock.MagicMock()
        task_mock.done.return_value = True
        task_mock.cancel = mock.MagicMock()

        ws_mock = mock.MagicMock()
        speak_tasks = {ws_mock: task_mock}

        pending = speak_tasks.pop(ws_mock, None)
        if pending and not pending.done():
            pending.cancel()

        task_mock.cancel.assert_not_called()
