"""
test_rag_batch_inserts.py — Tests for perf: batch SQLite inserts in RAG index builder.

Closes: #14

Tests verify:
1. build_index() uses executemany (not per-chunk execute) for chunks, chunks_fts, and meta
2. build_index() correctly inserts all chunks when using executemany
3. Meta table is correctly populated via executemany
"""

import re
import sqlite3
import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _build_index_source() -> str:
    """Return the source of build_index() from vision_rag.py."""
    src = _read("vision_rag.py")
    idx = src.index("def build_index(")
    # Find the next top-level def/class after build_index
    next_def = re.search(r"\n    def ", src[idx + 1:])
    end = (idx + 1 + next_def.start()) if next_def else len(src)
    return src[idx:end]


def _make_rag(tmp_path: Path):
    """Create a VisionRAGManager with a temp base dir and source root."""
    from vision_rag import VisionRAGManager
    source = tmp_path / "src"
    source.mkdir()
    return VisionRAGManager(base_dir=tmp_path, source_root=source)


# ---------------------------------------------------------------------------
# 1. Structural: executemany used for all three tables
# ---------------------------------------------------------------------------


class TestBuildIndexUsesExecuteMany:
    def test_chunks_table_uses_executemany(self):
        """build_index() must use executemany for the chunks table."""
        fn_src = _build_index_source()
        assert "conn.executemany" in fn_src, (
            "build_index() must use conn.executemany() for batch inserts"
        )

    def test_chunks_fts_table_uses_executemany(self):
        """build_index() must use executemany for the chunks_fts FTS table."""
        fn_src = _build_index_source()
        assert "chunks_fts" in fn_src
        # executemany must be used (not just per-row execute) for fts_rows
        assert "fts_rows" in fn_src, "fts_rows accumulator list must be present"
        # Confirm executemany is called with fts_rows
        assert re.search(r"conn\.executemany\(.*?fts_rows", fn_src, re.DOTALL), (
            "conn.executemany() must be called with fts_rows"
        )

    def test_meta_table_uses_executemany(self):
        """build_index() must use executemany for the meta table (not a for-loop of execute)."""
        fn_src = _build_index_source()
        # Must NOT have a for-loop calling execute for meta inserts
        assert not re.search(
            r"for\s+\w+.*?in\s+meta.*?conn\.execute",
            fn_src,
            re.DOTALL,
        ), "build_index() must not use a per-item execute loop for meta inserts"
        # Must use executemany with meta
        assert re.search(r"conn\.executemany\(.*?meta", fn_src, re.DOTALL), (
            "build_index() must use conn.executemany() for meta table inserts"
        )

    def test_chunks_rows_accumulator_present(self):
        """chunks_rows list accumulator must be present in build_index()."""
        fn_src = _build_index_source()
        assert "chunks_rows" in fn_src, (
            "chunks_rows accumulator list must be present in build_index()"
        )

    def test_no_per_chunk_execute_for_inserts(self):
        """build_index() must not use conn.execute() with INSERT INTO chunks inside the loop."""
        fn_src = _build_index_source()
        # Look for execute (not executemany) with INSERT INTO chunks
        per_chunk_insert = re.search(
            r"conn\.execute\s*\(\s*[\"']INSERT\s+(OR\s+REPLACE\s+)?INTO\s+chunks",
            fn_src,
        )
        assert per_chunk_insert is None, (
            "build_index() must not use conn.execute() for per-chunk INSERT INTO chunks; "
            "use executemany() instead"
        )


# ---------------------------------------------------------------------------
# 2. Functional: build_index() correctly inserts all chunks via executemany
# ---------------------------------------------------------------------------


class TestBuildIndexCorrectness:
    def test_all_chunks_inserted(self, tmp_path):
        """build_index() must insert all chunks into the chunks table."""
        mgr = _make_rag(tmp_path)
        text = "word " * 300  # enough for multiple chunks
        (tmp_path / "src" / "doc.txt").write_text(text, encoding="utf-8")

        result = mgr.build_index()

        assert result["ok"] is True
        assert result["chunks_indexed"] > 0

        with mgr._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == result["chunks_indexed"]

    def test_fts_rows_match_chunks(self, tmp_path):
        """chunks_fts must contain the same number of rows as the chunks table."""
        mgr = _make_rag(tmp_path)
        (tmp_path / "src" / "doc.txt").write_text("hello world " * 200, encoding="utf-8")

        mgr.build_index()

        with mgr._connect() as conn:
            chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            fts_count = conn.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]

        assert chunk_count > 0
        assert fts_count == chunk_count

    def test_meta_all_keys_written(self, tmp_path):
        """All expected meta keys must be present after build_index()."""
        mgr = _make_rag(tmp_path)
        (tmp_path / "src" / "doc.txt").write_text("some text " * 100, encoding="utf-8")

        mgr.build_index()

        with mgr._connect() as conn:
            rows = conn.execute("SELECT key FROM meta").fetchall()
        keys = {r[0] for r in rows}

        expected = {
            "source_root",
            "files_indexed",
            "chunks_indexed",
            "average_chunk_chars",
            "updated_at",
            "build_elapsed_ms",
            "schema_version",
        }
        assert expected.issubset(keys), (
            f"Missing meta keys: {expected - keys}"
        )

    def test_multiple_files_all_indexed(self, tmp_path):
        """build_index() must index all files when multiple files are present."""
        mgr = _make_rag(tmp_path)
        for i in range(3):
            (tmp_path / "src" / f"file{i}.txt").write_text(
                f"content for file {i} " * 100, encoding="utf-8"
            )

        result = mgr.build_index()

        assert result["ok"] is True
        assert result["files_indexed"] == 3
        assert result["chunks_indexed"] > 0

        with mgr._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == result["chunks_indexed"]
