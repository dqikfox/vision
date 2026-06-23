"""
test_cycle19.py — Structural tests for cycle-19 improvements

Tests verify:
1. Automation routine 'command' action uses shlex.split + shell=False (no injection)
2. find_files tool calls _validate_tool_path() before os.walk()
3. browser_scroll whitelists direction ('up'/'down')
4. browser_eval blocks eval(), Function(), setTimeout(), setInterval(), document.write(), innerHTML=, WebSocket()
5. /api/rag/index has localhost-only guard
6. /api/rag/export-training has localhost-only guard + takes Request param
7. CI quality.yml bandit uses -ll flag (only high severity)
"""

import re


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


APP = "live_chat_app.py"
YML = ".github/workflows/quality.yml"


# ---------------------------------------------------------------------------
# 1. Automation routine 'command' action — shell=False + shlex
# ---------------------------------------------------------------------------


def test_automation_command_no_shell_true():
    """Automation 'command' action must not use shell=True as a subprocess argument."""
    src = _read(APP)
    fn = re.search(
        r'elif action == "command".*?(?=\n    elif action == |\n    else:)',
        src,
        re.DOTALL,
    )
    assert fn is not None, "automation 'command' action block not found"
    body = fn.group()
    # Remove comments before checking — the comment text may contain 'shell=True'
    body_no_comments = re.sub(r"#[^\n]*", "", body)
    assert "shell=True" not in body_no_comments, "Automation 'command' action must not use shell=True (injection risk)"
    assert "shell=False" in body_no_comments, "Automation 'command' action must explicitly set shell=False"


def test_automation_command_uses_shlex():
    """Automation 'command' action must use shlex.split to parse command string."""
    src = _read(APP)
    fn = re.search(
        r'elif action == "command".*?(?=\n    elif action == |\n    else:)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "shlex.split" in body or "shlex" in body, (
        "Automation 'command' action must use shlex.split() to tokenize the command"
    )


# ---------------------------------------------------------------------------
# 2. find_files — _validate_tool_path() called before os.walk
# ---------------------------------------------------------------------------


def test_find_files_validates_path():
    """find_files tool must call _validate_tool_path() before os.walk()."""
    src = _read(APP)
    block = re.search(
        r'elif name == "find_files".*?(?=\n    elif name == |\n    # ──)',
        src,
        re.DOTALL,
    )
    assert block is not None, "find_files handler not found"
    body = block.group()
    assert "_validate_tool_path(" in body, "find_files must call _validate_tool_path() to prevent path traversal"
    validate_pos = body.find("_validate_tool_path(")
    walk_pos = body.find("os.walk(")
    assert validate_pos < walk_pos, "_validate_tool_path() must be called BEFORE os.walk()"


# ---------------------------------------------------------------------------
# 3. browser_scroll — whitelist direction
# ---------------------------------------------------------------------------


def test_browser_scroll_whitelists_direction():
    """browser_scroll must reject directions other than 'up' or 'down'."""
    src = _read(APP)
    block = re.search(
        r'elif name == "browser_scroll".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None, "browser_scroll handler not found"
    body = block.group()
    assert '"up"' in body and '"down"' in body, "browser_scroll must whitelist 'up' and 'down' directions"
    # Should return an error for invalid directions
    assert "direction not in" in body or "direction must be" in body, (
        "browser_scroll must validate direction and return an error for invalid values"
    )


# ---------------------------------------------------------------------------
# 4. browser_eval — expanded dangerous JS patterns
# ---------------------------------------------------------------------------


def test_browser_eval_blocks_eval():
    """browser_eval must block eval() calls."""
    src = _read(APP)
    block = re.search(
        r'elif name == "browser_eval".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert r"eval\s*\(" in body, "browser_eval must block eval() calls"


def test_browser_eval_blocks_settimeout():
    """browser_eval must block setTimeout/setInterval."""
    src = _read(APP)
    block = re.search(
        r'elif name == "browser_eval".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "setTimeout" in body, "browser_eval must block setTimeout"
    assert "setInterval" in body, "browser_eval must block setInterval"


def test_browser_eval_blocks_document_write():
    """browser_eval must block document.write."""
    src = _read(APP)
    block = re.search(
        r'elif name == "browser_eval".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "document.write" in body or r"document\.write" in body, "browser_eval must block document.write"


def test_browser_eval_blocks_inner_html():
    """browser_eval must block .innerHTML= assignments."""
    src = _read(APP)
    block = re.search(
        r'elif name == "browser_eval".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "innerHTML" in body, "browser_eval must block .innerHTML= assignments"


def test_browser_eval_blocks_websocket():
    """browser_eval must block WebSocket() constructor."""
    src = _read(APP)
    block = re.search(
        r'elif name == "browser_eval".*?(?=\n    elif name == )',
        src,
        re.DOTALL,
    )
    assert block is not None
    body = block.group()
    assert "WebSocket" in body, "browser_eval must block WebSocket() usage"


# ---------------------------------------------------------------------------
# 5. /api/rag/index — localhost-only guard
# ---------------------------------------------------------------------------


def test_rag_index_localhost_guard():
    """POST /api/rag/index must reject non-localhost clients with 403."""
    src = _read(APP)
    ep = re.search(
        r'@app\.post\("/api/rag/index"\).*?async def api_rag_index\(.*?(?=\n@app\.)',
        src,
        re.DOTALL,
    )
    assert ep is not None, "/api/rag/index endpoint not found"
    body = ep.group()
    assert "403" in body, "/api/rag/index must return 403 for non-localhost clients"
    assert "127.0.0.1" in body or "localhost" in body, "/api/rag/index must check client IP against localhost values"


def test_rag_index_takes_request_param():
    """POST /api/rag/index must accept Request to read client host."""
    src = _read(APP)
    assert (
        "async def api_rag_index(payload: dict[str, Any], request: Request)" in src or "async def api_rag_index(" in src
    ), "/api/rag/index must accept Request param"
    block = re.search(r"async def api_rag_index\(([^)]*)\)", src)
    assert block is not None
    assert "Request" in block.group(), "/api/rag/index must accept Request param"


# ---------------------------------------------------------------------------
# 6. /api/rag/export-training — localhost-only guard
# ---------------------------------------------------------------------------


def test_rag_export_localhost_guard():
    """POST /api/rag/export-training must reject non-localhost clients with 403."""
    src = _read(APP)
    ep = re.search(
        r'@app\.post\("/api/rag/export-training"\).*?async def api_rag_export_training\(.*?(?=\n@app\.)',
        src,
        re.DOTALL,
    )
    assert ep is not None, "/api/rag/export-training endpoint not found"
    body = ep.group()
    assert "403" in body, "/api/rag/export-training must return 403 for non-localhost"
    assert "127.0.0.1" in body or "localhost" in body, (
        "/api/rag/export-training must check client IP against localhost values"
    )


def test_rag_export_takes_request_param():
    """POST /api/rag/export-training must accept Request param."""
    src = _read(APP)
    block = re.search(r"async def api_rag_export_training\(([^)]*)\)", src)
    assert block is not None
    assert "Request" in block.group(), "/api/rag/export-training must accept Request param"


# ---------------------------------------------------------------------------
# 7. CI — bandit uses -ll flag
# ---------------------------------------------------------------------------


def test_ci_bandit_uses_severity_filter():
    """CI bandit scan must use -ll to limit failures to high-severity findings."""
    src = _read(YML)
    bandit_line = next(
        (line for line in src.splitlines() if "bandit" in line and "run" not in line.lower().split(":")[0]),
        None,
    )
    # Check for -ll flag in the bandit run command
    bandit_block = re.search(r"bandit.*?(?=\n\n|\Z)", src, re.DOTALL)
    assert bandit_block is not None, "bandit step not found in quality.yml"
    assert "-ll" in src, "bandit must use -ll flag to only fail on HIGH severity findings"
