"""
vision_rag_integration.py — Vision RAG Integration Layer
========================================================
Integrates Vision with the local Ollama + Chroma RAG system.

This module provides:
  1. Direct Chroma queries for fast retrieval
  2. Full RAG pipeline with Ollama answer generation
  3. Context-aware query augmentation
  4. Result formatting for Vision consumption

Architecture
------------
  Vision RAG Integration
    ├─ ChromaClient       ← connects to existing Chroma DB
    ├─ OllamaClient       ← uses existing Ollama endpoint
    ├─ QueryEngine        ← orchestrates retrieval + generation
    └─ ResultFormatter    ← formats for Vision tool responses

Configuration
-------------
Reads from environment or defaults:
  - CHROMA_DB_PATH: I:\\My Drive\\Z\\X\rag-v1-package\vector_db\\chroma_ollama
  - CHROMA_COLLECTION: rag_sensitive_ollama
  - OLLAMA_BASE_URL: http://127.0.0.1:11434
  - EMBEDDING_MODEL: nomic-embed-text:latest
  - ANSWER_MODEL: gemma3:latest
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

# Default paths from RAG_BLUEPRINT.md
DEFAULT_CHROMA_PATH = r"I:\My Drive\Z\X\rag-v1-package\vector_db\chroma_ollama"
DEFAULT_COLLECTION = "rag_sensitive_ollama"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text:latest"
DEFAULT_ANSWER_MODEL = "gemma3:latest"

# Script paths from RAG_BLUEPRINT.md
QUERY_SCRIPT = r"I:\My Drive\Z\X\rag-v1-package\query_chroma_ollama.py"
ASK_SCRIPT = r"I:\My Drive\Z\X\rag-v1-package\ask_rag_ollama.py"
BUILD_SCRIPT = r"I:\My Drive\Z\X\rag-v1-package\build_chroma_ollama.py"


class VisionRAGClient:
    """
    Client for querying the local RAG system.
    Uses the existing scripts from rag-v1-package.
    """

    def __init__(
        self,
        chroma_path: str = DEFAULT_CHROMA_PATH,
        collection: str = DEFAULT_COLLECTION,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        embed_model: str = DEFAULT_EMBED_MODEL,
        answer_model: str = DEFAULT_ANSWER_MODEL,
    ) -> None:
        self.chroma_path = chroma_path
        self.collection = collection
        self.ollama_url = ollama_url
        self.embed_model = embed_model
        self.answer_model = answer_model

    def _check_chroma_exists(self) -> bool:
        """Check if Chroma DB exists and is accessible."""
        return Path(self.chroma_path).exists()

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            urllib.request.urlopen(f"{self.ollama_url}/api/tags", timeout=2)
            return True
        except Exception:
            return False

    def get_status(self) -> dict[str, Any]:
        """Get current RAG system status."""
        status = {
            "chroma_path": self.chroma_path,
            "collection": self.collection,
            "ollama_url": self.ollama_url,
            "chroma_exists": self._check_chroma_exists(),
            "ollama_available": self._check_ollama_available(),
            "embed_model": self.embed_model,
            "answer_model": self.answer_model,
        }

        # Try to get document count from manifest
        manifest_path = Path(self.chroma_path).parent / "chroma_ollama_manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                status["indexed_docs"] = manifest.get("processed_docs", 0)
                status["total_docs"] = manifest.get("estimated_total_docs", 0)
                status["build_complete"] = manifest.get("completed", False)
            except Exception as exc:
                logger.warning("Failed to read manifest: %s", exc)

        return status

    def query_chroma(
        self,
        query: str,
        n_results: int = 5,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Query Chroma directly for relevant documents.
        Uses query_chroma_ollama.py script.
        """
        if not self._check_chroma_exists():
            return [{"error": "Chroma DB not found", "path": self.chroma_path}]

        try:
            # Build command
            cmd = [
                sys.executable,
                QUERY_SCRIPT,
                query,
                str(n_results),
            ]

            # Run query
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error("Chroma query failed: %s", result.stderr)
                return [{"error": "Query failed", "stderr": result.stderr}]

            # Parse results
            return self._parse_chroma_results(result.stdout)

        except subprocess.TimeoutExpired:
            return [{"error": "Query timed out"}]
        except Exception as exc:
            logger.error("Chroma query error: %s", exc)
            return [{"error": str(exc)}]

    def ask_rag(
        self,
        question: str,
        n_context: int = 3,
    ) -> dict[str, Any]:
        """
        Ask a question using full RAG pipeline.
        Uses ask_rag_ollama.py script.
        """
        if not self._check_chroma_exists():
            return {"error": "Chroma DB not found", "path": self.chroma_path}

        if not self._check_ollama_available():
            return {"error": "Ollama not available", "url": self.ollama_url}

        try:
            cmd = [
                sys.executable,
                ASK_SCRIPT,
                question,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                logger.error("RAG ask failed: %s", result.stderr)
                return {"error": "RAG failed", "stderr": result.stderr}

            return {
                "question": question,
                "answer": result.stdout.strip(),
                "model": self.answer_model,
            }

        except subprocess.TimeoutExpired:
            return {"error": "RAG query timed out"}
        except Exception as exc:
            logger.error("RAG ask error: %s", exc)
            return {"error": str(exc)}

    def _parse_chroma_results(self, output: str) -> list[dict[str, Any]]:
        """Parse output from query_chroma_ollama.py."""
        results = []
        lines = output.strip().split("\n")

        current_result = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to parse as JSON
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    results.append(data)
            except json.JSONDecodeError:
                # Treat as text result
                if line.startswith("-") or line.startswith("Result"):
                    results.append({"text": line})

        return results if results else [{"text": output}]

    def format_for_vision(
        self,
        query: str,
        results: list[dict[str, Any]],
        max_length: int = 2000,
    ) -> str:
        """
        Format RAG results for Vision tool responses.
        """
        if not results:
            return f"No results found for: {query}"

        if "error" in results[0]:
            return f"RAG Error: {results[0]['error']}"

        formatted = [f"RAG Query: '{query}'\n", "Results:"]

        for i, result in enumerate(results[:5], 1):
            text = result.get("text", result.get("document", str(result)))
            distance = result.get("distance", "N/A")
            source = result.get("source", result.get("metadata", {}).get("source", "unknown"))

            formatted.append(f"\n{i}. [{distance}] {source}")
            formatted.append(f"   {text[:300]}...")

        output = "\n".join(formatted)
        return output[:max_length] if len(output) > max_length else output


# ── Singleton Instance ───────────────────────────────────────────────────────

_rag_client: VisionRAGClient | None = None


def get_rag_client() -> VisionRAGClient:
    """Get or create the singleton RAG client."""
    global _rag_client
    if _rag_client is None:
        _rag_client = VisionRAGClient()
    return _rag_client


# ── Tool Interface for Vision ────────────────────────────────────────────────


async def rag_query_tool(query: str, n_results: int = 5) -> str:
    """
    Tool interface for Vision's tool system.
    Queries the local RAG system and returns formatted results.
    """
    client = get_rag_client()
    results = await asyncio.to_thread(client.query_chroma, query, n_results)
    return await asyncio.to_thread(client.format_for_vision, query, results)


async def rag_ask_tool(question: str) -> str:
    """
    Tool interface for full RAG Q&A.
    Asks a question using the RAG pipeline.
    """
    client = get_rag_client()
    result = await asyncio.to_thread(client.ask_rag, question)

    if "error" in result:
        return f"RAG Error: {result['error']}"

    return f"Question: {result['question']}\n\nAnswer: {result['answer']}\n\n(Model: {result['model']})"


async def rag_status_tool() -> str:
    """Tool interface for RAG status check."""
    client = get_rag_client()
    status = await asyncio.to_thread(client.get_status)

    lines = [
        "RAG System Status:",
        f"  Chroma DB: {'✅' if status['chroma_exists'] else '❌'} {status['chroma_path']}",
        f"  Ollama: {'✅' if status['ollama_available'] else '❌'} {status['ollama_url']}",
        f"  Collection: {status['collection']}",
        f"  Embed Model: {status['embed_model']}",
        f"  Answer Model: {status['answer_model']}",
    ]

    if "indexed_docs" in status:
        lines.extend(
            [
                f"  Indexed: {status['indexed_docs']:,} / {status['total_docs']:,} documents",
                f"  Build Complete: {'✅' if status['build_complete'] else '⏳ In Progress'}",
            ]
        )

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    client = get_rag_client()
    print(json.dumps(client.get_status(), indent=2))
