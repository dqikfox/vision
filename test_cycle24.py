"""
test_cycle24.py — Structural tests for cycle-24 improvements

Tests verify:
1. list_files calls _validate_tool_path(fpath) before iterating the directory
2. list_files path validation is consistent with other file tools (read_file, write_file, find_files)
"""

import re

APP = "live_chat_app.py"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_list_files_calls_validate_tool_path():
    """list_files must call _validate_tool_path(fpath) to prevent path traversal."""
    src = _read(APP)
    fn = re.search(
        r'elif name == "list_files":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None, "list_files handler not found"
    body = fn.group(1)
    assert "_validate_tool_path" in body, (
        "list_files must call _validate_tool_path(fpath) — without it, "
        "an attacker can traverse to any directory on the system"
    )


def test_list_files_validate_before_listdir():
    """_validate_tool_path must be called before p.iterdir() / _listdir()."""
    src = _read(APP)
    fn = re.search(
        r'elif name == "list_files":(.*?)(?=\n    elif name|\Z)',
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    validate_pos = body.find("_validate_tool_path")
    listdir_pos = body.find("_listdir")
    assert validate_pos != -1, "_validate_tool_path call not found in list_files"
    assert listdir_pos != -1, "_listdir not found in list_files"
    assert validate_pos < listdir_pos, (
        "_validate_tool_path must be called before _listdir() executes"
    )


def test_file_tools_consistently_validate_path():
    """All file-listing/reading/writing tools must use _validate_tool_path."""
    src = _read(APP)
    tools_to_check = ["list_files", "read_file", "find_files"]
    for tool in tools_to_check:
        fn = re.search(
            rf'elif name == "{re.escape(tool)}":(.*?)(?=\n    elif name|\Z)',
            src,
            re.DOTALL,
        )
        assert fn is not None, f"{tool} handler not found"
        body = fn.group(1)
        assert "_validate_tool_path" in body, (
            f"{tool} is missing _validate_tool_path — inconsistent with other file tools"
        )
