"""
test_cycle20.py — Structural tests for cycle-20 improvements

Tests verify:
1. _save_key() strips newlines from value before writing to .env
2. press_key validates key name length/ascii before calling pyautogui
3. press_key wraps pyautogui call in try/except using _tool_err
4. focus_window prefers exact match before substring match
5. window_resize and window_move prefer exact match before substring
"""

import re


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


APP = "live_chat_app.py"


# ---------------------------------------------------------------------------
# 1. _save_key — newline sanitisation
# ---------------------------------------------------------------------------


def test_save_key_strips_newlines():
    """_save_key() must remove \\n/\\r from value before writing to .env."""
    src = _read(APP)
    fn = re.search(
        r"def _save_key\(.*?(?=\n\S|\nAPI_11)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_save_key() not found"
    body = fn.group()
    # Should have a safe_value that strips newlines
    assert "safe_value" in body or (r'replace("\n"' in body or "replace('\\n'" in body), (
        "_save_key() must strip newlines from value before writing to .env"
    )


def test_save_key_uses_safe_value():
    """_save_key() must write safe_value (not raw value) to .env lines."""
    src = _read(APP)
    fn = re.search(
        r"def _save_key\(.*?(?=\n\S|\nAPI_11)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # The .env write lines should use safe_value, not raw value
    env_write = re.search(r"lines\[i\] = f\"{env_var}=(\S+)\"", body)
    if env_write:
        assert "safe_value" in env_write.group(1), "lines[i] assignment must use safe_value, not raw value"
    append_write = re.search(r"lines\.append\(f\"{env_var}=(\S+)\"\)", body)
    if append_write:
        assert "safe_value" in append_write.group(1), "lines.append() must use safe_value, not raw value"


# ---------------------------------------------------------------------------
# 2. press_key — validation
# ---------------------------------------------------------------------------


def test_press_key_validates_length():
    """press_key must check key part length before calling pyautogui."""
    src = _read(APP)
    block = re.search(
        r'elif name == "press_key".*?(?=\n    # ──|\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None, "press_key handler not found"
    body = block.group()
    assert "len(" in body, "press_key must check key name length"
    # Should return an error for oversized keys
    assert "error" in body.lower() or "invalid" in body.lower(), (
        "press_key must return an error message for invalid key names"
    )


def test_press_key_validates_ascii():
    """press_key must reject non-ASCII key names."""
    src = _read(APP)
    block = re.search(
        r'elif name == "press_key".*?(?=\n    # ──|\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "isascii()" in body or ".isascii" in body, "press_key must validate key names are ASCII"


def test_press_key_uses_tool_err():
    """press_key must catch pyautogui exceptions via _tool_err."""
    src = _read(APP)
    block = re.search(
        r'elif name == "press_key".*?(?=\n    # ──|\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "_tool_err(" in body, "press_key must wrap pyautogui.hotkey() in try/except using _tool_err()"


# ---------------------------------------------------------------------------
# 3. focus_window — exact-first matching
# ---------------------------------------------------------------------------


def test_focus_window_exact_match_first():
    """focus_window must try exact title match before falling back to substring."""
    src = _read(APP)
    block = re.search(
        r'elif name == "focus_window".*?(?=\n    # ──|\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None, "focus_window handler not found"
    body = block.group()
    # Must have exact equality check (w.title.lower() == title.lower())
    assert "== title.lower()" in body or "title.lower() ==" in body, (
        "focus_window must check for exact title match first"
    )


def test_focus_window_falls_back_to_substring():
    """focus_window still falls back to substring matching when no exact match exists."""
    src = _read(APP)
    block = re.search(
        r'elif name == "focus_window".*?(?=\n    # ──|\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    # Must still have 'in w.title.lower()' for substring fallback
    assert "in w.title.lower()" in body or "in w_.title.lower()" in body, (
        "focus_window must still fall back to substring matching"
    )


# ---------------------------------------------------------------------------
# 4. window_resize — exact-first matching
# ---------------------------------------------------------------------------


def test_window_resize_exact_match_first():
    """window_resize must try exact title match before falling back to substring."""
    src = _read(APP)
    block = re.search(
        r'elif name == "window_resize".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None, "window_resize handler not found"
    body = block.group()
    assert "== title.lower()" in body or "title.lower() ==" in body, (
        "window_resize must check for exact title match first"
    )


# ---------------------------------------------------------------------------
# 5. window_move — exact-first matching
# ---------------------------------------------------------------------------


def test_window_move_exact_match_first():
    """window_move must try exact title match before falling back to substring."""
    src = _read(APP)
    block = re.search(
        r'elif name == "window_move".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None, "window_move handler not found"
    body = block.group()
    assert "== title.lower()" in body or "title.lower() ==" in body, (
        "window_move must check for exact title match first"
    )
