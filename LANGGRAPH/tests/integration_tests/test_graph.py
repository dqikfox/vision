import json

import pytest

from agent import graph

pytestmark = pytest.mark.anyio


async def test_agent_echoes_message() -> None:
    res = await graph.ainvoke({"message": "hello"})
    assert "You said: hello" in res["response"]
    assert res["intent"] == "general_response"


async def test_agent_persists_memory(tmp_path) -> None:
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AGENT_MEMORY_DIR", str(tmp_path))
        first = await graph.ainvoke({"message": "remember favorite_editor=neovim"})
        second = await graph.ainvoke({"message": "what editor do i like?"})
    assert "Stored memory: favorite_editor=neovim" in first["response"]
    assert "favorite_editor: neovim" in second["response"]
    assert second["retrieved_context"] != "No relevant memory matches found."


async def test_agent_self_reflection(tmp_path) -> None:
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AGENT_MEMORY_DIR", str(tmp_path))
        result = await graph.ainvoke({"message": "who are you?"})
    assert "Identity:" in result["response"]
    assert result["intent"] == "self_reflection"


async def test_agent_returns_api_catalog() -> None:
    result = await graph.ainvoke({"message": "show api catalog"})
    assert "Verified no-auth API catalog" in result["response"]
    assert "HTTPBin" in result["response"]


async def test_agent_writes_session_summary(tmp_path) -> None:
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AGENT_MEMORY_DIR", str(tmp_path))
        await graph.ainvoke({"message": "hello"}, context={"memory_namespace": "tester"})
    session_path = tmp_path / "tester" / "session.json"
    payload = json.loads(session_path.read_text(encoding="utf-8"))
    assert payload["last_user_message"] == "hello"
