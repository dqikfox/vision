---
applyTo: "vision_rag*.py"
---

# Vision RAG System Instructions

## RAG Architecture
Vision's RAG (Retrieval-Augmented Generation) system uses **SQLite FTS5** for fast full-text search over a local document corpus. It consists of:
- `vision_rag.py` - Core indexing and search engine
- `vision_rag_integration.py` - Pipeline integration with LLM

## Design Principles
1. **Offline-first**: Works without internet (local SQLite database)
2. **Fast retrieval**: FTS5 provides sub-50ms search on large corpora
3. **Minimal dependencies**: No vector databases, no heavy ML models
4. **Deterministic**: Same query always returns same results
5. **Privacy-preserving**: All data stays local

## Supported File Types
```python
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst",
    ".json", ".jsonl", ".csv", ".tsv",
    ".yaml", ".yml", ".py", ".js", ".ts",
    ".tsx", ".jsx", ".html", ".htm", ".xml",
    ".sql", ".sh", ".ps1", ".bat", ".toml",
    ".ini", ".cfg",
}
```

## Indexing Pattern
```python
from vision_rag import RAGIndex

# Initialize index (creates SQLite database)
index = RAGIndex(db_path="vision_corpus.db")

# Index a directory
index.index_directory(
    directory="C:\\project\\docs",
    skip_dirs={"node_modules", ".git", "__pycache__"},
    max_file_size=1024 * 1024  # 1MB limit
)

# Index is ready for search
results = index.search("how to configure voice settings", limit=5)
```

## Search API
```python
def search(
    self,
    query: str,
    limit: int = 10,
    min_score: float = 0.0,
    file_types: list[str] | None = None
) -> list[dict[str, Any]]:
    """Search the corpus using FTS5.

    Args:
        query: Search query (supports FTS5 syntax)
        limit: Maximum results to return
        min_score: Minimum relevance score (0.0-1.0)
        file_types: Filter by file extensions (e.g., [".py", ".md"])

    Returns:
        List of result dicts with keys:
        - path: str - File path
        - content: str - Matched text chunk
        - score: float - Relevance score
        - line_start: int - Starting line number
        - line_end: int - Ending line number
    """
```

## FTS5 Query Syntax
Support advanced queries:
```python
# Phrase search
results = index.search('"vision overlay"')

# Boolean operators
results = index.search('websocket AND python')

# Prefix matching
results = index.search('ollama*')

# Column search
results = index.search('content:accessibility')
```

## Chunking Strategy
- **Chunk size**: 500-1000 characters (configurable)
- **Overlap**: 100 characters between chunks (prevents split context)
- **Metadata preservation**: Store file path, line numbers, last modified

Example:
```python
def chunk_document(content: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split document into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        # Find natural break (newline or space)
        if end < len(content):
            end = content.rfind('\n', start, end)
            if end == -1:
                end = content.rfind(' ', start, start + chunk_size)
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks
```

## Database Schema
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
    path,           -- File path
    content,        -- Text content
    chunk_index,    -- Chunk number within file
    line_start,     -- Starting line number
    line_end,       -- Ending line number
    file_type,      -- File extension
    last_modified,  -- Modification timestamp
    tokenize='porter ascii'
);

CREATE INDEX idx_path ON documents(path);
CREATE INDEX idx_file_type ON documents(file_type);
```

## Incremental Indexing
Only re-index changed files:
```python
def needs_reindex(self, file_path: Path) -> bool:
    """Check if file was modified since last index."""
    cursor = self.conn.execute(
        "SELECT last_modified FROM documents WHERE path = ? LIMIT 1",
        (str(file_path),)
    )
    row = cursor.fetchone()
    if not row:
        return True

    last_indexed = float(row[0])
    current_mtime = file_path.stat().st_mtime
    return current_mtime > last_indexed
```

## Export for Training
Export search results as training data:
```python
def export_training_data(
    self,
    queries: list[str],
    output_path: Path,
    format: str = "jsonl"
) -> None:
    """Export query-document pairs for LLM fine-tuning.

    Args:
        queries: List of representative queries
        output_path: Output file path
        format: 'jsonl' or 'csv'
    """
    with output_path.open('w', encoding='utf-8') as f:
        for query in queries:
            results = self.search(query, limit=5)
            for result in results:
                item = {
                    "query": query,
                    "document": result["content"],
                    "path": result["path"],
                    "score": result["score"]
                }
                if format == "jsonl":
                    f.write(json.dumps(item) + '\n')
                elif format == "csv":
                    # Implement CSV export
                    pass
```

## Integration with LLM
```python
def augment_prompt(query: str, context_limit: int = 3000) -> str:
    """Retrieve relevant context and augment LLM prompt."""
    results = index.search(query, limit=10)

    # Build context string
    context_parts = []
    total_chars = 0

    for result in results:
        chunk = f"--- {result['path']} (lines {result['line_start']}-{result['line_end']}) ---\n"
        chunk += result['content'] + '\n\n'

        if total_chars + len(chunk) > context_limit:
            break

        context_parts.append(chunk)
        total_chars += len(chunk)

    context = ''.join(context_parts)

    # Augmented prompt
    return f"""Using the following documentation as context:

{context}

Answer the following question:
{query}
"""
```

## Performance Optimization
- **Batch inserts**: Use transactions for bulk indexing
- **PRAGMA settings**: Optimize SQLite for performance
- **Memory mapping**: Use `PRAGMA mmap_size` for large databases
- **Concurrent reads**: SQLite allows multiple readers

```python
def optimize_database(self) -> None:
    """Apply performance optimizations."""
    self.conn.execute("PRAGMA journal_mode = WAL")
    self.conn.execute("PRAGMA synchronous = NORMAL")
    self.conn.execute("PRAGMA cache_size = 10000")
    self.conn.execute("PRAGMA temp_store = MEMORY")
    self.conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
```

## Error Handling
Handle common RAG errors gracefully:
```python
try:
    results = index.search(query)
except sqlite3.OperationalError as e:
    if "locked" in str(e):
        logger.warning("Database locked, retrying...")
        time.sleep(0.1)
        results = index.search(query)
    else:
        raise
except UnicodeDecodeError as e:
    logger.error(f"Failed to decode file: {e}")
    # Skip file and continue
```

## Testing
Test RAG functionality:
```python
def test_rag_search():
    index = RAGIndex(":memory:")  # In-memory for testing

    # Add test documents
    index.add_document(
        path="test.py",
        content="def hello():\n    print('Hello, Vision!')"
    )

    # Search
    results = index.search("hello function")
    assert len(results) > 0
    assert "hello()" in results[0]["content"]
```

## Monitoring
Log RAG performance metrics:
```python
import time

def search_with_metrics(query: str) -> tuple[list[dict], float]:
    """Search and return results with timing."""
    start = time.time()
    results = index.search(query)
    elapsed = time.time() - start

    logger.info(f"RAG search: '{query[:50]}' returned {len(results)} results in {elapsed*1000:.1f}ms")

    return results, elapsed
```

## Privacy & Security
- Never index sensitive files (`.env`, `secrets.json`, etc.)
- Respect `.gitignore` patterns
- Allow user to exclude directories
- Provide data export and deletion tools
