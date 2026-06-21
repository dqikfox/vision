"""
test_cycle29.py — Structural tests for cycle-29 improvements

Tests verify:
1. Memory fact deletion (pop/remove) is performed under _save_lock
2. WS voice settings int() parsing is guarded with try/except
"""

import re

APP = "live_chat_app.py"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. Memory fact deletion under _save_lock
# ---------------------------------------------------------------------------


def test_facts_pop_under_save_lock():
    src = _read(APP)
    # Find the del_fact WS handler block
    fn = re.search(
        r'"del_fact".*?memory\.save\(\)',
        src,
        re.DOTALL,
    )
    assert fn is not None, "del_fact handler not found"
    body = fn.group()
    assert "_save_lock" in body, (
        "memory.data['facts'].pop() must be performed under memory._save_lock "
        "to prevent TOCTOU index-out-of-range race"
    )


def test_facts_pop_bounds_check_inside_lock():
    src = _read(APP)
    # Find the block
    fn = re.search(
        r'"del_fact".*?memory\.save\(\)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    lock_pos = body.find("_save_lock")
    pop_pos = body.find(".pop(idx)")
    bounds_pos = body.find("0 <= idx < len(")
    assert lock_pos != -1
    assert pop_pos != -1
    assert bounds_pos != -1
    # Both bounds check and pop must come after the lock context
    assert bounds_pos > lock_pos, "Bounds check must be inside the _save_lock block"
    assert pop_pos > lock_pos, "pop(idx) must be inside the _save_lock block"


# ---------------------------------------------------------------------------
# 2. WS voice settings int() parsing guarded
# ---------------------------------------------------------------------------


def test_tts_rate_int_guarded():
    src = _read(APP)
    # Find set_voice_settings WS handler — scope to the elif block
    fn = re.search(
        r'elif t == "set_voice_settings":(.*?)(?=\n            elif t ==|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None, "set_voice_settings WS handler not found"
    body = fn.group(1)
    tts_rate_pos = body.find("tts_rate = int(")
    assert tts_rate_pos != -1, "tts_rate int() conversion not found"
    preceding = body[:tts_rate_pos]
    assert "try:" in preceding, (
        "tts_rate int() must be wrapped in a try block to handle ValueError"
    )
    assert "(ValueError, TypeError)" in body, (
        "set_voice_settings must catch (ValueError, TypeError) for int() conversions"
    )


def test_tts_voice_idx_int_guarded():
    src = _read(APP)
    fn = re.search(
        r'elif t == "set_voice_settings":(.*?)(?=\n            elif t ==|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    idx_pos = body.find("tts_voice_idx = int(")
    assert idx_pos != -1, "tts_voice_idx int() conversion not found"
    preceding = body[:idx_pos]
    assert "try:" in preceding, (
        "tts_voice_idx int() must be wrapped in a try block"
    )


def test_voice_settings_int_errors_preserve_existing_value():
    src = _read(APP)
    fn = re.search(
        r'elif t == "set_voice_settings":(.*?)(?=\n            elif t ==|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    except_blocks = list(re.finditer(r"except \(ValueError, TypeError\):\s*\n\s*pass", body))
    assert len(except_blocks) >= 2, (
        "Both tts_rate and tts_voice_idx int() conversions must silently "
        "preserve the existing value on parse error (except: pass)"
    )
