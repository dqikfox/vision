"""
rag_tool.py — Vision RAG integration
=====================================
Connects Vision's exec_tool to the local Chroma vector DB at
I:\\My Drive\\Z\\X\\rag-v1-package

Tools exposed:
  rag_search  — semantic search, returns top-k document chunks
  rag_ask     — full RAG: retrieve + generate answer via Ollama
  rag_status  — check if Chroma DB and Ollama are ready
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib import request as _urllib_request

import chromadb

# ── Config ────────────────────────────────────────────────────────────────────

RAG_ROOT = Path(r"I:\My Drive\Z\X\rag-v1-package")
DB_DIR = RAG_ROOT / "vector_db" / "chroma_ollama"
COLLECTION = "rag_sensitive_ollama"
EMBED_MODEL = "nomic-embed-text:latest"
ANSWER_MODEL = "gemma3:latest"
OLLAMA_BASE = "http://127.0.0.1:11434"
CHROMA_BASE = "http://127.0.0.1:8040"
MAX_CHARS = 4000

# Add RAG package to path so we can reuse its helpers
if str(RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ROOT))


# ── Helpers ───────────────────────────────────────────────────────────────────


def _post_json(url: str, payload: dict, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = _urllib_request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with _urllib_request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ollama_embed(text: str) -> list[float]:
    resp = _post_json(
        f"{OLLAMA_BASE}/api/embed",
        {"model": EMBED_MODEL, "input": [text[:MAX_CHARS]]},
        timeout=60,
    )
    return resp["embeddings"][0]


def _ollama_generate(prompt: str, system: str = "") -> str:
    payload: dict = {"model": ANSWER_MODEL, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    resp = _post_json(f"{OLLAMA_BASE}/api/generate", payload, timeout=300)
    return resp.get("response", "").strip()


def _parse_n_results(raw_value: object, default: int = 5) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return default

    if 1 <= parsed <= 20:
        return parsed
    return default


def _validate_n_results(n_results: int) -> int:
    if not isinstance(n_results, int) or not 1 <= n_results <= 20:
        raise ValueError("n_results must be an integer between 1 and 20")
    return n_results


def _get_collection():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_collection(COLLECTION)


# ── Tool implementations ──────────────────────────────────────────────────────


def rag_status() -> str:
    """Check if RAG components are ready."""
    results = {}

    # Check Ollama
    try:
        _urllib_request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=3)
        results["ollama"] = "OK"
    except Exception as e:
        results["ollama"] = f"DOWN: {e}"

    # Check Chroma DB exists
    results["chroma_db_path"] = str(DB_DIR)
    results["chroma_db_exists"] = DB_DIR.exists()

    # Check collection
    try:
        col = _get_collection()
        results["collection"] = COLLECTION
        results["document_count"] = col.count()
        results["status"] = "READY"
    except Exception as e:
        results["collection_error"] = str(e)
        results["status"] = "NOT_INDEXED — run build_chroma_ollama.py first"

    return json.dumps(results, indent=2)


def rag_search(query: str, n_results: int = 5) -> str:
    """Semantic search against the RAG corpus. Returns top-k chunks."""
    try:
        n_results = _validate_n_results(n_results)
        col = _get_collection()
        embedding = _ollama_embed(query)
        result = col.query(query_embeddings=[embedding], n_results=n_results)

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        hits = []
        for doc_id, dist, meta, doc in zip(ids, distances, metas, docs):
            hits.append(
                {
                    "id": doc_id,
                    "score": round(1 - dist, 4),  # convert distance to similarity
                    "source": meta.get("source_path", meta.get("file_name", "unknown")),
                    "category": meta.get("category", ""),
                    "preview": doc[:600],
                }
            )

        return json.dumps(
            {
                "query": query,
                "n_results": len(hits),
                "hits": hits,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        return f"RAG search error: {e}"


def rag_ask(question: str, n_results: int = 5) -> str:
    """Full RAG: retrieve relevant chunks then generate an answer via Ollama."""
    try:
        n_results = _validate_n_results(n_results)
        col = _get_collection()
        embedding = _ollama_embed(question)
        result = col.query(query_embeddings=[embedding], n_results=n_results)

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        ids = result.get("ids", [[]])[0]

        snippets = []
        sources = []
        for i, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), 1):
            src = meta.get("source_path", meta.get("file_name", "unknown"))
            snippets.append(f"[{i}] {src}\n{doc[:MAX_CHARS]}")
            sources.append({"id": doc_id, "source": src})

        system = (
            "Answer using the retrieved local PC context when relevant. "
            "Prefer explicit facts from structured reference files like key.json. "
            "Prefer concrete paths, ports, model names, and file references. "
            "If the context is insufficient, say so plainly."
        )
        prompt = "Retrieved context:\n\n" + "\n\n".join(snippets)
        prompt += f"\n\nQuestion: {question}\n\nAnswer:"

        answer = _ollama_generate(prompt, system=system)

        return json.dumps(
            {
                "question": question,
                "answer": answer,
                "sources": sources,
                "model": ANSWER_MODEL,
            },
            indent=2,
            ensure_ascii=False,
        )

    except Exception as e:
        return f"RAG ask error: {e}"


# ── Tool schemas for Vision TOOLS list ───────────────────────────────────────

RAG_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "rag_status",
            "description": "Check if the local RAG system (Chroma vector DB + Ollama) is ready. Shows document count and index status.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": (
                "Semantic search against the local RAG corpus (273,500+ documents from F:\\rag-v1\\data). "
                "Returns the most relevant document chunks for a query. "
                "Use for finding files, paths, configs, API keys, project notes, or any personal knowledge."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"},
                    "n_results": {"type": "integer", "description": "Number of results (default 5, max 20)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rag_ask",
            "description": (
                "Ask a question and get an AI-generated answer grounded in the local RAG corpus. "
                "Retrieves relevant context then uses Ollama (gemma3) to synthesise an answer. "
                "Best for: 'Where are my API keys?', 'What models do I have?', 'What's the path to X?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to answer"},
                    "n_results": {"type": "integer", "description": "Context chunks to retrieve (default 5)"},
                },
                "required": ["question"],
            },
        },
    },
]

RAG_TOOL_NAMES = ["rag_status", "rag_search", "rag_ask"]


def handle_rag_tool(name: str, args: dict) -> str:
    """Dispatch RAG tool calls from exec_tool."""
    if name == "rag_status":
        return rag_status()
    elif name == "rag_search":
        n_results = _parse_n_results(args.get("n_results", 5))
        return rag_search(args.get("query", ""), n_results)
    elif name == "rag_ask":
        n_results = _parse_n_results(args.get("n_results", 5))
        return rag_ask(args.get("question", ""), n_results)
    return f"Unknown RAG tool: {name}"
