"""Local RAG indexing/search/export utilities for Vision.

This module builds a SQLite FTS5 index from a filesystem corpus (defaulting to
the Hugging Face bucket mirror at F:\\rag-v1\\data on Windows) and exposes:

- fast keyword retrieval for runtime grounding
- dataset exports for training/finetuning prep
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".json",
    ".jsonl",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".htm",
    ".xml",
    ".sql",
    ".sh",
    ".ps1",
    ".bat",
    ".toml",
    ".ini",
    ".cfg",
}

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".archon",
}


def _token_count(text: str) -> int:
    return max(1, len(text.split()))


def _safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _flatten_json(value: Any, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            lines.extend(_flatten_json(nested, new_prefix))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            new_prefix = f"{prefix}[{idx}]"
            lines.extend(_flatten_json(nested, new_prefix))
    else:
        rendered = str(value).strip()
        if rendered:
            lines.append(f"{prefix}: {rendered}" if prefix else rendered)
    return lines


def _chunk_text(text: str, chunk_size: int = 1400, overlap: int = 220) -> list[str]:
    cleaned = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not cleaned:
        return []

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(paragraph) <= chunk_size:
            current = paragraph
            continue

        start = 0
        while start < len(paragraph):
            end = min(len(paragraph), start + chunk_size)
            piece = paragraph[start:end].strip()
            if piece:
                chunks.append(piece)
            if end >= len(paragraph):
                break
            start = max(0, end - overlap)
        current = ""

    if current:
        chunks.append(current)

    return chunks


@dataclass
class RAGSearchHit:
    chunk_id: str
    rel_path: str
    abs_path: str
    score: float
    snippet: str
    content: str
    token_count: int


class VisionRAGManager:
    """RAG manager with SQLite FTS5 backend for local corpora."""

    def __init__(self, base_dir: Path, source_root: Path | None = None) -> None:
        self.base_dir = base_dir
        self.state_dir = self.base_dir / ".rag"
        self.db_path = self.state_dir / "knowledge.db"
        self.exports_dir = self.state_dir / "exports"
        self.source_root = self._resolve_source_root(source_root)

    @staticmethod
    def _resolve_source_root(explicit: Path | None) -> Path:
        if explicit:
            candidate = explicit.expanduser()
            if candidate.exists():
                return candidate

        env_workspace = os.environ.get("RAG_PLUGIN_WORKSPACE", "").strip()
        env_candidate = Path(env_workspace).expanduser() if env_workspace else None

        windows_default = Path(r"F:\rag-v1\data")
        windows_workspace = Path(r"F:\rag-v1")
        unix_default = Path.home() / "rag-v1" / "data"
        unix_workspace = Path.home() / "rag-v1"

        candidates = [
            env_candidate / "data" if env_candidate else None,
            env_candidate,
            windows_default,
            windows_workspace / "data",
            windows_workspace,
            unix_default,
            unix_workspace,
        ]

        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate

        return windows_default

    def _connect(self) -> sqlite3.Connection:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
              chunk_id TEXT PRIMARY KEY,
              rel_path TEXT NOT NULL,
              abs_path TEXT NOT NULL,
              source_type TEXT NOT NULL,
              content TEXT NOT NULL,
              char_count INTEGER NOT NULL,
              token_count INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(chunk_id UNINDEXED, rel_path, content, tokenize='unicode61');

            CREATE INDEX IF NOT EXISTS idx_chunks_rel_path ON chunks(rel_path);
            """
        )

    def _clear_index(self, conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM chunks;")
        conn.execute("DELETE FROM chunks_fts;")
        conn.execute("DELETE FROM meta;")

    def _extract_text(self, path: Path) -> tuple[str, str]:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            return "", "unsupported"

        if suffix in {".json", ".jsonl"}:
            if suffix == ".json":
                data = json.loads(_safe_read_text(path))
                return "\n".join(_flatten_json(data)), "json"

            lines: list[str] = []
            for raw in _safe_read_text(path).splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    lines.append(raw)
                    continue
                lines.extend(_flatten_json(data))
            return "\n".join(lines), "jsonl"

        if suffix in {".csv", ".tsv"}:
            delimiter = "\t" if suffix == ".tsv" else ","
            rows: list[str] = []
            with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
                reader = csv.reader(handle, delimiter=delimiter)
                for row in reader:
                    joined = " | ".join(cell.strip() for cell in row if cell.strip())
                    if joined:
                        rows.append(joined)
            return "\n".join(rows), "table"

        return _safe_read_text(path), "text"

    def _iter_source_files(self, max_files: int = 0) -> list[Path]:
        root = self.source_root
        if not root.exists():
            return []

        collected: list[Path] = []
        for candidate in root.rglob("*"):
            if max_files and len(collected) >= max_files:
                break
            if not candidate.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in candidate.parts):
                continue
            if candidate.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            try:
                if candidate.stat().st_size > 6 * 1024 * 1024:
                    continue
            except OSError:
                continue
            collected.append(candidate)

        return collected

    def build_index(
        self,
        *,
        max_files: int = 0,
        chunk_size: int = 1400,
        overlap: int = 220,
    ) -> dict[str, Any]:
        started = datetime.utcnow()
        files = self._iter_source_files(max_files=max_files)

        with self._connect() as conn:
            self._ensure_schema(conn)
            self._clear_index(conn)

            total_chunks = 0
            total_chars = 0
            now = datetime.utcnow().isoformat()

            for path in files:
                try:
                    text, source_type = self._extract_text(path)
                except Exception:
                    continue

                if not text.strip():
                    continue

                rel_path = str(path.relative_to(self.source_root)).replace("\\", "/")
                chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
                for idx, chunk in enumerate(chunks):
                    chunk_id = hashlib.sha1(f"{rel_path}:{idx}:{chunk[:120]}".encode("utf-8", "ignore")).hexdigest()
                    char_count = len(chunk)
                    token_count = _token_count(chunk)

                    conn.execute(
                        """
                        INSERT INTO chunks(chunk_id, rel_path, abs_path, source_type, content, char_count, token_count, created_at)
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (chunk_id, rel_path, str(path), source_type, chunk, char_count, token_count, now),
                    )
                    conn.execute(
                        "INSERT INTO chunks_fts(chunk_id, rel_path, content) VALUES(?, ?, ?)",
                        (chunk_id, rel_path, chunk),
                    )

                    total_chunks += 1
                    total_chars += char_count

            finished = datetime.utcnow()
            elapsed_ms = int((finished - started).total_seconds() * 1000)
            avg_chars = int(total_chars / total_chunks) if total_chunks else 0

            meta = {
                "source_root": str(self.source_root),
                "files_indexed": str(len(files)),
                "chunks_indexed": str(total_chunks),
                "average_chunk_chars": str(avg_chars),
                "updated_at": finished.isoformat(),
                "build_elapsed_ms": str(elapsed_ms),
                "schema_version": "1",
            }
            for key, value in meta.items():
                conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))

            conn.commit()

        return {
            "ok": True,
            "source_root": str(self.source_root),
            "files_indexed": len(files),
            "chunks_indexed": total_chunks,
            "average_chunk_chars": avg_chars,
            "build_elapsed_ms": elapsed_ms,
            "updated_at": finished.isoformat(),
            "db_path": str(self.db_path),
        }

    def status(self) -> dict[str, Any]:
        if not self.db_path.exists():
            return {
                "ok": True,
                "indexed": False,
                "source_root": str(self.source_root),
                "db_path": str(self.db_path),
                "message": "Index not built yet.",
            }

        with self._connect() as conn:
            self._ensure_schema(conn)
            chunk_count = int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
            meta_rows = conn.execute("SELECT key, value FROM meta").fetchall()
            meta = {k: v for k, v in meta_rows}

        return {
            "ok": True,
            "indexed": chunk_count > 0,
            "source_root": str(self.source_root),
            "db_path": str(self.db_path),
            "chunks_indexed": chunk_count,
            "meta": meta,
        }

    def search(self, query: str, *, limit: int = 8, include_content: bool = True) -> dict[str, Any]:
        cleaned_query = " ".join(query.split()).strip()
        if not cleaned_query:
            return {"ok": False, "error": "query is required", "results": []}

        if not self.db_path.exists():
            return {"ok": False, "error": "index not built", "results": []}

        limit = max(1, min(int(limit), 50))

        with self._connect() as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                """
                SELECT
                  c.chunk_id,
                  c.rel_path,
                  c.abs_path,
                  bm25(chunks_fts) AS score,
                  snippet(chunks_fts, 2, '[', ']', ' ... ', 22) AS snippet,
                  c.content,
                  c.token_count
                FROM chunks_fts
                JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
                WHERE chunks_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (cleaned_query, limit),
            ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            chunk_id, rel_path, abs_path, score, snippet, content, token_count = row
            results.append(
                {
                    "chunk_id": chunk_id,
                    "rel_path": rel_path,
                    "abs_path": abs_path,
                    "score": float(score),
                    "snippet": snippet,
                    "token_count": int(token_count),
                    "content": content if include_content else "",
                }
            )

        return {
            "ok": True,
            "query": cleaned_query,
            "limit": limit,
            "results": results,
            "result_count": len(results),
        }

    def export_training_data(self, *, max_examples: int = 0) -> dict[str, Any]:
        if not self.db_path.exists():
            return {"ok": False, "error": "index not built"}

        with self._connect() as conn:
            self._ensure_schema(conn)
            rows = conn.execute("SELECT chunk_id, rel_path, content FROM chunks ORDER BY rel_path, chunk_id").fetchall()

        if max_examples > 0:
            rows = rows[:max_examples]

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        export_dir = self.exports_dir / timestamp
        export_dir.mkdir(parents=True, exist_ok=True)

        kb_jsonl = export_dir / "knowledge_base.jsonl"
        corpus_jsonl = export_dir / "training_corpus.jsonl"
        sft_train = export_dir / "instruction_train.jsonl"
        sft_val = export_dir / "instruction_val.jsonl"

        train_count = 0
        val_count = 0

        with (
            kb_jsonl.open("w", encoding="utf-8") as kb_handle,
            corpus_jsonl.open("w", encoding="utf-8") as corpus_handle,
            sft_train.open("w", encoding="utf-8") as train_handle,
            sft_val.open("w", encoding="utf-8") as val_handle,
        ):
            for chunk_id, rel_path, content in rows:
                metadata = {
                    "chunk_id": chunk_id,
                    "source": rel_path,
                    "source_root": str(self.source_root),
                }

                kb_record = {"id": chunk_id, "text": content, "metadata": metadata}
                kb_handle.write(json.dumps(kb_record, ensure_ascii=False) + "\n")

                corpus_record = {"text": content, "metadata": metadata}
                corpus_handle.write(json.dumps(corpus_record, ensure_ascii=False) + "\n")

                prompt = (
                    f"You are given a source chunk from `{rel_path}`. "
                    "Return the key facts exactly as grounded in the provided context."
                )
                sft_record = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a retrieval-grounded assistant. Never invent facts.",
                        },
                        {
                            "role": "user",
                            "content": f"{prompt}\n\nContext:\n{content}",
                        },
                        {
                            "role": "assistant",
                            "content": content,
                        },
                    ],
                    "metadata": metadata,
                }

                split_hash = int(hashlib.sha1(chunk_id.encode("utf-8")).hexdigest(), 16) % 10
                if split_hash == 0:
                    val_handle.write(json.dumps(sft_record, ensure_ascii=False) + "\n")
                    val_count += 1
                else:
                    train_handle.write(json.dumps(sft_record, ensure_ascii=False) + "\n")
                    train_count += 1

        manifest = {
            "ok": True,
            "export_dir": str(export_dir),
            "knowledge_base_jsonl": str(kb_jsonl),
            "training_corpus_jsonl": str(corpus_jsonl),
            "instruction_train_jsonl": str(sft_train),
            "instruction_val_jsonl": str(sft_val),
            "records": len(rows),
            "train_records": train_count,
            "val_records": val_count,
            "generated_at": datetime.utcnow().isoformat(),
        }

        (export_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest
