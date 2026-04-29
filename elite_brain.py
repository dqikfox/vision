"""
elite_brain.py — Cognitive Enhancement Layer for Vision
========================================================
Gives the LLM more "brain power" through five orthogonal capabilities:

  1. SEMANTIC MEMORY    — Embed facts / past turns, retrieve by cosine sim.
                          No external API: uses numpy float32 projections.

  2. MULTI-PATH REASONING — Tree-of-Thoughts: spawn N hypotheses in parallel,
                             self-critique each, synthesise the best answer.

  3. META-COGNITION     — After every response the brain scores itself
                          (confidence, completeness, safety) and optionally
                          triggers a self-revision pass.

  4. DYNAMIC CONTEXT    — Assembles the most relevant snippets of memory,
                          tool history, and episodic recall into the system
                          prompt — no wasted tokens, no forgotten context.

  5. CURIOSITY ENGINE   — Proactively detects knowledge gaps and schedules
                          background "wonder" tasks that fill them silently.

  6. SELF-EVOLUTION     — Converts weak outcomes into durable local guidance
                          rules that improve future responses.

Architecture
------------
  Brain                  ← top-level façade, wired into live_chat_app.py
    ├─ SemanticStore      ← vector store (numpy cosine sim)
    ├─ EpisodicLog        ← compact record of past Q-A pairs + outcomes
    ├─ ThoughtTree        ← parallel hypothesis generation + synthesis
    ├─ MetaCritic         ← self-scoring + optional revision
    ├─ ContextForge       ← assembles augmented system prompt
    ├─ CuriosityEngine    ← background gap-detection / background fills
    └─ SelfEvolutionEngine← learns reusable guidance from outcomes

Integration
-----------
  In live_chat_app.py:

    from elite_brain import get_brain
    brain = get_brain()                        # singleton

    # Before calling the LLM:
    augmented_prompt = await brain.augment_system(base_prompt, user_message)
    messages = [{"role": "system", "content": augmented_prompt}, *history[-20:]]

    # After receiving a response:
    await brain.ingest(user_message, assistant_response, tools_used=["read_screen"], latency_ms=320.0, outcome="success")
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import re
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

BRAIN_DATA_DIR = Path(__file__).parent / ".brain"
EMBED_DIM = 256  # projection dimension for lightweight embeddings
MAX_SEMANTIC_MEMORIES = 2_000
MAX_EPISODIC_ENTRIES = 500
TOP_K_RETRIEVAL = 6
THOUGHT_BRANCHES = 3  # parallel hypothesis count for ToT
METACRITIC_THRESHOLD = 0.65  # below this score triggers revision
MAX_CONTEXT_TOKENS = 1_800  # token budget for brain-injected context block
MAX_ADAPTATIONS = 256
TOP_K_ADAPTATIONS = 3

# ── Utilities ──────────────────────────────────────────────────────────────────


def _hash_text(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def _token_estimate(text: str) -> int:
    """Rough token count (4 chars ≈ 1 token)."""
    return max(1, len(text) // 4)


def _truncate(text: str, max_tokens: int) -> str:
    limit = max_tokens * 4
    return text[:limit] + " …" if len(text) > limit else text


# ── Embedding Engine ───────────────────────────────────────────────────────────


class EmbeddingEngine:
    """
    Lightweight deterministic embedding via random-projection onto a fixed
    matrix seeded from the text's own character n-gram bag.

    Properties:
    - No external API calls, no GPU, no extra dependencies beyond numpy
    - Deterministic: same text always produces the same vector
    - Cosine-comparable: works correctly for nearest-neighbour retrieval
    - Dimension: EMBED_DIM (default 256) float32
    """

    def __init__(self, dim: int = EMBED_DIM) -> None:
        self.dim = dim
        # Stable global projection matrix seeded from a fixed value
        rng = np.random.default_rng(seed=0xDEADBEEF)
        self._P: np.ndarray = rng.standard_normal((65536, dim)).astype(np.float32)
        # Norm rows so projection preserves unit scale
        norms = np.linalg.norm(self._P, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        self._P /= norms

    def embed(self, text: str) -> np.ndarray:
        """Return a unit-norm float32 vector of shape (dim,)."""
        text = text.lower()
        # Build char-trigram bag of codes
        codes: list[int] = []
        for i in range(len(text) - 2):
            tri = text[i : i + 3]
            code = (ord(tri[0]) * 31 + ord(tri[1])) * 31 + ord(tri[2])
            codes.append(code % 65536)
        if not codes:
            codes = [ord(c) % 65536 for c in text[:8]]
        # Project: sum the row vectors for each trigram code
        indices = np.array(codes, dtype=np.int32)
        vec = self._P[indices].sum(axis=0)
        norm = float(np.linalg.norm(vec))
        if norm < 1e-9:
            return np.zeros(self.dim, dtype=np.float32)
        return (vec / norm).astype(np.float32)

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity in [-1, 1]."""
        return float(np.dot(a, b))


_embed_engine = EmbeddingEngine()


# ── Semantic Memory Store ──────────────────────────────────────────────────────


@dataclass
class MemoryEntry:
    uid: str
    text: str
    vector: np.ndarray
    source: str  # "fact" | "episodic" | "tool" | "observation"
    timestamp: float
    access_count: int = 0
    importance: float = 1.0


class SemanticStore:
    """
    Vector store backed by a JSON file for persistence.
    Uses cosine similarity for retrieval. No external dependencies.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._entries: dict[str, MemoryEntry] = {}
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for item in raw:
                vec = np.array(item["vector"], dtype=np.float32)
                entry = MemoryEntry(
                    uid=item["uid"],
                    text=item["text"],
                    vector=vec,
                    source=item.get("source", "fact"),
                    timestamp=item.get("timestamp", 0.0),
                    access_count=item.get("access_count", 0),
                    importance=item.get("importance", 1.0),
                )
                self._entries[entry.uid] = entry
            logger.info("SemanticStore loaded %d entries", len(self._entries))
        except Exception as exc:
            logger.warning("SemanticStore load error: %s", exc)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "uid": e.uid,
                "text": e.text,
                "vector": e.vector.tolist(),
                "source": e.source,
                "timestamp": e.timestamp,
                "access_count": e.access_count,
                "importance": e.importance,
            }
            for e in self._entries.values()
        ]
        self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    # ── Mutation ────────────────────────────────────────────────────────────────

    def add(self, text: str, source: str = "fact", importance: float = 1.0) -> str:
        """Add or update an entry. Returns uid."""
        uid = _hash_text(text)
        if uid in self._entries:
            self._entries[uid].importance = max(self._entries[uid].importance, importance)
            return uid
        vec = _embed_engine.embed(text)
        self._entries[uid] = MemoryEntry(
            uid=uid,
            text=text,
            vector=vec,
            source=source,
            timestamp=time.time(),
            importance=importance,
        )
        self._evict_if_needed()
        return uid

    def _evict_if_needed(self) -> None:
        """Evict low-importance, low-access entries when over limit."""
        if len(self._entries) <= MAX_SEMANTIC_MEMORIES:
            return
        scored = sorted(
            self._entries.values(),
            key=lambda e: e.importance * math.log1p(e.access_count + 1),
        )
        to_remove = len(self._entries) - MAX_SEMANTIC_MEMORIES
        for entry in scored[:to_remove]:
            del self._entries[entry.uid]

    # ── Retrieval ───────────────────────────────────────────────────────────────

    def query(self, text: str, top_k: int = TOP_K_RETRIEVAL, source_filter: str | None = None) -> list[MemoryEntry]:
        """Return top-k entries by cosine similarity."""
        if not self._entries:
            return []
        q_vec = _embed_engine.embed(text)
        candidates = list(self._entries.values())
        if source_filter:
            candidates = [e for e in candidates if e.source == source_filter]
        if not candidates:
            return []
        vectors = np.stack([e.vector for e in candidates])
        sims = vectors @ q_vec
        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            entry = candidates[int(idx)]
            entry.access_count += 1
            results.append(entry)
        return results

    def __len__(self) -> int:
        return len(self._entries)


# ── Episodic Log ───────────────────────────────────────────────────────────────


@dataclass
class Episode:
    uid: str
    user_msg: str
    assistant_response: str
    outcome: str  # "success" | "failure" | "partial" | "unknown"
    tools_used: list[str]
    latency_ms: float
    timestamp: float
    metacritic_score: float = 1.0


class EpisodicLog:
    """
    Compact rolling log of past interactions with outcome labels.
    Used for few-shot recall: "last time user asked X, you did Y and it worked."
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._episodes: deque[Episode] = deque(maxlen=MAX_EPISODIC_ENTRIES)
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for item in raw:
                self._episodes.append(Episode(**item))
            logger.info("EpisodicLog loaded %d episodes", len(self._episodes))
        except Exception as exc:
            logger.warning("EpisodicLog load error: %s", exc)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.__dict__ for e in self._episodes]
        self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def record(
        self,
        user_msg: str,
        assistant_response: str,
        outcome: str = "unknown",
        tools_used: list[str] | None = None,
        latency_ms: float = 0.0,
        metacritic_score: float = 1.0,
    ) -> None:
        ep = Episode(
            uid=_hash_text(f"{user_msg}{time.time()}"),
            user_msg=user_msg,
            assistant_response=assistant_response,
            outcome=outcome,
            tools_used=tools_used or [],
            latency_ms=latency_ms,
            timestamp=time.time(),
            metacritic_score=metacritic_score,
        )
        self._episodes.append(ep)

    def find_similar(self, query: str, top_k: int = 3) -> list[Episode]:
        """Return the most similar past episodes (cosine sim on user_msg)."""
        if not self._episodes:
            return []
        q_vec = _embed_engine.embed(query)
        scored: list[tuple[float, Episode]] = []
        for ep in self._episodes:
            sim = _embed_engine.similarity(q_vec, _embed_engine.embed(ep.user_msg))
            scored.append((sim, ep))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]

    def success_rate(self) -> float:
        if not self._episodes:
            return 1.0
        successes = sum(1 for e in self._episodes if e.outcome == "success")
        return successes / len(self._episodes)


# ── Tree of Thoughts ───────────────────────────────────────────────────────────


@dataclass
class Thought:
    branch_id: int
    hypothesis: str
    critique: str
    score: float  # 0-1, higher is better


class ThoughtTree:
    """
    Implements a one-level Tree of Thoughts:

      1. Generate N candidate hypotheses (answers/plans) in parallel.
      2. Critique each one independently.
      3. Pick the highest-scoring branch.
      4. Optionally synthesise the top-2 branches.

    All generation is delegated to a pluggable `llm_fn` coroutine so the
    tree works with any provider Vision has configured.
    """

    def __init__(self, branches: int = THOUGHT_BRANCHES) -> None:
        self.branches = branches
        self._llm_fn: Callable[[str], asyncio.coroutines] | None = None

    def set_llm(self, fn: Callable[[str], asyncio.coroutines]) -> None:
        """Wire in the `_fast_completion` function from live_chat_app."""
        self._llm_fn = fn

    async def _call(self, prompt: str, max_tokens: int = 300) -> str:
        if self._llm_fn is None:
            return ""
        try:
            result = await self._llm_fn(prompt, max_tokens)
            return result or ""
        except Exception as exc:
            logger.debug("ThoughtTree._call error: %s", exc)
            return ""

    async def think(self, question: str, context: str = "") -> str:
        """
        Run the full ToT pipeline and return the best synthesised answer.
        Falls back to empty string if the llm_fn is not wired.
        """
        if self._llm_fn is None:
            return ""

        ctx_block = f"\nContext:\n{_truncate(context, 400)}\n" if context else ""

        # Step 1: Generate N hypotheses in parallel
        async def gen_hypothesis(branch_id: int) -> str:
            variation = [
                "Think step-by-step.",
                "Consider edge cases first.",
                "Approach this from a systems perspective.",
            ]
            hint = variation[branch_id % len(variation)]
            prompt = (
                f"You are a reasoning engine. {hint}\n"
                f"{ctx_block}"
                f"Question: {question}\n"
                f"Give a concise, thoughtful answer:"
            )
            return await self._call(prompt, max_tokens=250)

        hypotheses = await asyncio.gather(
            *[gen_hypothesis(i) for i in range(self.branches)],
            return_exceptions=True,
        )
        valid_hypotheses = [h for h in hypotheses if isinstance(h, str) and h.strip()]
        if not valid_hypotheses:
            return ""

        # Step 2: Critique each hypothesis in parallel
        async def critique(hypothesis: str, branch_id: int) -> Thought:
            prompt = (
                f"Rate this answer on a scale of 0.0-1.0 for:\n"
                f"  - Correctness\n  - Completeness\n  - Safety\n\n"
                f"Answer being rated:\n{hypothesis}\n\n"
                f"Reply with ONLY a JSON object: "
                f'{{ "score": <float>, "critique": "<one sentence>" }}'
            )
            raw = await self._call(prompt, max_tokens=80)
            try:
                parsed = json.loads(raw)
                score = float(parsed.get("score", 0.5))
                critique_text = str(parsed.get("critique", ""))
            except Exception:
                score = 0.5
                critique_text = "Unable to parse critique."
            return Thought(
                branch_id=branch_id,
                hypothesis=hypothesis,
                critique=critique_text,
                score=max(0.0, min(1.0, score)),
            )

        thoughts = await asyncio.gather(
            *[critique(h, i) for i, h in enumerate(valid_hypotheses)],
            return_exceptions=True,
        )
        valid_thoughts: list[Thought] = [t for t in thoughts if isinstance(t, Thought)]
        if not valid_thoughts:
            return valid_hypotheses[0]

        # Step 3: Sort and pick best
        valid_thoughts.sort(key=lambda t: t.score, reverse=True)
        best = valid_thoughts[0]

        # Step 4: Synthesise top-2 if they're close
        if len(valid_thoughts) >= 2 and (valid_thoughts[0].score - valid_thoughts[1].score) < 0.15:
            synthesis_prompt = (
                f"Synthesise these two answers into one optimal response:\n\n"
                f"Answer A: {valid_thoughts[0].hypothesis}\n\n"
                f"Answer B: {valid_thoughts[1].hypothesis}\n\n"
                f"Synthesised answer:"
            )
            synthesised = await self._call(synthesis_prompt, max_tokens=300)
            if synthesised.strip():
                return synthesised

        return best.hypothesis


# ── MetaCritic ─────────────────────────────────────────────────────────────────


@dataclass
class CritiqueResult:
    score: float  # 0-1
    confidence: float
    completeness: float
    safety: float
    issues: list[str]
    should_revise: bool


@dataclass
class AdaptationCandidate:
    trigger: str
    guidance: str
    issue_hint: str = ""


@dataclass
class AdaptationRule:
    uid: str
    trigger: str
    guidance: str
    vector: np.ndarray
    created_at: float
    updated_at: float
    successes: int = 0
    failures: int = 0
    issue_hint: str = ""


class MetaCritic:
    """
    Scores an assistant response against the user's original intent.
    If the score falls below METACRITIC_THRESHOLD, signals that a revision
    pass should be triggered.
    """

    def __init__(self) -> None:
        self._llm_fn: Callable | None = None

    def set_llm(self, fn: Callable) -> None:
        self._llm_fn = fn

    async def score(self, user_msg: str, response: str) -> CritiqueResult:
        if self._llm_fn is None:
            return CritiqueResult(
                score=1.0,
                confidence=1.0,
                completeness=1.0,
                safety=1.0,
                issues=[],
                should_revise=False,
            )
        prompt = (
            f"Evaluate this AI assistant response.\n\n"
            f"User asked: {_truncate(user_msg, 200)}\n"
            f"Response: {_truncate(response, 400)}\n\n"
            f"Reply ONLY with JSON:\n"
            f'{{"confidence":0.0-1.0,"completeness":0.0-1.0,"safety":0.0-1.0,'
            f'"issues":["<issue1>"],"overall":0.0-1.0}}'
        )
        try:
            raw = await self._llm_fn(prompt, 120)
            parsed = json.loads(raw or "{}")
        except Exception:
            parsed = {}

        confidence = float(parsed.get("confidence", 0.8))
        completeness = float(parsed.get("completeness", 0.8))
        safety = float(parsed.get("safety", 1.0))
        overall = float(parsed.get("overall", (confidence + completeness + safety) / 3))
        issues = [str(i) for i in parsed.get("issues", [])]
        return CritiqueResult(
            score=max(0.0, min(1.0, overall)),
            confidence=confidence,
            completeness=completeness,
            safety=safety,
            issues=issues,
            should_revise=overall < METACRITIC_THRESHOLD,
        )


# ── Context Forge ──────────────────────────────────────────────────────────────


class ContextForge:
    """
    Dynamically assembles the richest possible system-prompt addendum that
    fits within MAX_CONTEXT_TOKENS.  Priority order:

      1. Relevant semantic memories (facts, observations)
      2. Similar episodic recalls (past success patterns)
      3. Working-memory scratch pad (key entities from current conversation)
    """

    def __init__(self, store: SemanticStore, episodes: EpisodicLog) -> None:
        self.store = store
        self.episodes = episodes
        self._scratch: dict[str, str] = {}  # entity → summary

    def update_scratch(self, key: str, value: str) -> None:
        self._scratch[key] = value

    def clear_scratch(self) -> None:
        self._scratch.clear()

    def forge(self, user_message: str) -> str:
        """
        Return the brain-augmented context block.
        Empty string if nothing meaningful is available.
        """
        budget = MAX_CONTEXT_TOKENS
        sections: list[str] = []

        # ── 1. Semantic memory hits ────────────────────────────────────────────
        hits = self.store.query(user_message, top_k=TOP_K_RETRIEVAL)
        if hits:
            mem_lines: list[str] = []
            used = 0
            for entry in hits:
                snippet = f"• [{entry.source}] {entry.text}"
                tok = _token_estimate(snippet)
                if used + tok > budget // 2:
                    break
                mem_lines.append(snippet)
                used += tok
            if mem_lines:
                sections.append("RELEVANT MEMORIES:\n" + "\n".join(mem_lines))
                budget -= used

        # ── 2. Episodic recalls ────────────────────────────────────────────────
        past = self.episodes.find_similar(user_message, top_k=2)
        if past:
            ep_lines: list[str] = []
            used = 0
            for ep in past:
                if ep.outcome not in ("success", "partial"):
                    continue
                snippet = (
                    f"• PAST [{ep.outcome}]: '{_truncate(ep.user_msg, 80)}' → '{_truncate(ep.assistant_response, 120)}'"
                )
                tok = _token_estimate(snippet)
                if used + tok > budget // 3:
                    break
                ep_lines.append(snippet)
                used += tok
            if ep_lines:
                sections.append("EPISODIC RECALL (what worked before):\n" + "\n".join(ep_lines))
                budget -= used

        # ── 3. Working scratch pad ─────────────────────────────────────────────
        if self._scratch and budget > 100:
            scratch_lines = [f"• {k}: {_truncate(v, 60)}" for k, v in list(self._scratch.items())[-8:]]
            sections.append("WORKING MEMORY:\n" + "\n".join(scratch_lines))

        if not sections:
            return ""

        return "\n\n".join(sections)


# ── Curiosity Engine ───────────────────────────────────────────────────────────


class CuriosityEngine:
    """
    Detects knowledge gaps in the semantic store and schedules background
    fills.  Runs as a long-lived asyncio task.

    Gap detection: after every ingestion, check if the response contained
    phrases like "I don't know", "I'm not sure", "I cannot find" etc.
    When found, queue a self-research task.
    """

    _GAP_PATTERNS = re.compile(
        r"i (don'?t|do not|cannot|can'?t) (know|find|recall|remember|confirm)|"
        r"i('?m| am) (not sure|unsure|uncertain)|"
        r"i have no (information|data|knowledge) (about|on)",
        re.I,
    )

    def __init__(self, store: SemanticStore) -> None:
        self.store = store
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
        self._llm_fn: Callable | None = None
        self._running = False

    def set_llm(self, fn: Callable) -> None:
        self._llm_fn = fn

    def inspect(self, user_msg: str, response: str) -> None:
        """Check response for knowledge gaps; enqueue research topics."""
        if self._GAP_PATTERNS.search(response):
            topic = _truncate(user_msg, 120)
            if not self._queue.full():
                self._queue.put_nowait(topic)

    async def run(self) -> None:
        """Background loop: fill knowledge gaps via LLM self-research."""
        self._running = True
        while self._running:
            try:
                topic = await asyncio.wait_for(self._queue.get(), timeout=30.0)
            except TimeoutError:
                continue
            if self._llm_fn is None:
                continue
            try:
                prompt = (
                    f"You are a self-improving AI. Provide a concise, factual 2-3 sentence "
                    f"summary about the following topic that will help you answer future "
                    f"questions more accurately:\n\nTopic: {topic}"
                )
                fact = await self._llm_fn(prompt, 150)
                if fact and len(fact.strip()) > 20:
                    self.store.add(
                        text=f"[auto-researched] {topic}: {fact.strip()}",
                        source="observation",
                        importance=0.6,
                    )
                    logger.debug("CuriosityEngine filled gap: %s", topic[:60])
            except Exception as exc:
                logger.debug("CuriosityEngine error: %s", exc)

    def stop(self) -> None:
        self._running = False


class SelfEvolutionEngine:
    """Learn small, durable behavior rules from outcomes and critiques."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._rules: dict[str, AdaptationRule] = {}
        self._llm_fn: Callable | None = None
        self._load()

    def set_llm(self, fn: Callable) -> None:
        self._llm_fn = fn

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for item in raw:
                vector = np.array(item["vector"], dtype=np.float32)
                rule = AdaptationRule(
                    uid=item["uid"],
                    trigger=item["trigger"],
                    guidance=item["guidance"],
                    vector=vector,
                    created_at=float(item.get("created_at", 0.0)),
                    updated_at=float(item.get("updated_at", 0.0)),
                    successes=int(item.get("successes", 0)),
                    failures=int(item.get("failures", 0)),
                    issue_hint=str(item.get("issue_hint", "")),
                )
                self._rules[rule.uid] = rule
            logger.info("SelfEvolutionEngine loaded %d rules", len(self._rules))
        except Exception as exc:
            logger.warning("SelfEvolutionEngine load error: %s", exc)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "uid": rule.uid,
                "trigger": rule.trigger,
                "guidance": rule.guidance,
                "vector": rule.vector.tolist(),
                "created_at": rule.created_at,
                "updated_at": rule.updated_at,
                "successes": rule.successes,
                "failures": rule.failures,
                "issue_hint": rule.issue_hint,
            }
            for rule in self._rules.values()
        ]
        self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def __len__(self) -> int:
        return len(self._rules)

    def _upsert(self, candidate: AdaptationCandidate) -> AdaptationRule:
        basis = f"{candidate.trigger}\n{candidate.guidance}"
        uid = _hash_text(basis)
        now = time.time()
        if uid in self._rules:
            rule = self._rules[uid]
            rule.updated_at = now
            if candidate.issue_hint:
                rule.issue_hint = candidate.issue_hint
            return rule

        rule = AdaptationRule(
            uid=uid,
            trigger=candidate.trigger,
            guidance=candidate.guidance,
            vector=_embed_engine.embed(basis),
            created_at=now,
            updated_at=now,
            issue_hint=candidate.issue_hint,
        )
        self._rules[uid] = rule
        self._prune()
        return rule

    def _prune(self) -> None:
        if len(self._rules) <= MAX_ADAPTATIONS:
            return
        scored = sorted(
            self._rules.values(),
            key=lambda rule: (
                (rule.failures * 1.5) + (rule.successes * 0.5),
                rule.updated_at,
            ),
        )
        for rule in scored[: len(self._rules) - MAX_ADAPTATIONS]:
            del self._rules[rule.uid]

    def query(self, text: str, top_k: int = TOP_K_ADAPTATIONS) -> list[AdaptationRule]:
        if not self._rules:
            return []
        q_vec = _embed_engine.embed(text)
        candidates = list(self._rules.values())
        vectors = np.stack([rule.vector for rule in candidates])
        sims = vectors @ q_vec
        order = np.argsort(sims)[::-1]
        results: list[AdaptationRule] = []
        for idx in order:
            rule = candidates[int(idx)]
            similarity = float(sims[int(idx)])
            if similarity < 0.18:
                continue
            results.append(rule)
            if len(results) >= top_k:
                break
        return results

    def build_guidance_block(self, user_message: str) -> str:
        hits = self.query(user_message, top_k=TOP_K_ADAPTATIONS)
        if not hits:
            return ""
        lines = [f"• {rule.guidance}" for rule in hits]
        return "SELF-EVOLUTION RULES (adapt from prior outcomes):\n" + "\n".join(lines)

    def snapshot(self, top_k: int = TOP_K_ADAPTATIONS) -> list[dict[str, Any]]:
        ranked = sorted(
            self._rules.values(),
            key=lambda rule: (rule.successes + rule.failures, rule.updated_at),
            reverse=True,
        )
        return [
            {
                "trigger": rule.trigger,
                "guidance": rule.guidance,
                "issue_hint": rule.issue_hint,
                "successes": rule.successes,
                "failures": rule.failures,
                "updated_at": rule.updated_at,
            }
            for rule in ranked[:top_k]
        ]

    async def observe(
        self,
        user_message: str,
        assistant_response: str,
        critique: CritiqueResult,
        outcome: str,
        tools_used: list[str] | None = None,
    ) -> None:
        del tools_used
        if outcome == "success" and critique.score >= 0.8:
            for rule in self.query(user_message, top_k=1):
                rule.successes += 1
                rule.updated_at = time.time()
            return

        if not critique.should_revise and outcome not in ("partial", "failure"):
            return

        candidate = await self._derive_candidate(
            user_message=user_message,
            assistant_response=assistant_response,
            critique=critique,
            outcome=outcome,
        )
        if candidate is None:
            return
        rule = self._upsert(candidate)
        rule.failures += 1
        rule.updated_at = time.time()

    async def _derive_candidate(
        self,
        user_message: str,
        assistant_response: str,
        critique: CritiqueResult,
        outcome: str,
    ) -> AdaptationCandidate | None:
        fallback_issue = critique.issues[0] if critique.issues else "Improve completeness and clarity."
        if self._llm_fn is None:
            return self._fallback_candidate(user_message, fallback_issue)

        prompt = (
            "You are extracting one durable self-improvement rule for an AI assistant.\n"
            "Given a weak or partial outcome, produce one concise future-facing rule.\n"
            "Return JSON only with keys trigger, guidance, issue_hint.\n\n"
            f"User message: {_truncate(user_message, 120)}\n"
            f"Assistant response: {_truncate(assistant_response, 160)}\n"
            f"Outcome: {outcome}\n"
            f"Issues: {json.dumps(critique.issues[:3])}\n\n"
            'Example: {"trigger":"Ambiguous setup requests","guidance":"Ask one focused clarifying question before acting when setup scope is unclear.","issue_hint":"ambiguity"}'
        )
        try:
            raw = await self._llm_fn(prompt, 140)
            parsed = json.loads(raw or "{}")
            trigger = str(parsed.get("trigger", "")).strip()
            guidance = str(parsed.get("guidance", "")).strip()
            issue_hint = str(parsed.get("issue_hint", fallback_issue)).strip()
            if trigger and guidance:
                return AdaptationCandidate(trigger=trigger, guidance=guidance, issue_hint=issue_hint)
        except Exception:
            pass
        return self._fallback_candidate(user_message, fallback_issue)

    def _fallback_candidate(self, user_message: str, issue: str) -> AdaptationCandidate:
        issue_lower = issue.lower()
        if "ambigu" in issue_lower or "clarif" in issue_lower or "underspec" in issue_lower:
            guidance = "Ask one focused clarifying question before acting when the request is ambiguous."
        elif "direct" in issue_lower or "command" in issue_lower or "lead" in issue_lower:
            guidance = "Lead with the exact command, action, or answer first, then add the shortest useful explanation."
        elif "safe" in issue_lower or "risk" in issue_lower or "harm" in issue_lower:
            guidance = "Prefer the safest reversible action and state the blocker plainly instead of guessing."
        elif "complete" in issue_lower or "missing" in issue_lower or "omit" in issue_lower:
            guidance = "Cover the request end-to-end; if something is missing, say exactly what is blocked."
        else:
            cleaned_issue = issue.strip().rstrip(".") or "clarity and completeness"
            guidance = f"Improve future responses by explicitly addressing this recurring issue: {cleaned_issue}."
        return AdaptationCandidate(
            trigger=_truncate(user_message, 24),
            guidance=guidance,
            issue_hint=issue,
        )


# ── Brain — Top-Level Façade ───────────────────────────────────────────────────


class Brain:
    """
    The unified cognitive enhancement layer.
    One singleton per process — call `get_brain()` to obtain it.

    Public API
    ----------
    await brain.augment_system(base_system_prompt, user_message)
        → str   — enriched system prompt to pass to the LLM

    await brain.ingest(user_message, assistant_response, tools_used, latency_ms)
        → None  — record the interaction, update memories, run curiosity check

    await brain.think(question, context)
        → str   — run Tree-of-Thoughts for complex / high-stakes questions

    await brain.critique(user_msg, response)
        → CritiqueResult

    brain.save()
        → None  — flush semantic store + episodic log to disk
    """

    def __init__(self) -> None:
        BRAIN_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._store = SemanticStore(BRAIN_DATA_DIR / "semantic.json")
        self._episodes = EpisodicLog(BRAIN_DATA_DIR / "episodes.json")
        self._forge = ContextForge(self._store, self._episodes)
        self._critic = MetaCritic()
        self._tree = ThoughtTree(branches=THOUGHT_BRANCHES)
        self._curiosity = CuriosityEngine(self._store)
        self._evolution = SelfEvolutionEngine(BRAIN_DATA_DIR / "adaptations.json")
        self._llm_fn: Callable | None = None
        self._curiosity_task: asyncio.Task | None = None
        self._save_counter = 0
        logger.info(
            "Brain online — semantic:%d episodes:%d",
            len(self._store),
            len(self._episodes._episodes),
        )

    # ── LLM wiring ─────────────────────────────────────────────────────────────

    def wire_llm(self, fast_completion_fn: Callable) -> None:
        """
        Provide the `_fast_completion` coroutine from live_chat_app.
        Must be called before any async methods are used.
        """
        self._llm_fn = fast_completion_fn
        self._critic.set_llm(fast_completion_fn)
        self._tree.set_llm(fast_completion_fn)
        self._curiosity.set_llm(fast_completion_fn)
        self._evolution.set_llm(fast_completion_fn)

    def start_background_tasks(self) -> None:
        """Launch the curiosity engine. Call once the event loop is running."""
        if self._curiosity_task is None or self._curiosity_task.done():
            self._curiosity_task = asyncio.create_task(self._curiosity.run(), name="brain_curiosity")

    def stop(self) -> None:
        """Graceful shutdown."""
        self._curiosity.stop()
        if self._curiosity_task and not self._curiosity_task.done():
            self._curiosity_task.cancel()
        self.save()

    # ── Core API ────────────────────────────────────────────────────────────────

    async def augment_system(self, base_prompt: str, user_message: str) -> str:
        """
        Enrich the system prompt with the most relevant context the brain
        has assembled for this specific user message.
        """
        evolution_block = self._evolution.build_guidance_block(user_message)
        brain_block = self._forge.forge(user_message)
        blocks = [block for block in (evolution_block, brain_block) if block]
        if not blocks:
            return base_prompt
        separator = "\n\n── BRAIN AUGMENTATION ──────────────────────────────────────────────\n"
        return (
            base_prompt
            + separator
            + "\n\n".join(blocks)
            + "\n────────────────────────────────────────────────────────────────────\n"
        )

    async def ingest(
        self,
        user_message: str,
        assistant_response: str,
        tools_used: list[str] | None = None,
        latency_ms: float = 0.0,
        outcome: str = "unknown",
    ) -> None:
        """
        Record a completed interaction.  Also:
        - Extracts key entities into the scratch pad
        - Checks for knowledge gaps (curiosity)
        - Periodically persists to disk
        """
        critique = await self._critic.score(user_message, assistant_response)

        # Record episode
        self._episodes.record(
            user_msg=user_message,
            assistant_response=assistant_response,
            outcome=outcome,
            tools_used=tools_used or [],
            latency_ms=latency_ms,
            metacritic_score=critique.score,
        )
        await self._evolution.observe(
            user_message,
            assistant_response,
            critique=critique,
            outcome=outcome,
            tools_used=tools_used or [],
        )

        # Extract salient content into semantic store
        combined = f"Q: {user_message}\nA: {assistant_response}"
        importance = 1.2 if outcome == "success" else 0.8
        self._store.add(combined, source="episodic", importance=importance)

        # Curiosity gap detection
        self._curiosity.inspect(user_message, assistant_response)

        # Scratch-pad: remember what the user was working on
        self._forge.update_scratch("last_topic", _truncate(user_message, 80))

        # Auto-save every 10 interactions
        self._save_counter += 1
        if self._save_counter % 10 == 0:
            await asyncio.get_running_loop().run_in_executor(None, self.save)

    async def think(self, question: str, context: str = "") -> str:
        """Invoke Tree-of-Thoughts for high-complexity or important queries."""
        return await self._tree.think(question, context)

    async def critique(self, user_msg: str, response: str) -> CritiqueResult:
        """Score a response and return a CritiqueResult."""
        return await self._critic.score(user_msg, response)

    def remember(self, text: str, source: str = "fact", importance: float = 1.0) -> None:
        """Manually inject a fact into the semantic store."""
        self._store.add(text, source=source, importance=importance)

    def recall(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> list[str]:
        """Return the text of the top-k semantically similar memories."""
        return [e.text for e in self._store.query(query, top_k=top_k)]

    def update_working_memory(self, key: str, value: str) -> None:
        """Update an entity in the contextual scratch pad."""
        self._forge.update_scratch(key, value)

    def clear_working_memory(self) -> None:
        """Reset the scratch pad (on session reset)."""
        self._forge.clear_scratch()

    def save(self) -> None:
        """Flush everything to disk."""
        try:
            self._store.save()
            self._episodes.save()
            self._evolution.save()
        except Exception as exc:
            logger.warning("Brain.save error: %s", exc)

    # ── Introspection ───────────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """Return a diagnostic snapshot."""
        return {
            "semantic_memories": len(self._store),
            "episodes": len(self._episodes._episodes),
            "episode_success_rate": round(self._episodes.success_rate(), 3),
            "curiosity_queue_depth": self._curiosity._queue.qsize(),
            "adaptation_rules": len(self._evolution),
            "top_adaptations": self._evolution.snapshot(),
            "llm_wired": self._llm_fn is not None,
            "curiosity_running": bool(self._curiosity_task and not self._curiosity_task.done()),
            "scratch_keys": list(self._forge._scratch.keys()),
        }


# ── Singleton ──────────────────────────────────────────────────────────────────

_brain_instance: Brain | None = None


def get_brain() -> Brain:
    """Return the process-wide Brain singleton."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = Brain()
    return _brain_instance
