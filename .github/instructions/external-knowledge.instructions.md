---
applyTo: "**/*"
---

# Vision External Knowledge Integration

## Knowledge Sources

Vision integrates with three external knowledge repositories for enhanced context and skills:

### 1. C:\project\skills (Shared Skills Repository)
**Purpose**: Reusable cross-project workflows and specialized skills

**Usage**: When implementing features that benefit from existing patterns or specialized domain knowledge.

**Integration**: Reference skills in Copilot prompts:
```
"Use the [skill-name] skill from C:\project\skills to implement [feature]"
```

**Key Skills Available**:
- Agent frameworks and orchestration
- Accessibility compliance patterns
- API integration templates
- Evaluation and testing frameworks
- Security patterns (Active Directory, authentication)
- Automation workflows
- UI/UX patterns (3D web experiences, WinUI)

### 2. C:\Users\CHANN0$\Documents\unsloth_data (ULTRON Training Corpus)
**Purpose**: ULTRON persona, workflows, and operational knowledge

**Key Files**:
- `00_dataset_manifest.txt` - Overview of training data
- `01_user_system_profile.txt` - User preferences and system config
- `02_projects_and_goals.txt` - Project objectives and roadmap
- `03_tools_mcp_skills_agents_api.txt` - Tool and API documentation
- `04_ultron_persona_and_operating_playbook.txt` - ULTRON operational guidelines
- `05_operator_workflows_and_examples.txt` - Workflow examples
- `99_ultron_private_corpus.txt` - Extended knowledge base

**Usage**: When coordinating with ULTRON or implementing multi-agent workflows, reference this corpus for consistent patterns.

### 3. I:\My Drive\Z\X\rag-v1-package (RAG Package)
**Purpose**: Production RAG system with vector database and artifacts

**Directories**:
- `source_data/` - Raw training data and documents
- `rag_artifacts/` - Processed RAG outputs
- `vector_db/` - Vector database (embeddings)
- `minilm_rag/` - MiniLM-based retrieval system
- `Letta/` - Letta framework integration
- `assistant_upload_staging/` - Prepared data for assistant fine-tuning

**Usage**: For RAG enhancements, reference this production-grade RAG implementation.

## Integration Patterns

### Pattern 1: Skill-Based Feature Implementation
When implementing a new feature, check if a relevant skill exists:

```python
# Example: Implementing accessibility features
# Reference: C:\project\skills\accessibility-compliance-accessibility-audit

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

def check_accessibility_compliance(element: dict[str, Any]) -> dict[str, Any]:
    """Check element for WCAG compliance using patterns from accessibility-audit skill.

    Args:
        element: UI element to audit

    Returns:
        Compliance report with issues and recommendations
    """
    issues = []

    # Color contrast check (WCAG AA: 4.5:1)
    if "color" in element and "background" in element:
        contrast_ratio = calculate_contrast(element["color"], element["background"])
        if contrast_ratio < 4.5:
            issues.append({
                "type": "contrast",
                "severity": "error",
                "message": f"Contrast ratio {contrast_ratio:.2f} below WCAG AA (4.5:1)",
                "recommendation": "Increase color contrast or use darker background"
            })

    # Keyboard accessibility
    if element.get("interactive") and not element.get("keyboard_accessible"):
        issues.append({
            "type": "keyboard",
            "severity": "error",
            "message": "Interactive element not keyboard accessible",
            "recommendation": "Add tabindex and keyboard event handlers"
        })

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "score": calculate_compliance_score(issues)
    }
```

### Pattern 2: ULTRON Coordination
When coordinating with ULTRON, reference the operating playbook:

```python
# Reference: C:\Users\CHANN0$\Documents\unsloth_data\04_ultron_persona_and_operating_playbook.txt

def request_ultron_assistance(task: str, context: dict[str, Any]) -> dict[str, Any]:
    """Request ULTRON assistance following operational guidelines.

    Per ULTRON playbook:
    - Provide clear task description
    - Include relevant context
    - Specify expected output format
    - Set priority level
    """
    return {
        "task": task,
        "context": context,
        "priority": determine_priority(task),
        "expected_format": "structured_response",
        "coordination_mode": "async"  # ULTRON operates asynchronously
    }
```

### Pattern 3: RAG Enhancement
When improving Vision's RAG system, reference the production RAG package:

```python
# Reference: I:\My Drive\Z\X\rag-v1-package

import sqlite3
from pathlib import Path

def integrate_vector_search(
    query: str,
    rag_package_path: Path = Path(r"I:\My Drive\Z\X\rag-v1-package")
) -> list[dict[str, Any]]:
    """Enhance FTS5 search with vector similarity from production RAG.

    Combines:
    - Vision's SQLite FTS5 (fast keyword search)
    - RAG package vector_db (semantic similarity)

    Returns hybrid results ranked by combined score.
    """
    # FTS5 keyword search
    fts_results = vision_fts5_search(query, limit=20)

    # Vector similarity search
    vector_db_path = rag_package_path / "vector_db"
    if vector_db_path.exists():
        vector_results = query_vector_db(query, vector_db_path, limit=20)

        # Merge and re-rank
        return merge_search_results(fts_results, vector_results)

    return fts_results
```

## Referencing External Knowledge

### In Code Comments
```python
# Pattern from C:\project\skills\agent-framework-azure-ai-py
# See: SKILL.md for full agent coordination workflow
```

### In Copilot Prompts
```
"Implement [feature] using patterns from the [skill-name] skill in C:\project\skills"
"Follow ULTRON coordination guidelines from unsloth_data/04_ultron_persona_and_operating_playbook.txt"
"Enhance RAG using vector search patterns from rag-v1-package/minilm_rag"
```

### In Documentation
```markdown
## External References

This implementation follows patterns from:
- **Skill**: `accessibility-compliance-accessibility-audit` (C:\project\skills)
- **ULTRON Playbook**: Section 3.2 - Multi-Agent Coordination
- **RAG Package**: `minilm_rag/` vector search integration
```

## Environment Configuration

Add to `.env`:
```bash
# External Knowledge Sources
SKILLS_REPO_PATH=C:\project\skills
ULTRON_CORPUS_PATH=C:\Users\CHANN0$\Documents\unsloth_data
RAG_PACKAGE_PATH=I:\My Drive\Z\X\rag-v1-package

# Enable external knowledge integration
VISION_USE_SKILLS_REPO=true
VISION_USE_ULTRON_CORPUS=true
VISION_USE_RAG_PACKAGE=true
```

## Best Practices

### 1. Skill Discovery
Before implementing a new feature:
1. Search `C:\project\skills` for relevant patterns
2. Read the skill's `SKILL.md` or `README.md`
3. Adapt patterns to Vision's architecture
4. Reference the skill in code comments

### 2. ULTRON Coordination
When working with ULTRON:
1. Review `04_ultron_persona_and_operating_playbook.txt`
2. Follow established communication patterns
3. Use async coordination (ULTRON operates asynchronously)
4. Reference workflow examples from `05_operator_workflows_and_examples.txt`

### 3. RAG Enhancement
When improving RAG:
1. Study production patterns in `rag-v1-package/`
2. Compare with Vision's SQLite FTS5 approach
3. Consider hybrid search (FTS5 + vector)
4. Reuse preprocessing pipelines from `rag_artifacts/`

### 4. Keep Vision Focused
- **Do**: Reference external knowledge for patterns and inspiration
- **Do**: Adapt patterns to Vision's architecture
- **Don't**: Duplicate external code wholesale
- **Don't**: Create tight coupling to external repos

## Copilot Integration

When Copilot suggests code, it should:
- Check for relevant skills in `C:\project\skills`
- Reference ULTRON playbook for coordination tasks
- Consider RAG package patterns for search enhancements
- Maintain Vision's architectural independence
- Add references to external knowledge in comments

## Examples

### Example 1: Using Agent Framework Skill
```python
# Pattern from: C:\project\skills\agent-framework-azure-ai-py
from __future__ import annotations

class VisionAgent:
    """Vision agent following patterns from agent-framework-azure-ai-py skill."""

    def __init__(self, name: str, capabilities: list[str]):
        self.name = name
        self.capabilities = capabilities
        self.state = "idle"

    async def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute task using agent framework pattern."""
        self.state = "working"
        try:
            result = await self._process_task(task)
            return {"ok": True, "result": result}
        except Exception as e:
            logger.error(f"Agent task failed: {e}")
            return {"ok": False, "error": str(e)}
        finally:
            self.state = "idle"
```

### Example 2: ULTRON Coordination
```python
# Reference: unsloth_data/04_ultron_persona_and_operating_playbook.txt
# Section: Multi-Agent Task Delegation

async def delegate_to_ultron(task_description: str) -> dict[str, Any]:
    """Delegate complex task to ULTRON coordinator.

    Per ULTRON playbook:
    - Use async communication
    - Provide structured task description
    - Include success criteria
    - Set timeout expectations
    """
    message = {
        "type": "task_delegation",
        "task": task_description,
        "delegator": "vision",
        "success_criteria": define_success_criteria(task_description),
        "timeout": 300,  # 5 minutes
        "priority": "normal"
    }

    return await send_to_ultron_queue(message)
```

### Example 3: RAG Package Integration
```python
# Reference: I:\My Drive\Z\X\rag-v1-package\minilm_rag
import numpy as np
from sentence_transformers import SentenceTransformer

class HybridRAG:
    """Hybrid RAG combining Vision FTS5 + RAG package vectors."""

    def __init__(self):
        self.fts_index = VisionFTS5Index()
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.vector_cache = {}

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Hybrid search: FTS5 + vector similarity."""
        # Fast keyword search
        fts_results = self.fts_index.search(query, limit=limit * 2)

        # Semantic reranking
        query_embedding = self.model.encode(query)
        scored_results = []

        for result in fts_results:
            doc_embedding = self._get_embedding(result["content"])
            similarity = np.dot(query_embedding, doc_embedding)
            scored_results.append({
                **result,
                "vector_score": float(similarity),
                "hybrid_score": result["fts_score"] * 0.5 + similarity * 0.5
            })

        # Return top results by hybrid score
        return sorted(scored_results, key=lambda x: x["hybrid_score"], reverse=True)[:limit]
```

## Integration Roadmap

### Phase 1: Discovery (Current)
- ✅ Identify external knowledge sources
- ✅ Document integration patterns
- ✅ Add environment configuration
- ✅ Create Copilot instructions

### Phase 2: Active Integration (Next)
- [ ] Index skills repository for fast search
- [ ] Create skill recommendation system
- [ ] Integrate ULTRON corpus into RAG
- [ ] Implement hybrid search with RAG package

### Phase 3: Automation (Future)
- [ ] Auto-suggest relevant skills during development
- [ ] ULTRON coordination API
- [ ] Real-time RAG package sync
- [ ] Skill usage analytics

## Security & Privacy

- **Skills repo**: Public patterns, safe to reference
- **ULTRON corpus**: Private, contains user preferences and workflows
- **RAG package**: Private, may contain sensitive training data

**Always**:
- Check file permissions before accessing
- Never commit paths to private data
- Use environment variables for paths
- Respect data privacy in shared contexts
