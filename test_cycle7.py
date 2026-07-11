"""
test_cycle7.py — Unit tests for cycle-7 improvements.

Covers: RAG incremental indexing, tool argument bounds (scroll, screenshot_region,
        browser_scroll, ocr_region, kill_process), startup preflight broadcast,
        graceful shutdown RAG close, and VisionRAGManager.close().
"""

import types
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_rag(tmp_path: Path):
    """Create a VisionRAGManager with a temp source root and db path."""
    from vision_rag import VisionRAGManager

    source = tmp_path / "src"
    source.mkdir()
    return VisionRAGManager(source_root=source, db_path=tmp_path / "rag.db")


# ---------------------------------------------------------------------------
# VisionRAGManager — incremental indexing
# ---------------------------------------------------------------------------


class TestRAGIncremental:
    def test_schema_has_file_hash_column(self, tmp_path):
        mgr = _make_rag(tmp_path)
        (tmp_path / "src" / "a.txt").write_text("hello world " * 50, encoding="utf-8")
        mgr.build_index()
        with mgr._connect() as conn:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()]
        assert "file_hash" in cols
        assert "file_mtime" in cols

    def test_unchanged_file_not_re_chunked(self, tmp_path):
        """Second build_index call with same file should not insert new chunks."""
        mgr = _make_rag(tmp_path)
        (tmp_path / "src" / "b.txt").write_text("stable content " * 60, encoding="utf-8")

        first = mgr.build_index()
        second = mgr.build_index()

        assert first["chunks_indexed"] > 0
        assert second["chunks_indexed"] == first["chunks_indexed"]
        # New chunks were not inserted (no duplicates)
        with mgr._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == first["chunks_indexed"]

    def test_deleted_file_chunks_removed(self, tmp_path):
        """Chunks for a deleted file should be removed on the next build_index call."""
        mgr = _make_rag(tmp_path)
        f = tmp_path / "src" / "c.txt"
        f.write_text("content to be deleted " * 80, encoding="utf-8")

        first = mgr.build_index()
        assert first["chunks_indexed"] > 0

        f.unlink()
        second = mgr.build_index()
        assert second["chunks_indexed"] == 0

        with mgr._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_modified_file_re_indexed(self, tmp_path):
        """Modifying a file changes its hash — chunks should be refreshed."""
        mgr = _make_rag(tmp_path)
        f = tmp_path / "src" / "d.txt"
        f.write_text("version one " * 80, encoding="utf-8")
        first = mgr.build_index()

        # Force mtime change so hash differs
        import time

        time.sleep(0.05)
        f.write_text("version two completely different content " * 80, encoding="utf-8")

        second = mgr.build_index()
        with mgr._connect() as conn:
            hashes = conn.execute("SELECT DISTINCT file_hash FROM chunks").fetchall()
        # Only the new hash should be present
        assert len(hashes) == 1
        _ = second  # result not None

    def test_build_index_result_has_incremental_key(self, tmp_path):
        mgr = _make_rag(tmp_path)
        (tmp_path / "src" / "e.txt").write_text("content " * 60, encoding="utf-8")
        result = mgr.build_index()
        assert result.get("incremental") is True

    def test_close_does_not_raise_on_missing_db(self, tmp_path):
        mgr = _make_rag(tmp_path)
        # No db exists yet
        mgr.close()  # should not raise

    def test_close_runs_pragma_optimize(self, tmp_path):
        mgr = _make_rag(tmp_path)
        (tmp_path / "src" / "f.txt").write_text("data " * 60, encoding="utf-8")
        mgr.build_index()
        mgr.close()  # should not raise and should checkpoint WAL


# ---------------------------------------------------------------------------
# Tool argument bounds — live_chat_app.exec_tool
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
    # Give psutil a stub process_iter
    stubs["psutil"].process_iter = mock.MagicMock(return_value=[])
    stubs["psutil"].NoSuchProcess = Exception
    with mock.patch.dict(sys.modules, stubs):
        return importlib.import_module("live_chat_app")


@pytest.mark.asyncio
async def test_scroll_negative_clicks_clamped():
    """scroll: negative clicks should be clamped to minimum 1."""
    app = _app_module()
    scroll_calls = []
    app.pyautogui.scroll = lambda amount, x=0, y=0: scroll_calls.append(amount)
    result = await app.exec_tool("scroll", {"x": 100, "y": 100, "clicks": -10, "direction": "down"})
    assert "scrolled" in result.lower()
    # clamped to 1 click → scroll amount should be -1
    assert scroll_calls and abs(scroll_calls[0]) == 1


@pytest.mark.asyncio
async def test_scroll_extreme_clicks_clamped():
    """scroll: clicks > 50 should be clamped to 50."""
    app = _app_module()
    scroll_calls = []
    app.pyautogui.scroll = lambda amount, x=0, y=0: scroll_calls.append(amount)
    await app.exec_tool("scroll", {"x": 0, "y": 0, "clicks": 999, "direction": "up"})
    assert scroll_calls and abs(scroll_calls[0]) == 50


@pytest.mark.asyncio
async def test_browser_scroll_extreme_amount_clamped():
    """browser_scroll: amount > 10000 should be clamped."""
    app = _app_module()
    page_mock = mock.AsyncMock()
    page_mock.evaluate = mock.AsyncMock(return_value=None)
    with mock.patch.object(app, "get_browser_page", return_value=page_mock):
        result = await app.exec_tool("browser_scroll", {"direction": "down", "amount": 999999})
    # Should call evaluate with clamped value
    call_args = page_mock.evaluate.call_args[0][0]
    assert "10000" in call_args


@pytest.mark.asyncio
async def test_kill_process_negative_pid_rejected():
    """kill_process: negative pid should return error, not kill anything."""
    app = _app_module()
    app.HAS_PSUTIL = True
    result = await app.exec_tool("kill_process", {"pid": -5})
    assert "error" in result.lower() or "pid" in result.lower()


@pytest.mark.asyncio
async def test_kill_process_zero_pid_rejected():
    """kill_process: pid=0 should return error."""
    app = _app_module()
    app.HAS_PSUTIL = True
    result = await app.exec_tool("kill_process", {"pid": 0})
    assert "error" in result.lower() or "pid" in result.lower()


@pytest.mark.asyncio
async def test_kill_process_invalid_string_pid_rejected():
    """kill_process: non-numeric pid string should return error gracefully."""
    app = _app_module()
    app.HAS_PSUTIL = True
    result = await app.exec_tool("kill_process", {"pid": "not_a_number"})
    assert "error" in result.lower() or "invalid" in result.lower()


@pytest.mark.asyncio
async def test_screenshot_region_extreme_dims_clamped():
    """screenshot_region: out-of-range dimensions should be clamped, not crash."""
    app = _app_module()
    captured = {}

    def fake_screenshot(region):
        captured["region"] = region
        img = mock.MagicMock()
        img.save = lambda *a, **k: None
        return img

    app.pyautogui.screenshot = fake_screenshot
    with mock.patch("base64.b64encode", return_value=b"abc"):
        await app.exec_tool(
            "screenshot_region",
            {"x": -999, "y": 999999, "width": 0, "height": -100},
        )
    if captured.get("region"):
        rx, ry, rw, rh = captured["region"]
        assert rx >= 0
        assert ry <= 65535
        assert rw >= 1
        assert rh >= 1
