"""
test_cycle28.py — Structural tests for cycle-28 improvements

Tests verify:
1. _run_tool WS dispatch uses _tracked_task
2. api_rag_index wraps int() params in try/except → 400
3. api_rag_search wraps int() params in try/except → 400
4. api_rag_export_training wraps int() params in try/except → 400
5. live_chat_ui.html escHtml(k) in onclick saveCfgKey button
6. live_chat_ui.html escHtml(provider) in toast notification
"""

import re

APP = "live_chat_app.py"
UI = "live_chat_ui.html"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. _run_tool WS dispatch — must use _tracked_task
# ---------------------------------------------------------------------------


def test_run_tool_uses_tracked_task():
    src = _read(APP)
    assert "asyncio.create_task(_run_tool(" not in src, (
        "WS tool dispatch must use _tracked_task(_run_tool(...)) "
        "not bare asyncio.create_task()"
    )
    assert "_tracked_task(_run_tool(" in src, (
        "_tracked_task(_run_tool(...)) must be present in WS handler"
    )


# ---------------------------------------------------------------------------
# 2. api_rag_index — int() params wrapped in try/except
# ---------------------------------------------------------------------------


def test_rag_index_int_params_guarded():
    src = _read(APP)
    fn = re.search(
        r"async def api_rag_index\(.*?(?=\n@app\.|\nasync def |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "api_rag_index not found"
    body = fn.group()
    assert "int(payload.get" in body, "api_rag_index must parse int params"
    # Must have try/except around the int() calls
    try_pos = body.find("try:")
    int_pos = body.find("int(payload.get")
    except_pos = body.find("(ValueError, TypeError)")
    assert try_pos != -1, "api_rag_index must wrap int() parsing in try block"
    assert except_pos != -1, "api_rag_index must catch ValueError/TypeError"
    assert try_pos < int_pos < except_pos or try_pos < int_pos, (
        "int() parsing must be inside the try block"
    )


def test_rag_index_returns_400_on_bad_params():
    src = _read(APP)
    fn = re.search(
        r"async def api_rag_index\(.*?(?=\n@app\.|\nasync def |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "status_code=400" in body, (
        "api_rag_index must return HTTP 400 on invalid integer parameters"
    )


# ---------------------------------------------------------------------------
# 3. api_rag_search — int() params wrapped
# ---------------------------------------------------------------------------


def test_rag_search_int_params_guarded():
    src = _read(APP)
    fn = re.search(
        r"async def api_rag_search\(.*?(?=\n@app\.|\nasync def |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "api_rag_search not found"
    body = fn.group()
    assert "(ValueError, TypeError)" in body, (
        "api_rag_search must catch ValueError/TypeError from int() parsing"
    )
    assert "status_code=400" in body, (
        "api_rag_search must return HTTP 400 on invalid parameters"
    )


# ---------------------------------------------------------------------------
# 4. api_rag_export_training — int() params wrapped
# ---------------------------------------------------------------------------


def test_rag_export_int_params_guarded():
    src = _read(APP)
    fn = re.search(
        r"async def api_rag_export_training\(.*?(?=\n@app\.|\nasync def |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "api_rag_export_training not found"
    body = fn.group()
    assert "(ValueError, TypeError)" in body, (
        "api_rag_export_training must catch ValueError/TypeError from int() parsing"
    )
    assert "status_code=400" in body, (
        "api_rag_export_training must return HTTP 400 on invalid parameters"
    )


# ---------------------------------------------------------------------------
# 5. UI — escHtml(k) in onclick saveCfgKey
# ---------------------------------------------------------------------------


def test_ui_save_cfg_key_onclick_escaped():
    src = _read(UI)
    # The old unescaped pattern must be gone
    assert "onclick=\"saveCfgKey('${k}')\"" not in src, (
        "Provider key in onclick must be escaped: saveCfgKey('${escHtml(k)}')"
    )
    assert "escHtml(k)" in src, (
        "saveCfgKey onclick must use escHtml(k) to prevent XSS"
    )


# ---------------------------------------------------------------------------
# 6. UI — escHtml(provider) in toast
# ---------------------------------------------------------------------------


def test_ui_key_saved_toast_escaped():
    src = _read(UI)
    # The unescaped toast pattern must be gone in saveCfgKey function
    fn = re.search(
        r"function saveCfgKey\(provider\)(.*?)(?=\nfunction |\Z)",
        src,
        re.DOTALL,
    )
    assert fn is not None, "saveCfgKey function not found"
    body = fn.group(1)
    assert "escHtml(provider)" in body, (
        "toast in saveCfgKey must use escHtml(provider) to prevent XSS"
    )
    assert "${provider}" not in body or "escHtml" in body, (
        "Raw ${provider} in toast is unescaped — must use escHtml"
    )
