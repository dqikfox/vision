# Self-Aware Retrieval LangGraph Agent

This project is now a more capable LangGraph scaffold with:
- durable namespace-aware file-backed memory
- retrieval over stored memories
- self-state and operating-principles storage
- session summaries
- explicit intent, comprehension, and reasoning-outline fields
- LangSmith-ready tracing support
- OpenHarness memory mirroring
- optional Open Orchestrator memory integration
- verified no-auth API catalog for agent/tool prototyping

## What changed

### 1. Retrieval layer
The agent now ranks relevant stored memories for the current message and returns a `retrieved_context` field.

Current retrieval is lightweight lexical scoring, which is a good scaffold before adding embeddings/vector search.

### 2. LangSmith tracing scaffold
`src/agent/telemetry.py` adds best-effort tracing wrappers. If `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true` are set, calls can be traced.

### 3. OpenHarness memory bridge
`src/agent/openharness_bridge.py` can mirror durable notes into the OpenHarness memory root and maintain a `MEMORY.md` index.

### 4. Self-awareness and comprehension
The agent keeps explicit structured metadata about:
- identity
- capabilities
- limitations
- principles
- inferred intent
- comprehension summary
- reasoning outline

## Storage layout
Primary memory store:

```text
<AGENT_MEMORY_DIR or ~/.openharness/data/memory/langgraph-agent>/<namespace>/
  memory.json
  session.json
  self.json
```

OpenHarness mirror:

```text
<OPENHARNESS_MEMORY_DIR or ~/.openharness/data/memory>/
  MEMORY.md
  langgraph-<namespace>-<key>.md
```

## Example messages

Show verified API catalog:

```json
{"message": "show api catalog"}
```

Store memory:

```json
{"message": "remember favorite_editor=neovim"}
```

Recall with retrieval:

```json
{"message": "what editor do i like?"}
```

Self-reflection:

```json
{"message": "who are you?"}
```

## Enable LangSmith
Create `.env` from `.env.example` and add:

```text
LANGSMITH_API_KEY=lsv2...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=openharness-self-aware-agent
```

## Run

```bash
cd LANGGRAPH
pip install -e . "langgraph-cli[inmem]"
langgraph dev
```

## Open Orchestrator integration

This repo can now optionally bridge into Open Orchestrator's stronger memory stack:
- topic memory via `.owt/memory/MEMORY.md`
- SQLite recall memory via `recall.db`

Enable it by passing runtime context like:

```json
{
  "use_open_orchestrator_memory": true,
  "open_orchestrator_repo_root": "C:/project/openorchestrator"
}
```

This is the right direction because Open Orchestrator already provides:
- FTS-backed recall store
- layered memory budgets
- mined facts
- orchestration/swarms/peer messaging

## Suggested next upgrades
- replace lexical retrieval with embeddings/vector search
- add a real LLM-backed synthesis node
- package reusable behavior as an agent skill repo structure similar to netresearch/agent-skill-repo
- add MCP tools as graph nodes
