from pathlib import Path

from langgraph.pregel import Pregel

from agent.api_catalog import render_api_catalog
from agent.graph import graph
from agent.memory import FileMemoryStore, build_reasoning_outline, extract_memory_updates, infer_intent
from agent.openharness_bridge import append_topic_note
from agent.owt_bridge import OwtUnavailableError
from agent.retrieval import retrieve_relevant_memories


def test_graph_compiles() -> None:
    assert isinstance(graph, Pregel)


def test_extract_memory_updates() -> None:
    assert extract_memory_updates("remember favorite shell = bash") == {"favorite_shell": "bash"}
    assert extract_memory_updates("hello") == {}


def test_file_memory_store_round_trip(tmp_path) -> None:
    store = FileMemoryStore(str(tmp_path), namespace="test-user")
    store.upsert("theme", "dark", source="test")
    record = store.get("theme")
    assert record is not None
    assert record.value == "dark"


def test_intent_inference() -> None:
    assert infer_intent("remember theme=dark") == "store_memory"
    assert infer_intent("what do you know about me?") == "recall_memory"
    assert infer_intent("who are you?") == "self_reflection"


def test_reasoning_outline() -> None:
    outline = build_reasoning_outline("general_response", 2, "Agent")
    assert outline[0] == "Detected intent: general_response"


def test_retrieval_returns_match(tmp_path) -> None:
    store = FileMemoryStore(str(tmp_path), namespace="test-user")
    store.upsert("favorite_editor", "neovim", source="test")
    results = retrieve_relevant_memories(store, "editor")
    assert results
    assert results[0].key == "favorite_editor"


def test_openharness_bridge_writes_topic(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENHARNESS_MEMORY_DIR", str(tmp_path))
    path = append_topic_note("agent-topic", "# Topic\n")
    assert path == Path(tmp_path) / "agent-topic.md"
    assert path.exists()


def test_render_api_catalog() -> None:
    catalog = render_api_catalog()
    assert "HTTPBin" in catalog
    assert "REST Countries" in catalog


def test_owt_bridge_import_guard() -> None:
    try:
        raise OwtUnavailableError("missing")
    except OwtUnavailableError as exc:
        assert str(exc) == "missing"
