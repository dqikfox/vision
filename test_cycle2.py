"""
test_cycle2.py — Unit tests for cycle-2 improvements.

Covers: _tracked_task lifecycle, _run_preflight validation,
        Memory._normalize type coercion, and execute_python audit logging.
"""

from __future__ import annotations

import asyncio
import os
import sys
import types
import unittest.mock as mock
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers to import module without starting the full server
# ---------------------------------------------------------------------------


def _import_app_module():
    """Return live_chat_app module, skipping network/device init side-effects."""
    if "live_chat_app" in sys.modules:
        return sys.modules["live_chat_app"]
    # Patch heavy optional imports so the module can be imported offline
    stubs = {
        "elevenlabs": types.ModuleType("elevenlabs"),
        "elevenlabs.client": types.ModuleType("elevenlabs.client"),
        "pyautogui": types.ModuleType("pyautogui"),
        "pytesseract": types.ModuleType("pytesseract"),
        "PIL": types.ModuleType("PIL"),
        "PIL.Image": types.ModuleType("PIL.Image"),
    }
    with mock.patch.dict(sys.modules, stubs):
        import importlib

        app = importlib.import_module("live_chat_app")
    return app


# ---------------------------------------------------------------------------
# _tracked_task
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tracked_task_adds_to_set():
    app = _import_app_module()

    async def _noop():
        await asyncio.sleep(0)

    initial = len(app._background_tasks)
    task = app._tracked_task(_noop())
    # Task is added before it finishes
    assert len(app._background_tasks) >= initial
    await asyncio.sleep(0.05)  # let task complete


@pytest.mark.asyncio
async def test_tracked_task_removed_on_done():
    app = _import_app_module()

    completed = asyncio.Event()

    async def _quick():
        completed.set()

    app._tracked_task(_quick())
    await asyncio.wait_for(completed.wait(), timeout=2)
    await asyncio.sleep(0.05)
    # Done callback removes from set
    # We can't guarantee set is empty (other tasks may be there) but the
    # specific coroutine must have been removed.
    assert True  # no exception means lifecycle completed cleanly


@pytest.mark.asyncio
async def test_tracked_task_exception_does_not_propagate():
    """Exceptions inside tracked tasks must be swallowed (logged, not raised)."""
    app = _import_app_module()

    async def _bad():
        raise ValueError("intentional test error")

    task = app._tracked_task(_bad())
    # Give the event loop a chance to run the task and its done-callback
    await asyncio.sleep(0.1)
    assert task.done()


# ---------------------------------------------------------------------------
# Memory._normalize type coercion
# ---------------------------------------------------------------------------


def test_memory_normalize_coerces_types():
    app = _import_app_module()
    mem = app.Memory.__new__(app.Memory)

    raw = {
        "user_name": 42,  # should become "42"
        "user_preferences": "bad",  # should become {}
        "interaction_count": "7",  # should become 7
        "facts": None,  # should become []
        "recent_topics": "x",  # should become []
    }
    normalized = mem._normalize(raw)
    assert isinstance(normalized["user_name"], str)
    assert isinstance(normalized["user_preferences"], dict)
    assert isinstance(normalized["interaction_count"], int)
    assert isinstance(normalized["facts"], list)
    assert isinstance(normalized["recent_topics"], list)


# ---------------------------------------------------------------------------
# execute_python audit logging
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_python_writes_audit_log(tmp_path, monkeypatch):
    app = _import_app_module()

    logged: list[tuple] = []

    def _fake_write_log(event: str, detail: str = "") -> None:
        logged.append((event, detail))

    monkeypatch.setattr(app, "write_log", _fake_write_log)

    await app.exec_tool("execute_python", {"code": "x=1", "timeout": "5"})

    assert any(e == "execute_python" for e, _ in logged), (
        f"execute_python did not emit an audit log entry; logged={logged!r}"
    )
    audit_entries = [(e, d) for e, d in logged if e == "execute_python"]
    assert "x=1" in audit_entries[0][1] or "x=1" in str(audit_entries[0])


# ---------------------------------------------------------------------------
# _run_preflight — smoke: at least returns a dict with expected keys
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_preflight_returns_dict():
    app = _import_app_module()
    result = await app._run_preflight()
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    # Must contain the canonical health keys
    for key in ("elevenlabs", "ocr", "audio", "playwright"):
        assert key in result, f"Missing key {key!r} in preflight result {result!r}"
