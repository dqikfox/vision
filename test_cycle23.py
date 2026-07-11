"""
test_cycle23.py — Structural tests for cycle-23 improvements

Tests verify:
1. /api/tool/execute wraps request.json() in try/except → 400 on bad JSON
2. type_text tool rejects text longer than 10 000 chars
3. execute_python tool rejects code longer than 50 000 chars
4. asyncio.create_task(_always_learn_step) adds done callbacks for error logging
5. transcribe() temp file creation is inside the try block (finally always cleans up)
6. list_files validates pattern string (no slashes/NUL, max 256 chars)
"""

import re

APP = "live_chat_app.py"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. tool_execute endpoint JSON parse error handling
# ---------------------------------------------------------------------------


def test_tool_execute_json_parse_try_except():
    src = _read(APP)
    fn = re.search(
        r"async def tool_execute\(.*?(?=\n@app\.|\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None, "tool_execute endpoint not found"
    body = fn.group()
    assert "request.json()" in body, "tool_execute must call request.json()"
    # Must be inside a try block
    try_pos = body.find("try:")
    json_pos = body.find("request.json()")
    assert try_pos != -1, "tool_execute must have a try block around request.json()"
    assert json_pos > try_pos, "request.json() must be inside the try block"


def test_tool_execute_returns_400_on_bad_json():
    src = _read(APP)
    fn = re.search(
        r"async def tool_execute\(.*?(?=\n@app\.|\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    assert "status_code=400" in body, "tool_execute must return HTTP 400 when JSON parse fails"


# ---------------------------------------------------------------------------
# 2. type_text length cap
# ---------------------------------------------------------------------------


def test_type_text_has_length_cap():
    src = _read(APP)
    fn = re.search(
        r'elif name == "type_text":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None, "type_text handler not found"
    body = fn.group(1)
    assert "len(text)" in body, "type_text must check len(text)"
    assert "10_000" in body or "10000" in body, "type_text must cap at 10 000 chars"


def test_type_text_returns_error_on_oversize():
    src = _read(APP)
    fn = re.search(
        r'elif name == "type_text":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    # Should return an error (via _tool_err or a return statement) when too long
    assert "_tool_err" in body or "return f" in body, (
        "type_text must return an error message when text exceeds length cap"
    )


# ---------------------------------------------------------------------------
# 3. execute_python code length cap
# ---------------------------------------------------------------------------


def test_execute_python_has_length_cap():
    src = _read(APP)
    fn = re.search(
        r'elif name == "execute_python":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None, "execute_python handler not found"
    body = fn.group(1)
    assert "len(code)" in body, "execute_python must check len(code)"
    assert "50_000" in body or "50000" in body, "execute_python must cap at 50 000 chars"


def test_execute_python_error_before_execution():
    src = _read(APP)
    fn = re.search(
        r'elif name == "execute_python":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    cap_pos = body.find("len(code)")
    exec_pos = body.find("exec(")
    assert cap_pos != -1
    assert exec_pos != -1
    assert cap_pos < exec_pos, "Code length check must appear before exec() call"


# ---------------------------------------------------------------------------
# 4. asyncio.create_task done callbacks for _always_learn_step
# ---------------------------------------------------------------------------


def test_always_learn_tasks_have_done_callbacks():
    src = _read(APP)
    # Count create_task calls for _always_learn_step
    task_sites = list(
        re.finditer(
            r"asyncio\.create_task\(_always_learn_step\(",
            src,
        )
    )
    assert len(task_sites) >= 3, f"Expected at least 3 _always_learn_step task sites, found {len(task_sites)}"
    # Each site should be followed by add_done_callback within 300 chars
    for m in task_sites:
        nearby = src[m.start() : m.start() + 350]
        assert "add_done_callback" in nearby, (
            f"asyncio.create_task at offset {m.start()} must have add_done_callback "
            "to capture exceptions from _always_learn_step"
        )


def test_always_learn_callback_logs_exceptions():
    src = _read(APP)
    # The callbacks should call write_log
    callbacks = list(re.finditer(r"add_done_callback\(", src))
    for cb in callbacks:
        nearby = src[cb.start() : cb.start() + 300]
        if "always_learn" in src[max(0, cb.start() - 200) : cb.start()]:
            assert "write_log" in nearby or "exception" in nearby.lower(), (
                "add_done_callback for always_learn must log the exception"
            )


# ---------------------------------------------------------------------------
# 5. transcribe temp file inside try block
# ---------------------------------------------------------------------------


def test_transcribe_tempfile_inside_try():
    src = _read(APP)
    # Find the transcribe-related NamedTemporaryFile creation
    wav_match = re.search(
        r"NamedTemporaryFile\(suffix=\"\.wav\".*?\)",
        src,
    )
    assert wav_match is not None, "NamedTemporaryFile(.wav) not found in transcribe"
    file_pos = wav_match.start()
    # Find the enclosing try block (search backwards from file_pos)
    code_before = src[:file_pos]
    # Find the last 'try:' before the NamedTemporaryFile call
    try_matches = list(re.finditer(r"\n    try:\n", code_before))
    assert try_matches, "No try block found before NamedTemporaryFile in transcribe"
    last_try_pos = try_matches[-1].start()
    # Also find the matching finally (search forward from try pos)
    code_from_try = src[last_try_pos : last_try_pos + 5000]
    assert "finally:" in code_from_try, "The try block containing NamedTemporaryFile must have a finally clause"
    assert "os.unlink(path)" in code_from_try, "The finally block must unlink the temp file"


# ---------------------------------------------------------------------------
# 6. list_files pattern validation
# ---------------------------------------------------------------------------


def test_list_files_validates_pattern_type():
    src = _read(APP)
    fn = re.search(
        r'elif name == "list_files":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None, "list_files handler not found"
    body = fn.group(1)
    assert "pattern" in body, "list_files must use the pattern parameter"
    assert "isinstance(pattern" in body or "len(pattern)" in body, "list_files must validate the pattern parameter"


def test_list_files_blocks_path_separators_in_pattern():
    src = _read(APP)
    fn = re.search(
        r'elif name == "list_files":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    # Must reject slash/backslash in pattern
    assert (
        '"/"' in body
        or "'/'" in body
        or '"\\\\"' in body
        or "'\\\\'" in body
        or '"\\\\"' in body
        or "sep" in body
        or "\\\\" in body
    ), "list_files pattern validation must block path separator characters"


def test_list_files_pattern_max_length():
    src = _read(APP)
    fn = re.search(
        r'elif name == "list_files":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    assert "256" in body or "len(pattern)" in body, "list_files must enforce a maximum pattern length"
