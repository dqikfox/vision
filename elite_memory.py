"""
elite_memory.py — Semantic memory, context optimization, auto-summarization
==========================================================================
Sliding window context, relevance ranking, automatic summary generation.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class Message:
    """Single conversation message with metadata."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    tokens: int = 0
    relevance_score: float = 1.0
    is_summary: bool = False

class ContextOptimizer:
    """Sliding window context management."""
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.messages: List[Message] = []
        self.total_tokens = 0
    
    def add_message(self, role: str, content: str, tokens: int = 0) -> None:
        """Add message and trim if over limit."""
        msg = Message(role=role, content=content, tokens=tokens or len(content) // 4)
        self.messages.append(msg)
        self.total_tokens += msg.tokens
        self._trim_context()
    
    def _trim_context(self) -> None:
        """Remove least relevant messages to fit token budget."""
        while self.total_tokens > self.max_tokens and len(self.messages) > 1:
            # Keep system prompts, remove oldest non-critical
            candidates = [
                (i, m) for i, m in enumerate(self.messages)
                if m.role != "system"
            ]
            if not candidates:
                break
            
            # Remove oldest message
            idx, msg = min(candidates, key=lambda x: x[1].timestamp)
            self.messages.pop(idx)
            self.total_tokens -= msg.tokens
    
    def get_context(self) -> List[dict]:
        """Return optimized context for LLM."""
        return [
            {
                "role": m.role,
                "content": m.content,
            }
            for m in self.messages
        ]
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4

class ConversationSummarizer:
    """Auto-generate summaries of lengthy conversations."""
    
    def __init__(self, threshold_messages: int = 20):
        self.threshold = threshold_messages
        self.summaries: List[str] = []
    
    async def maybe_summarize(
        self,
        messages: List[Message],
        summarize_fn,  # async callable returning summary
    ) -> Optional[str]:
        """Trigger summarization if messages exceed threshold."""
        if len(messages) < self.threshold:
            return None
        
        # Summarize oldest 70% of messages
        cutoff = int(len(messages) * 0.7)
        to_summarize = messages[:cutoff]
        
        conversation_text = "\n".join([
            f"{m.role}: {m.content}" for m in to_summarize
        ])
        
        summary = await summarize_fn(conversation_text)
        self.summaries.append(summary)
        
        # Replace old messages with summary
        return summary

class SemanticMemoryIndex:
    """Index messages for semantic search (basic similarity)."""
    
    def __init__(self):
        self.index: dict[str, List[tuple[int, float]]] = {}  # keyword → [(msg_idx, relevance), ...]
    
    def index_message(self, idx: int, content: str) -> None:
        """Index message by keywords."""
        words = content.lower().split()
        for word in set(words):
            if len(word) > 3:  # Skip short words
                if word not in self.index:
                    self.index[word] = []
                self.index[word].append((idx, 1.0))
    
    def search(self, query: str, top_k: int = 3) -> List[int]:
        """Find most relevant messages by keyword overlap."""
        query_words = set(query.lower().split())
        scores: dict[int, float] = {}
        
        for word in query_words:
            if word in self.index:
                for idx, _ in self.index[word]:
                    scores[idx] = scores.get(idx, 0) + 1.0
        
        # Return top-k message indices
        return [idx for idx, _ in sorted(scores.items(), key=lambda x: -x[1])[:top_k]]

class EliteMemory:
    """Enhanced memory with context optimization + semantic search."""
    
    def __init__(self, memory_file: Path = None):
        self.context_opt = ContextOptimizer(max_tokens=8000)
        self.summarizer = ConversationSummarizer()
        self.search_index = SemanticMemoryIndex()
        self.memory_file = memory_file or Path("memory.json")
        self.facts: dict[str, list[str]] = {}
        self.load()
    
    def add_message(self, role: str, content: str) -> None:
        """Add message with indexing."""
        self.context_opt.add_message(role, content)
        idx = len(self.context_opt.messages) - 1
        self.search_index.index_message(idx, content)
    
    async def maybe_summarize(self, summarize_fn) -> Optional[str]:
        """Auto-summarize if needed."""
        return await self.summarizer.maybe_summarize(
            self.context_opt.messages,
            summarize_fn,
        )
    
    def get_context(self) -> List[dict]:
        """Get optimized context for LLM."""
        return self.context_opt.get_context()
    
    def search(self, query: str) -> List[str]:
        """Semantic search in conversation."""
        indices = self.search_index.search(query)
        return [
            self.context_opt.messages[i].content
            for i in indices
            if i < len(self.context_opt.messages)
        ]
    
    def add_fact(self, category: str, fact: str) -> None:
        """Store semantic fact."""
        if category not in self.facts:
            self.facts[category] = []
        self.facts[category].append(fact)
        self.save()
    
    def get_facts(self, category: str) -> List[str]:
        """Retrieve facts by category."""
        return self.facts.get(category, [])
    
    def save(self) -> None:
        """Persist to disk."""
        data = {
            "facts": self.facts,
            "updated": datetime.now().isoformat(),
        }
        try:
            self.memory_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"[memory] save failed: {e}")
    
    def load(self) -> None:
        """Load from disk."""
        if not self.memory_file.exists():
            return
        try:
            data = json.loads(self.memory_file.read_text())
            self.facts = data.get("facts", {})
        except Exception as e:
            print(f"[memory] load failed: {e}")
    
    def clear(self) -> None:
        """Clear all memory."""
        self.context_opt.messages.clear()
        self.context_opt.total_tokens = 0
        self.facts.clear()
        self.save()
