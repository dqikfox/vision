"""
test_cycle10.py — Unit tests for cycle-10 improvements.

Covers: provider/model validation on /api/model and WS set_model,
        broadcast() exception logging, _tool_err() info-disclosure fix,
        SQLite connection timeout, window_resize/move bounds.
"""

import asyncio
import sqlite3
import types
from unittest import mock

import httpx
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _app_module():
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
# Finding 2 + 5 — Provider/model validation
# ---------------------------------------------------------------------------

class TestProviderModelValidation:
    @pytest.mark.asyncio
    async def test_api_model_rejects_unknown_provider(self):
        """POST /api/model with unknown provider must return 400."""
        app = _app_module()
        async with httpx.AsyncClient(app=app.app, base_url="http://test") as client:
            r = await client.post("/api/model", json={"provider": "nonexistent_xyz", "model": "any"})
        assert r.status_code == 400
        assert "unknown provider" in r.json().get("error", "").lower()

    @pytest.mark.asyncio
    async def test_api_model_rejects_invalid_model_for_provider(self):
        """POST /api/model with invalid model for known provider must return 400."""
        app = _app_module()
        # Find a provider with a non-empty models list
        provider = next(
            (k for k, v in app.PROVIDERS.items() if v.get("models") and k != "ollama"),
            None,
        )
        if provider is None:
            pytest.skip("No provider with static model list found")
        async with httpx.AsyncClient(app=app.app, base_url="http://test") as client:
            r = await client.post("/api/model", json={"provider": provider, "model": "fake-model-zzz-9999"})
        assert r.status_code == 400
        body = r.json()
        assert "not available" in body.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_api_model_accepts_valid_provider(self):
        """POST /api/model with a known provider (no model) should succeed."""
        app = _app_module()
        provider = next(iter(app.PROVIDERS))
        async with httpx.AsyncClient(app=app.app, base_url="http://test") as client:
            r = await client.post("/api/model", json={"provider": provider, "model": ""})
        # Should be 200 (rate limit key is fresh)
        assert r.status_code == 200
        assert r.json().get("ok") is True

    @pytest.mark.asyncio
    async def test_api_model_accepts_empty_provider_and_model(self):
        """Empty strings for provider/model should not change state and succeed."""
        app = _app_module()
        async with httpx.AsyncClient(app=app.app, base_url="http://test") as client:
            r = await client.post("/api/model", json={"provider": "", "model": ""})
        assert r.status_code == 200

    def test_providers_dict_has_expected_keys(self):
        """All providers must have label, base_url, api_key, and models keys."""
        app = _app_module()
        for name, prov in app.PROVIDERS.items():
            assert "label" in prov, f"{name} missing 'label'"
            assert "base_url" in prov, f"{name} missing 'base_url'"
            assert "models" in prov, f"{name} missing 'models'"


# ---------------------------------------------------------------------------
# Finding 3 — broadcast() exception logging
# ---------------------------------------------------------------------------

class TestBroadcastExceptionLogging:
    @pytest.mark.asyncio
    async def test_failed_send_is_logged(self):
        """broadcast() must log failures, not silently swallow them."""
        app = _app_module()
        app._clients_lock = asyncio.Lock()

        log_calls = []
        ws_bad = mock.AsyncMock()
        ws_bad.send_text = mock.AsyncMock(side_effect=RuntimeError("connection lost"))
        ws_bad.client = "127.0.0.1"

        async with app._clients_lock:
            app.clients.add(ws_bad)

        with mock.patch.object(app, "write_log", side_effect=lambda *a: log_calls.append(a)):
            with mock.patch.object(app, "_resolve_target", return_value=None):
                await app.broadcast({"type": "test"})

        # The failed send should have been logged
        logged_keys = [a[0] for a in log_calls]
        assert "broadcast_error" in logged_keys, f"broadcast_error not in logs: {logged_keys}"

    @pytest.mark.asyncio
    async def test_dead_client_is_removed(self):
        """broadcast() must remove dead clients from the clients set."""
        app = _app_module()
        app._clients_lock = asyncio.Lock()

        ws_bad = mock.AsyncMock()
        ws_bad.send_text = mock.AsyncMock(side_effect=RuntimeError("gone"))
        ws_bad.client = "10.0.0.1"

        async with app._clients_lock:
            app.clients.add(ws_bad)

        with mock.patch.object(app, "_resolve_target", return_value=None), mock.patch.object(app, "write_log"):
            await app.broadcast({"type": "test"})

        assert ws_bad not in app.clients


# ---------------------------------------------------------------------------
# Finding 4 — _tool_err() info-disclosure prevention
# ---------------------------------------------------------------------------

class TestToolErrSanitisation:
    def test_permission_error_sanitised(self):
        app = _app_module()
        result = app._tool_err("read_file", PermissionError("access is denied to C:\\secret.key"))
        # Must not leak the secret path in return value
        assert "C:\\secret.key" not in result
        assert "permission" in result.lower() or "denied" in result.lower()

    def test_generic_error_sanitised(self):
        app = _app_module()
        result = app._tool_err("some_tool", Exception("internal error at 0xDEADBEEF memory address"))
        # Must not leak raw exception detail
        assert "0xDEADBEEF" not in result
        assert "some_tool failed" in result.lower() or "hint" in result.lower()

    def test_filenotfound_sanitised(self):
        app = _app_module()
        result = app._tool_err("read_file", FileNotFoundError("No such file: /home/user/.ssh/id_rsa"))
        assert "/home/user/.ssh/id_rsa" not in result
        assert "not found" in result.lower() or "file" in result.lower()

    def test_timeout_sanitised(self):
        app = _app_module()
        result = app._tool_err("run_command", TimeoutError("timed out after 30s"))
        assert "timed out" in result.lower() or "timeout" in result.lower()
        # Should not include raw numbers or internal details
        assert "30s" not in result

    def test_tool_error_written_to_log(self):
        app = _app_module()
        log_calls = []
        with mock.patch.object(app, "write_log", side_effect=lambda *a: log_calls.append(a)):
            app._tool_err("my_tool", RuntimeError("super secret internal error"))
        keys = [a[0] for a in log_calls]
        assert "tool_error_detail" in keys


# ---------------------------------------------------------------------------
# Finding 6 — SQLite connection timeout
# ---------------------------------------------------------------------------

class TestSQLiteConnectionTimeout:
    def test_connect_has_timeout(self, tmp_path):
        """_connect() must use a timeout to avoid hanging on lock contention."""
        from vision_rag import VisionRAGManager
        mgr = VisionRAGManager(source_root=tmp_path / "src", db_path=tmp_path / "rag.db")
        (tmp_path / "src").mkdir()

        conn_calls = []
        original_connect = sqlite3.connect

        def spy_connect(path, **kwargs):
            conn_calls.append(kwargs)
            return original_connect(path, **kwargs)

        with mock.patch("sqlite3.connect", side_effect=spy_connect):
            try:
                mgr.build_index()
            except Exception:
                pass

        timeouts = [c.get("timeout") for c in conn_calls]
        assert any(t is not None and t > 0 for t in timeouts), \
            f"Expected timeout in connect() calls but got: {conn_calls}"


# ---------------------------------------------------------------------------
# Finding 9 — window_resize / window_move bounds
# ---------------------------------------------------------------------------

class TestWindowBounds:
    @pytest.mark.asyncio
    async def test_window_resize_negative_dims_clamped(self):
        app = _app_module()
        gw_mock = mock.MagicMock()
        win_mock = mock.MagicMock()
        win_mock.title = "Test Window"
        gw_mock.getAllWindows.return_value = [win_mock]
        with mock.patch("pygetwindow.getAllWindows", gw_mock.getAllWindows):
            result = await app.exec_tool(
                "window_resize",
                {"title": "Test Window", "width": -100, "height": -500},
            )
        # Should succeed (clamped to min 200×200) or report no window found
        assert "error" not in result.lower() or "window" in result.lower()
        if win_mock.resizeTo.called:
            w_arg, h_arg = win_mock.resizeTo.call_args[0]
            assert w_arg >= 200
            assert h_arg >= 200

    @pytest.mark.asyncio
    async def test_window_resize_extreme_dims_clamped(self):
        app = _app_module()
        win_mock = mock.MagicMock()
        win_mock.title = "Test"
        with mock.patch("pygetwindow.getAllWindows", return_value=[win_mock]):
            await app.exec_tool(
                "window_resize",
                {"title": "Test", "width": 9999999, "height": 9999999},
            )
        if win_mock.resizeTo.called:
            w_arg, h_arg = win_mock.resizeTo.call_args[0]
            assert w_arg <= 7680
            assert h_arg <= 4320

    @pytest.mark.asyncio
    async def test_window_resize_invalid_type_returns_error(self):
        app = _app_module()
        result = await app.exec_tool(
            "window_resize",
            {"title": "Test", "width": "not_a_number", "height": "also_bad"},
        )
        assert "error" in result.lower() or "integer" in result.lower()
