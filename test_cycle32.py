"""Structural tests for cycle 32 fixes.

All four fixes guard memory.data["facts"] access under memory._save_lock.
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).parent / "live_chat_app.py"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# /api/memory/fact DELETE endpoint
# ---------------------------------------------------------------------------


def test_api_del_fact_uses_save_lock():
    src = _read(APP)
    m = re.search(
        r"@app\.delete\(\"/api/memory/fact\"\)(.*?)(?=\n@app\.|\Z)",
        src,
        re.DOTALL,
    )
    assert m is not None, "DELETE /api/memory/fact endpoint not found"
    body = m.group(1)
    assert "memory._save_lock" in body, "DELETE /api/memory/fact must use memory._save_lock"
    # The lock must wrap the remove, not just be present
    lock_pos = body.find("memory._save_lock")
    remove_pos = body.find(".remove(fact)")
    assert lock_pos < remove_pos, "memory._save_lock must precede .remove(fact) in DELETE endpoint"


# ---------------------------------------------------------------------------
# WS del_fact handler — elif (by-value) branch
# ---------------------------------------------------------------------------


def test_ws_del_fact_elif_uses_save_lock():
    src = _read(APP)
    m = re.search(
        r'elif t == "del_fact":(.*?)(?=\n            elif t ==|\Z)',
        src,
        re.DOTALL,
    )
    assert m is not None, "del_fact WS handler not found"
    body = m.group(1)
    # Count occurrences of _save_lock — should be at least 2 (one for idx, one for elif)
    lock_count = body.count("memory._save_lock")
    assert lock_count >= 2, (
        f"del_fact WS handler must protect BOTH idx pop AND elif remove with "
        f"_save_lock; found {lock_count} occurrence(s)"
    )
    # The elif branch must also re-check inside the lock
    elif_pos = body.find("elif fact")
    # Look for a second lock after the elif
    second_lock_pos = body.find("memory._save_lock", body.find("memory._save_lock") + 1)
    assert second_lock_pos != -1 and second_lock_pos > elif_pos, "elif branch of del_fact must also use _save_lock"


# ---------------------------------------------------------------------------
# forget tool handler
# ---------------------------------------------------------------------------


def test_forget_tool_uses_save_lock():
    src = _read(APP)
    m = re.search(
        r'elif name == "forget":(.*?)(?=\n    elif name ==|\Z)',
        src,
        re.DOTALL,
    )
    assert m is not None, "forget tool handler not found"
    body = m.group(1)
    assert "memory._save_lock" in body, "forget tool handler must use memory._save_lock"
    lock_pos = body.find("memory._save_lock")
    before_pos = body.find("before = len(")
    assert lock_pos < before_pos, "memory._save_lock must precede 'before = len(' in forget handler"


# ---------------------------------------------------------------------------
# recall tool handler
# ---------------------------------------------------------------------------


def test_recall_tool_uses_save_lock():
    src = _read(APP)
    m = re.search(
        r'elif name == "recall":(.*?)(?=\n    elif name ==|\Z)',
        src,
        re.DOTALL,
    )
    assert m is not None, "recall tool handler not found"
    body = m.group(1)
    assert "memory._save_lock" in body, "recall tool handler must use memory._save_lock when reading facts"
    lock_pos = body.find("memory._save_lock")
    facts_pos = body.find("memory.data")
    assert lock_pos < facts_pos, "memory._save_lock must precede memory.data access in recall handler"
