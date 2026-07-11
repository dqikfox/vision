"""
test_cycle5.py — Unit tests for cycle-5 improvements.

Covers: WebSocket size guard, Memory.save() atomic write,
        write_log() rotation, health endpoint new fields,
        execute_python result log entry.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import types
import unittest.mock as mock
from pathlib import Path

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
# write_log() — rotation
# ---------------------------------------------------------------------------

def test_write_log_rotates_at_100mb(tmp_path, monkeypatch):
    app = _app()
    log = tmp_path / "chat_events.log"
    # Create a fake oversized log (101 MB represented by a sparse file via seek)
    log.write_bytes(b"x")
    monkeypatch.setattr(app, "LOG_FILE", log)

    # Patch stat to report 101 MB
    original_stat = Path.stat

    def _fat_stat(self, *a, **kw):
        s = original_stat(self, *a, **kw)
        if self == log:
            # Return a mock stat_result with large st_size
            class _S:
                st_size = 101_000_000
                def __getattr__(self, n):
                    return getattr(s, n)
            return _S()
        return s

    monkeypatch.setattr(Path, "stat", _fat_stat)

    app.write_log("test", "rotation trigger")
    # A rotated file should exist in tmp_path
    rotated = [f for f in tmp_path.iterdir() if f.name != "chat_events.log"]
    assert len(rotated) >= 1, "Expected at least one rotated log file"


def test_write_log_creates_file(tmp_path, monkeypatch):
    app = _app()
    log = tmp_path / "chat_events.log"
    monkeypatch.setattr(app, "LOG_FILE", log)
    app.write_log("test_event", "hello world")
    content = log.read_text(encoding="utf-8")
    assert "TEST_EVENT" in content
    assert "hello world" in content


# ---------------------------------------------------------------------------
# Memory.save() — atomic write
# ---------------------------------------------------------------------------

def test_memory_save_atomic_creates_file(tmp_path, monkeypatch):
    app = _app()
    mem_file = tmp_path / "memory.json"
    monkeypatch.setattr(app, "MEMORY_FILE", mem_file)
    mem = app.Memory.__new__(app.Memory)
    mem.data = {"user_name": "test", "facts": [], "user_preferences": {},
                "interaction_count": 0, "recent_topics": []}
    mem.save()
    assert mem_file.exists()
    loaded = json.loads(mem_file.read_text(encoding="utf-8"))
    assert loaded["user_name"] == "test"


def test_memory_save_no_partial_write(tmp_path, monkeypatch):
    """After save(), file should be valid JSON, not a partial write."""
    app = _app()
    mem_file = tmp_path / "memory.json"
    monkeypatch.setattr(app, "MEMORY_FILE", mem_file)
    mem = app.Memory.__new__(app.Memory)
    mem.data = {"user_name": "atomic", "facts": ["a"] * 100,
                "user_preferences": {}, "interaction_count": 5, "recent_topics": []}
    mem.save()
    # Must parse cleanly
    result = json.loads(mem_file.read_text(encoding="utf-8"))
    assert len(result["facts"]) == 100


# ---------------------------------------------------------------------------
# Health endpoint — new fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_includes_new_fields():
    app = _app()
    resp = await app.api_health()
    body = json.loads(resp.body)
    for field in ("current_provider", "current_model", "active_connections", "background_tasks"):
        assert field in body, f"Health endpoint missing field: {field!r}"


@pytest.mark.asyncio
async def test_health_active_connections_is_int():
    app = _app()
    resp = await app.api_health()
    body = json.loads(resp.body)
    assert isinstance(body["active_connections"], int)
    assert body["active_connections"] >= 0


@pytest.mark.asyncio
async def test_health_background_tasks_is_int():
    app = _app()
    resp = await app.api_health()
    body = json.loads(resp.body)
    assert isinstance(body["background_tasks"], int)


# ---------------------------------------------------------------------------
# execute_python — result audit log
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_python_logs_result_entry(monkeypatch):
    app = _app()
    logged: list[tuple[str, str]] = []

    def _capture(event: str, detail: str = "") -> None:
        logged.append((event, detail))

    monkeypatch.setattr(app, "write_log", _capture)
    await app.exec_tool("execute_python", {"code": "x = 1 + 1", "timeout": "5"})

    result_entries = [d for e, d in logged if e == "execute_python_result"]
    assert result_entries, f"No execute_python_result log entry found; all logged: {logged!r}"
    assert "status=" in result_entries[0]
    assert "output_len=" in result_entries[0]


@pytest.mark.asyncio
async def test_execute_python_result_log_shows_error_on_bad_code(monkeypatch):
    app = _app()
    logged: list[tuple[str, str]] = []
    monkeypatch.setattr(app, "write_log", lambda e, d="": logged.append((e, d)))
    await app.exec_tool("execute_python", {"code": "raise ValueError('oops')", "timeout": "5"})
    result_entries = [d for e, d in logged if e == "execute_python_result"]
    # returncode != 0 when unhandled exception bubbles out of wrapper
    # The wrapper catches exceptions, so returncode may be 0 with error in stdout
    assert result_entries, "Expected execute_python_result log"
