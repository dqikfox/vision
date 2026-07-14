"""Structural tests for cycle 31 fixes.

1. Tool handler int/float conversions wrapped in try/except
2. UI provider label escaped with escHtml
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).parent / "live_chat_app.py"
UI = Path(__file__).parent / "live_chat_ui.html"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _tool_block(src: str, tool_name: str) -> str:
    """Extract the elif block for a named tool."""
    m = re.search(
        rf'elif name == "{re.escape(tool_name)}":(.*?)(?=\n    elif name ==|\n    return _tool_err|\Z)',
        src,
        re.DOTALL,
    )
    assert m is not None, f"Tool handler '{tool_name}' not found"
    return m.group(1)


# ---------------------------------------------------------------------------
# run_command timeout guarded
# ---------------------------------------------------------------------------

def test_run_command_timeout_guarded():
    src = _read(APP)
    body = _tool_block(src, "run_command")
    timeout_pos = body.find("timeout = int(")
    assert timeout_pos != -1, "run_command: timeout int() conversion not found"
    preceding = body[:timeout_pos]
    assert "try:" in preceding, "run_command: timeout must be inside a try block"
    assert "(ValueError, TypeError)" in body, (
        "run_command: must catch (ValueError, TypeError)"
    )


# ---------------------------------------------------------------------------
# wait tool seconds guarded
# ---------------------------------------------------------------------------

def test_wait_secs_guarded():
    src = _read(APP)
    body = _tool_block(src, "wait")
    secs_pos = body.find("secs = max(")
    assert secs_pos != -1, "wait: secs clamped assignment not found"
    preceding = body[:secs_pos]
    assert "try:" in preceding, "wait: secs must be inside a try block"
    assert "(ValueError, TypeError)" in body


# ---------------------------------------------------------------------------
# kb_index max_files guarded
# ---------------------------------------------------------------------------

def test_kb_index_max_files_guarded():
    src = _read(APP)
    body = _tool_block(src, "kb_index")
    mf_pos = body.find("max_files = int(")
    assert mf_pos != -1, "kb_index: max_files int() not found"
    preceding = body[:mf_pos]
    assert "try:" in preceding, "kb_index: max_files must be inside a try block"
    assert "(ValueError, TypeError)" in body


# ---------------------------------------------------------------------------
# kb_search limit guarded
# ---------------------------------------------------------------------------

def test_kb_search_limit_guarded():
    src = _read(APP)
    body = _tool_block(src, "kb_search")
    lim_pos = body.find("limit = int(")
    assert lim_pos != -1, "kb_search: limit int() not found"
    preceding = body[:lim_pos]
    assert "try:" in preceding, "kb_search: limit must be inside a try block"
    assert "(ValueError, TypeError)" in body


# ---------------------------------------------------------------------------
# kb_export_training_data max_examples guarded
# ---------------------------------------------------------------------------

def test_kb_export_max_examples_guarded():
    src = _read(APP)
    body = _tool_block(src, "kb_export_training_data")
    me_pos = body.find("max_examples = max(")
    assert me_pos != -1, "kb_export_training_data: max_examples clamped assignment not found"
    preceding = body[:me_pos]
    assert "try:" in preceding, (
        "kb_export_training_data: max_examples must be inside a try block"
    )
    assert "(ValueError, TypeError)" in body


# ---------------------------------------------------------------------------
# browser_wait timeout guarded
# ---------------------------------------------------------------------------

def test_browser_wait_timeout_guarded():
    src = _read(APP)
    body = _tool_block(src, "browser_wait")
    timeout_pos = body.find("timeout = int(")
    assert timeout_pos != -1, "browser_wait: timeout int() not found"
    preceding = body[:timeout_pos]
    assert "try:" in preceding, "browser_wait: timeout must be inside a try block"
    assert "(ValueError, TypeError)" in body


# ---------------------------------------------------------------------------
# fetch_url timeout_secs guarded
# ---------------------------------------------------------------------------

def test_fetch_url_timeout_secs_guarded():
    src = _read(APP)
    body = _tool_block(src, "fetch_url")
    ts_pos = body.find("timeout_secs = max(")
    assert ts_pos != -1, "fetch_url: timeout_secs clamped assignment not found"
    preceding = body[:ts_pos]
    assert "try:" in preceding, "fetch_url: timeout_secs must be inside a try block"
    assert "(ValueError, TypeError)" in body


# ---------------------------------------------------------------------------
# ocr_region coords guarded
# ---------------------------------------------------------------------------

def test_ocr_region_coords_guarded():
    src = _read(APP)
    body = _tool_block(src, "ocr_region")
    x_pos = body.find("x, y = max(")
    assert x_pos != -1, "ocr_region: x,y clamped assignment not found"
    preceding = body[:x_pos]
    assert "try:" in preceding, "ocr_region: x/y/w/h must be inside a try block"
    assert "(ValueError, TypeError)" in body


# ---------------------------------------------------------------------------
# UI: provider label escaped
# ---------------------------------------------------------------------------

def test_provider_label_escaped():
    src = _read(UI)
    # Must use escHtml(p.label...) not bare p.label
    assert "escHtml(p.label" in src, (
        "live_chat_ui.html: prov-title template must escape p.label with escHtml()"
    )
    # Must NOT have bare ${p.label||key} without escHtml
    assert "${p.label||key}" not in src, (
        "live_chat_ui.html: bare ${p.label||key} interpolation found — must use escHtml"
    )
