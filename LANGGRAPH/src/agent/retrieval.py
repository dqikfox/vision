from __future__ import annotations

import re
from dataclasses import dataclass
from math import sqrt

from agent.memory import FileMemoryStore, MemoryRecord


@dataclass
class RetrievalResult:
    key: str
    value: str
    score: float


def _tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in re.split(r"[\s.,:;!?()\[\]{}\"'`\-_/]+", text):
        stripped = token.strip()
        if stripped:
            tokens.add(stripped.lower())
    return tokens


def _score(query: str, record: MemoryRecord) -> float:
    q = _tokenize(query)
    r = _tokenize(f"{record.key} {record.value}")
    if not q or not r:
        return 0.0
    overlap = len(q & r)
    return overlap / sqrt(len(q) * len(r))


def retrieve_relevant_memories(store: FileMemoryStore, query: str, limit: int = 5) -> list[RetrievalResult]:
    results = []
    for record in store.list_records():
        score = _score(query, record)
        if score > 0:
            results.append(RetrievalResult(key=record.key, value=record.value, score=score))
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]


def render_retrieval_results(results: list[RetrievalResult]) -> str:
    if not results:
        return "No relevant memory matches found."
    return "\n".join(f"- {item.key}: {item.value} (score={item.score:.2f})" for item in results)
