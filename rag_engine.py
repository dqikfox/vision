"""
rag_engine.py — Vision RAG Module
Retrieval-Augmented Generation backend for the Vision project.
Reads documents from RAG_PLUGIN_WORKSPACE (default: F:\\rag-v1\\data\\)
and exposes a FastAPI server at http://localhost:8766

Dependencies:
    pip install fastapi uvicorn chromadb sentence-transformers
                anthropic httpx aiofiles python-multipart

Usage:
    python rag_engine.py
    # Then open rag_ui.html in your browser
"""

import asyncio
import hashlib
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

import chromadb
import httpx
import uvicorn
from chromadb.config import Settings
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
RAG_PORT = 8766
DATA_DIR = Path(os.environ.get("RAG_PLUGIN_WORKSPACE", r"F:\rag-v1\data"))
CHROMA_DIR = Path(os.environ.get("RAG_CHROMA_DIR", r"F:\rag-v1\chroma_db"))
COLLECTION_NAME = "vision_rag"
EMBED_MODEL = "all-MiniLM-L6-v2"          # fast, good quality, runs locally
CHUNK_SIZE = 512                           # chars per chunk
CHUNK_OVERLAP = 64                         # overlap between chunks
TOP_K = 5                                  # chunks to retrieve per query
MAX_CONTEXT_CHARS = 6000                   # total context chars sent to LLM

# LLM provider — reads same env vars as live_chat_app.py
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RAG] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rag_engine")

# ─────────────────────────────────────────────
# Global singletons (lazy-loaded on first use)
# ─────────────────────────────────────────────
_embed_model: SentenceTransformer | None = None
_chroma_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        log.info("Loading embedding model %s …", EMBED_MODEL)
        _embed_model = SentenceTransformer(EMBED_MODEL)
        log.info("Embedding model ready.")
    return _embed_model


def get_collection() -> chromadb.Collection:
    global _chroma_client, _collection
    if _collection is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        log.info(
            "ChromaDB collection '%s' ready (%d docs).",
            COLLECTION_NAME,
            _collection.count(),
        )
    return _collection


# ─────────────────────────────────────────────
# Text chunking utilities
# ─────────────────────────────────────────────
def chunk_text(text: str, source: str) -> list[dict]:
    """Split text into overlapping chunks, return list of metadata dicts."""
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 32:          # skip tiny fragments
            chunk_id = hashlib.md5(f"{source}:{idx}".encode()).hexdigest()
            chunks.append({
                "id": chunk_id,
                "text": chunk,
                "source": source,
                "chunk_index": idx,
            })
            idx += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def read_file_text(path: Path) -> str | None:
    """Read plain text from .txt, .md, .py, .json, .csv, etc."""
    suffix = path.suffix.lower()
    text_types = {
        ".txt", ".md", ".py", ".js", ".ts", ".json", ".csv",
        ".yaml", ".yml", ".toml", ".html", ".htm", ".xml",
        ".rst", ".log", ".cfg", ".ini", ".sh", ".bat",
    }
    if suffix not in text_types:
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        log.warning("Could not read %s: %s", path, exc)
        return None


# ─────────────────────────────────────────────
# Ingestion
# ─────────────────────────────────────────────
def ingest_directory(directory: Path) -> dict:
    """Walk `directory`, embed all readable files, upsert into ChromaDB."""
    col = get_collection()
    embed = get_embed_model()

    files_processed = 0
    chunks_added = 0
    skipped = 0
    errors: list[str] = []

    for fpath in directory.rglob("*"):
        if not fpath.is_file():
            continue
        text = read_file_text(fpath)
        if text is None:
            skipped += 1
            continue

        source = str(fpath.relative_to(directory))
        chunks = chunk_text(text, source)
        if not chunks:
            skipped += 1
            continue

        try:
            ids = [c["id"] for c in chunks]
            texts = [c["text"] for c in chunks]
            metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]
            embeddings = embed.encode(texts, show_progress_bar=False).tolist()
            col.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
            chunks_added += len(chunks)
            files_processed += 1
            log.info("  ✓ %s  (%d chunks)", source, len(chunks))
        except Exception as exc:
            errors.append(f"{source}: {exc}")
            log.error("Error ingesting %s: %s", source, exc)

    return {
        "files_processed": files_processed,
        "chunks_added": chunks_added,
        "skipped": skipped,
        "errors": errors,
        "total_in_db": col.count(),
    }


def ingest_text(text: str, source: str) -> dict:
    """Ingest raw text with a given source label."""
    col = get_collection()
    embed = get_embed_model()
    chunks = chunk_text(text, source)
    if not chunks:
        return {"chunks_added": 0, "source": source}
    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]
    embeddings = embed.encode(texts, show_progress_bar=False).tolist()
    col.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    return {"chunks_added": len(chunks), "source": source, "total_in_db": col.count()}


# ─────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────
def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed query and return top-k similar chunks."""
    col = get_collection()
    embed = get_embed_model()

    if col.count() == 0:
        return []

    q_vec = embed.encode([query], show_progress_bar=False).tolist()
    results = col.query(
        query_embeddings=q_vec,
        n_results=min(top_k, col.count()),
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "chunk_index": meta.get("chunk_index", 0),
            "score": round(1 - dist, 4),   # cosine similarity
        })
    return hits


# ─────────────────────────────────────────────
# LLM call (mirrors live_chat_app.py provider logic)
# ─────────────────────────────────────────────
async def call_llm(prompt: str, system: str = "") -> str:
    """Try Anthropic → OpenAI → Ollama in priority order."""

    if ANTHROPIC_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1024,
                        "system": system or "You are a helpful assistant.",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["content"][0]["text"]
        except Exception as exc:
            log.warning("Anthropic failed, trying next provider: %s", exc)

    if OPENAI_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                    json={
                        "model": "gpt-4o-mini",
                        "max_tokens": 1024,
                        "messages": [
                            {"role": "system", "content": system or "You are a helpful assistant."},
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            log.warning("OpenAI failed, trying Ollama: %s", exc)

    # Fallback: Ollama (local)
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": f"[SYSTEM] {system}\n\n[USER] {prompt}" if system else prompt,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["response"]
    except Exception as exc:
        raise RuntimeError(f"All LLM providers failed. Last error: {exc}") from exc


# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(title="Vision RAG Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    top_k: int = TOP_K
    generate: bool = True          # if True, call LLM; if False, return chunks only


class IngestTextRequest(BaseModel):
    text: str
    source: str = "manual_paste"


class DeleteRequest(BaseModel):
    source: str                    # delete all chunks matching this source


# ── Status ──────────────────────────────────────────────────────────────────

@app.get("/api/rag/status")
async def status():
    col = get_collection()
    return {
        "status": "online",
        "collection": COLLECTION_NAME,
        "total_chunks": col.count(),
        "data_dir": str(DATA_DIR),
        "chroma_dir": str(CHROMA_DIR),
        "embed_model": EMBED_MODEL,
        "providers": {
            "anthropic": bool(ANTHROPIC_KEY),
            "openai": bool(OPENAI_KEY),
            "ollama": OLLAMA_URL,
        },
    }


# ── Ingest ───────────────────────────────────────────────────────────────────

@app.post("/api/rag/ingest/directory")
async def ingest_directory_endpoint():
    """Ingest all files from RAG_PLUGIN_WORKSPACE."""
    if not DATA_DIR.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Data directory not found: {DATA_DIR}. "
                   "Set RAG_PLUGIN_WORKSPACE env var or create the directory.",
        )
    t0 = time.time()
    result = await asyncio.to_thread(ingest_directory, DATA_DIR)
    result["elapsed_seconds"] = round(time.time() - t0, 2)
    return result


@app.post("/api/rag/ingest/text")
async def ingest_text_endpoint(req: IngestTextRequest):
    """Ingest raw text."""
    return await asyncio.to_thread(ingest_text, req.text, req.source)


@app.post("/api/rag/ingest/file")
async def ingest_file_endpoint(file: UploadFile = File(...)):
    """Upload and ingest a single file."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    return await asyncio.to_thread(ingest_text, text, file.filename or "uploaded_file")


# ── Query / RAG ──────────────────────────────────────────────────────────────

@app.post("/api/rag/query")
async def query_endpoint(req: QueryRequest):
    """
    Retrieve relevant chunks and optionally generate an LLM answer.
    Returns chunks always; adds 'answer' key when generate=True.
    """
    t0 = time.time()
    chunks = await asyncio.to_thread(retrieve, req.query, req.top_k)

    result: dict[str, Any] = {
        "query": req.query,
        "chunks": chunks,
        "chunk_count": len(chunks),
    }

    if req.generate and chunks:
        context = "\n\n---\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}"
            for c in chunks
        )[:MAX_CONTEXT_CHARS]

        system_prompt = (
            "You are a knowledgeable assistant with access to a private document database. "
            "Answer the user's question using ONLY the provided context. "
            "Be concise and precise. If the context does not contain enough information, say so. "
            "Always cite which document(s) you drew information from."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {req.query}"

        try:
            answer = await call_llm(prompt, system_prompt)
            result["answer"] = answer
            result["provider"] = (
                "anthropic" if ANTHROPIC_KEY else
                "openai" if OPENAI_KEY else
                f"ollama/{OLLAMA_MODEL}"
            )
        except RuntimeError as exc:
            result["answer"] = f"[LLM Error] {exc}"
            result["provider"] = "error"

    elif req.generate and not chunks:
        result["answer"] = "No relevant documents found in the knowledge base for this query."
        result["provider"] = "none"

    result["elapsed_ms"] = round((time.time() - t0) * 1000)
    return result


# ── Management ───────────────────────────────────────────────────────────────

@app.get("/api/rag/sources")
async def list_sources():
    """List all unique source files in the collection."""
    col = get_collection()
    if col.count() == 0:
        return {"sources": []}
    # Fetch all metadatas (ChromaDB has no distinct query, so we page)
    results = col.get(include=["metadatas"])
    sources: dict[str, int] = {}
    for meta in results["metadatas"]:
        src = meta.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    return {
        "sources": [
            {"source": s, "chunks": c}
            for s, c in sorted(sources.items())
        ],
        "total_chunks": col.count(),
    }


@app.delete("/api/rag/source")
async def delete_source(req: DeleteRequest):
    """Delete all chunks for a given source file."""
    col = get_collection()
    results = col.get(where={"source": req.source}, include=["metadatas"])
    ids = results["ids"]
    if not ids:
        raise HTTPException(status_code=404, detail=f"No chunks found for source: {req.source}")
    col.delete(ids=ids)
    return {"deleted": len(ids), "source": req.source, "remaining": col.count()}


@app.delete("/api/rag/collection")
async def clear_collection():
    """Wipe the entire collection — irreversible."""
    global _collection
    if _chroma_client and _collection:
        _chroma_client.delete_collection(COLLECTION_NAME)
        _collection = None
    # Re-create empty collection
    get_collection()
    return {"status": "cleared", "total_chunks": 0}


# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    log.info("Vision RAG Engine starting on port %d", RAG_PORT)
    log.info("Data directory : %s", DATA_DIR)
    log.info("ChromaDB path  : %s", CHROMA_DIR)
    # Pre-load models in background so first query is fast
    asyncio.get_event_loop().run_in_executor(None, get_embed_model)
    asyncio.get_event_loop().run_in_executor(None, get_collection)


if __name__ == "__main__":
    uvicorn.run(
        "rag_engine:app",
        host="0.0.0.0",
        port=RAG_PORT,
        reload=False,
        log_level="info",
    )
