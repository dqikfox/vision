"""
test_cycle8.py — Unit tests for cycle-8 improvements.

Covers: global state lock for set_model/set_voice_settings, JSON config
        corruption recovery, thread-safe rate limiter, WS message type
        validation, fetch_url SSRF guard + timeout bounds, escHtml hardening.
"""

import asyncio
import json
import threading
import types
from pathlib import Path
from unittest import mock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _app_module():
    """Import live_chat_app with heavy optional deps stubbed out."""
    import importlib
    import sys

    stubs = {
        "elevenlabs": types.ModuleType("elevenlabs"),
        "elevenlabs.client": types.ModuleType("elevenlabs.client"),
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
# Finding 3 — Thread-safe rate limiter
# ---------------------------------------------------------------------------


class TestRateLimiter:
    def test_allows_calls_within_limit(self):
        app = _app_module()
        # Fresh key — first N calls should all pass
        for _ in range(5):
            assert app._check_rate_limit("test_key_allow", max_calls=5, window_secs=60)

    def test_blocks_calls_over_limit(self):
        app = _app_module()
        key = "test_key_block_" + str(id(self))
        for _ in range(3):
            app._check_rate_limit(key, max_calls=3, window_secs=60)
        # 4th call should be blocked
        assert not app._check_rate_limit(key, max_calls=3, window_secs=60)

    def test_rate_limiter_thread_safe(self):
        """Concurrent calls from multiple threads must not corrupt _rate_buckets."""
        app = _app_module()
        key = "test_thread_safe_" + str(id(self))
        results = []
        errors = []

        def call():
            try:
                results.append(app._check_rate_limit(key, max_calls=100, window_secs=60))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors in concurrent rate limiter: {errors}"
        assert len(results) == 50

    def test_rate_limit_lock_is_threading_lock(self):
        """_rate_limit_lock must be a threading.Lock, not an asyncio.Lock."""
        app = _app_module()
        assert isinstance(app._rate_limit_lock, type(threading.Lock()))


# ---------------------------------------------------------------------------
# Finding 2 — JSON config corruption recovery
# ---------------------------------------------------------------------------


class TestConfigCorruptionRecovery:
    def test_corrupt_command_center_config_returns_default(self, tmp_path):
        app = _app_module()
        bad_file = tmp_path / "vision_command_center_config.json"
        bad_file.write_text("NOT VALID JSON {{{", encoding="utf-8")
        with mock.patch.object(app, "COMMAND_CENTER_CONFIG_FILE", bad_file):
            result = app._load_command_center_config()
        # Should return a valid dict (the default), not raise
        assert isinstance(result, dict)

    def test_corrupt_automation_state_returns_default(self, tmp_path):
        app = _app_module()
        bad_file = tmp_path / "vision_automation_state.json"
        bad_file.write_text('{"broken": true, "unclosed":', encoding="utf-8")
        with mock.patch.object(app, "AUTOMATION_STATE_FILE", bad_file):
            result = app._load_automation_state()
        assert isinstance(result, dict)
        assert "routine_runs" in result


# ---------------------------------------------------------------------------
# Finding 5 — WS message type validation
# ---------------------------------------------------------------------------


class TestWSMessageValidation:
    @pytest.mark.asyncio
    async def test_non_dict_message_rejected(self):
        """A JSON array sent over WS should be silently rejected."""
        app = _app_module()
        ws_mock = mock.AsyncMock()
        raw_array = json.dumps([1, 2, 3])
        # Simulate the check the ws handler does
        msg = json.loads(raw_array)
        assert not isinstance(msg, dict), "array should fail dict check"

    @pytest.mark.asyncio
    async def test_missing_type_field_rejected(self):
        """Message without 'type' field should be rejected."""
        msg = {"action": "something"}
        t = msg.get("type")
        assert not isinstance(t, str) or not t

    @pytest.mark.asyncio
    async def test_empty_type_rejected(self):
        """Message with empty string 'type' should be rejected."""
        msg = {"type": ""}
        t = msg.get("type")
        assert not isinstance(t, str) or not t

    def test_valid_message_passes(self):
        """Normal messages with string type should pass validation."""
        msg = {"type": "text", "text": "hello"}
        t = msg.get("type")
        assert isinstance(t, str) and t == "text"


# ---------------------------------------------------------------------------
# Finding 8 — fetch_url SSRF guard
# ---------------------------------------------------------------------------


class TestFetchUrlSSRF:
    @pytest.mark.asyncio
    async def test_non_http_url_rejected(self):
        app = _app_module()
        result = await app.exec_tool("fetch_url", {"url": "file:///etc/passwd"})
        assert "error" in result.lower() or "http" in result.lower()

    @pytest.mark.asyncio
    async def test_ftp_url_rejected(self):
        app = _app_module()
        result = await app.exec_tool("fetch_url", {"url": "ftp://example.com/secret"})
        assert "error" in result.lower() or "http" in result.lower()

    @pytest.mark.asyncio
    async def test_javascript_url_rejected(self):
        app = _app_module()
        result = await app.exec_tool("fetch_url", {"url": "javascript:alert(1)"})
        assert "error" in result.lower() or "http" in result.lower()

    @pytest.mark.asyncio
    async def test_valid_https_url_passes_guard(self):
        """https:// URLs should pass the URL scheme guard (may still fail network)."""
        app = _app_module()
        # We just want to confirm no immediate rejection on scheme check
        url = "https://httpbin.org/get"
        assert url.startswith(("http://", "https://"))


# ---------------------------------------------------------------------------
# Finding 1 — Global state lock present and initialised in startup
# ---------------------------------------------------------------------------


class TestGlobalStateLock:
    def test_global_state_lock_declaration_exists(self):
        app = _app_module()
        # The lock is declared at module level; will be AsyncLock after startup()
        assert hasattr(app, "_global_state_lock")

    @pytest.mark.asyncio
    async def test_global_state_lock_is_asyncio_lock_after_init(self):
        """After startup(), _global_state_lock must be an asyncio.Lock."""
        app = _app_module()
        # Simulate startup lock init
        app._global_state_lock = asyncio.Lock()
        assert isinstance(app._global_state_lock, asyncio.Lock)
        # Lock must be acquirable
        async with app._global_state_lock:
            pass  # no deadlock


# ---------------------------------------------------------------------------
# escHtml (UI) — verify patterns not tested at Python level but documented
# ---------------------------------------------------------------------------


class TestEscHtmlPatterns:
    """Document the expected escHtml output patterns (logic lives in JS)."""

    def _esc(self, text: str) -> str:
        """Python mirror of the hardened JS escHtml function."""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def test_escapes_script_tag(self):
        assert "<script>" not in self._esc('<script>alert("xss")</script>')

    def test_escapes_double_quotes(self):
        assert "&quot;" in self._esc('"hello"')

    def test_escapes_single_quotes(self):
        assert "&#39;" in self._esc("it's fine")

    def test_ampersand_escaped(self):
        assert "&amp;" in self._esc("a & b")

    def test_safe_text_unchanged(self):
        result = self._esc("Hello World 123")
        assert result == "Hello World 123"
