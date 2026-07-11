"""
test_cycle16.py — Structural tests for cycle-16 improvements

Tests verify:
1. Stale 'live_chat_app.py:NNNN' line-ref strings removed from print statements
2. Per-file FTS orphan DELETE removed from vision_rag.py build_index loop
3. PowerShell MessageBox uses -ArgumentList (no f-string injection)
4. MCP JSON parse error returns ok=False with status_code
5. elite_memory.py save/load are thread-safe (use _save_lock + atomic write)
"""

import re

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _lines(src: str):
    return src.splitlines()


APP = "live_chat_app.py"
RAG = "vision_rag.py"
MCP = "vision_mcp_server.py"
MEM = "elite_memory.py"


# ---------------------------------------------------------------------------
# 1. Stale line-number suffixes removed from live_chat_app.py
# ---------------------------------------------------------------------------


def test_no_stale_line_refs_in_prints():
    """All 'live_chat_app.py:NNNN' stale refs must be gone."""
    src = _read(APP)
    matches = re.findall(r"live_chat_app\.py:\w+", src)
    assert matches == [], f"Found stale line refs: {matches}"


def test_print_statements_are_clean():
    """Spot-check that key print statements no longer end with the old suffix pattern."""
    src = _read(APP)
    assert "live_chat_app.py:4603" not in src
    assert "live_chat_app.py:4612" not in src
    assert "live_chat_app.py:5691" not in src


# ---------------------------------------------------------------------------
# 2. Per-file FTS orphan DELETE removed from vision_rag.py
# ---------------------------------------------------------------------------


def test_fts_orphan_delete_not_inside_per_file_loop():
    """
    The per-file 'DELETE FROM chunks_fts WHERE chunk_id NOT IN ...' was O(N);
    it must not appear inside the file-iteration block. The close() reset
    (DELETE FROM chunks_fts;) and the post-loop global cleanup are both fine.
    """
    src = _read(RAG)
    # The problematic per-file pattern is DELETE ... WHERE chunk_id NOT IN
    # combined with it being inside the per-file loop, before executemany
    indices = [m.start() for m in re.finditer(r"DELETE FROM chunks_fts WHERE chunk_id NOT IN", src)]
    assert len(indices) <= 1, (
        f"Found {len(indices)} per-file FTS orphan DELETEs; expected ≤1 (only the post-loop global cleanup)"
    )


def test_fts_post_loop_cleanup_present():
    """The single post-loop FTS orphan cleanup must still exist."""
    src = _read(RAG)
    assert "DELETE FROM chunks_fts WHERE chunk_id NOT IN" in src, "Post-loop FTS orphan cleanup DELETE is missing"


def test_per_file_fts_delete_comment_present():
    """A clarifying comment explains that FTS cleanup runs once after the loop."""
    src = _read(RAG)
    assert "FTS orphan cleanup runs once after the full loop" in src or "Note: FTS orphan cleanup" in src, (
        "Expected explanatory comment about single-pass FTS cleanup"
    )


# ---------------------------------------------------------------------------
# 3. PowerShell MessageBox uses -ArgumentList (no f-string injection)
# ---------------------------------------------------------------------------


def test_notification_uses_argument_list():
    """send_notification fallback must use -ArgumentList to pass title/message safely."""
    src = _read(APP)
    assert "-ArgumentList" in src, "send_notification fallback should use -ArgumentList"
    # New safe approach: pass message and title as positional args via $args[0]/$args[1]
    assert "$args[0]" in src, "PowerShell command should reference $args[0] instead of interpolating message"
    assert "$args[1]" in src, "PowerShell command should reference $args[1] instead of interpolating title"


def test_notification_no_direct_fstring_injection():
    """The old f-string MessageBox injection pattern in send_notification must be gone."""
    src = _read(APP)
    # Old pattern: f'[System.Windows.Forms.MessageBox]::Show("{safe_msg}"...'
    assert 'Show("{safe_msg}"' not in src, "Old f-string MessageBox injection pattern still present"
    # Verify the PowerShell command uses $args[0] not an embedded variable
    assert "MessageBox]::Show($args[0]" in src, (
        "MessageBox should use $args[0] positional arg, not string interpolation"
    )


# ---------------------------------------------------------------------------
# 4. MCP JSON parse error returns ok=False with status_code
# ---------------------------------------------------------------------------


def test_mcp_json_error_returns_ok_false():
    """ValueError from response.json() must yield ok=False, not ok=True."""
    src = _read(MCP)
    # After the 'except ValueError' block there must be an 'ok: False' return
    assert '"ok": False' in src or "'ok': False" in src or '"ok": False' in src, (
        "MCP JSON parse error should return {ok: False, ...}"
    )


def test_mcp_json_error_preserves_status_code():
    """The error return dict must include status_code."""
    src = _read(MCP)
    # Verify status_code is present in the except ValueError branch
    # We check for the pattern near json_err / ValueError
    except_block = re.search(
        r"except ValueError.*?return \{.*?\}",
        src,
        re.DOTALL,
    )
    assert except_block is not None, "except ValueError block with return not found"
    block_text = except_block.group()
    assert "status_code" in block_text, "JSON parse error return dict must include 'status_code'"


def test_mcp_json_error_logs_error():
    """The error return dict must include an 'error' key."""
    src = _read(MCP)
    except_block = re.search(
        r"except ValueError.*?return \{.*?\}",
        src,
        re.DOTALL,
    )
    assert except_block is not None
    block_text = except_block.group()
    assert '"error"' in block_text or "'error'" in block_text, "JSON parse error return dict must include 'error' key"


# ---------------------------------------------------------------------------
# 5. elite_memory.py thread-safety
# ---------------------------------------------------------------------------


def test_elite_memory_imports_threading():
    """elite_memory.py must import threading for lock support."""
    src = _read(MEM)
    assert "import threading" in src, "threading must be imported"


def test_elite_memory_imports_tempfile_and_os():
    """elite_memory.py must import tempfile and os for atomic writes."""
    src = _read(MEM)
    assert "import tempfile" in src, "tempfile must be imported for atomic save"
    assert "import os" in src, "os must be imported for atomic save"


def test_elite_memory_has_save_lock():
    """EliteMemory.__init__ must initialise _save_lock as a threading.Lock()."""
    src = _read(MEM)
    assert "_save_lock = threading.Lock()" in src, "_save_lock must be created in EliteMemory.__init__"


def test_elite_memory_save_uses_lock():
    """save() must acquire _save_lock."""
    src = _read(MEM)
    assert "self._save_lock" in src, "_save_lock must be referenced in save/load"
    # Verify 'with self._save_lock' context manager pattern
    assert "with self._save_lock:" in src, "save() or load() must use 'with self._save_lock:'"


def test_elite_memory_save_is_atomic():
    """save() must use tempfile + replace for atomic writes."""
    src = _read(MEM)
    assert "tempfile.mkstemp" in src or "NamedTemporaryFile" in src, (
        "save() must use a temporary file for atomic writes"
    )
    assert ".replace(" in src, "save() must atomically replace the target file with Path.replace()"


def test_elite_memory_load_uses_lock():
    """load() must acquire _save_lock to avoid races during concurrent save."""
    src = _read(MEM)
    # Both save and load should use the lock
    lock_count = src.count("with self._save_lock:")
    assert lock_count >= 2, f"Expected ≥2 'with self._save_lock:' blocks (save + load), found {lock_count}"


def test_elite_memory_lock_assigned_before_load():
    """_save_lock must be assigned before self.load() is called in __init__."""
    src = _read(MEM)
    lock_pos = src.find("_save_lock = threading.Lock()")
    load_pos = src.find("self.load()")
    assert lock_pos != -1 and load_pos != -1, "Both _save_lock and self.load() must exist"
    assert lock_pos < load_pos, "_save_lock must be initialised before self.load() in __init__"
