from __future__ import annotations

import pytest

import live_chat_app


@pytest.mark.asyncio
async def test_manual_model_selection_persists_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    saved_states: list[tuple[str | None, str | None]] = []
    broadcasts: list[dict[str, object]] = []
    cleared: list[bool] = []

    async def fake_broadcast(message: dict[str, object]) -> None:
        broadcasts.append(message)

    def fake_save_settings() -> None:
        saved_states.append((live_chat_app.selected_model_provider, live_chat_app.selected_model_name))

    monkeypatch.setattr(live_chat_app, "broadcast", fake_broadcast)
    monkeypatch.setattr(live_chat_app, "_save_settings", fake_save_settings)
    monkeypatch.setattr(live_chat_app, "_clear_all_histories", lambda: cleared.append(True))
    monkeypatch.setattr(live_chat_app, "write_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(live_chat_app, "current_provider", "ollama")
    monkeypatch.setattr(live_chat_app, "current_model", "gpt-oss:20b")
    monkeypatch.setattr(live_chat_app, "selected_model_provider", None)
    monkeypatch.setattr(live_chat_app, "selected_model_name", None)
    monkeypatch.setattr(live_chat_app, "_ollama_failover_active", True)

    await live_chat_app._set_manual_model_selection("anthropic", "claude-3-7-sonnet-latest", clear_histories=True)

    assert live_chat_app.current_provider == "anthropic"
    assert live_chat_app.current_model == "claude-3-7-sonnet-latest"
    assert live_chat_app.selected_model_provider == "anthropic"
    assert live_chat_app.selected_model_name == "claude-3-7-sonnet-latest"
    assert live_chat_app._ollama_failover_active is False
    assert saved_states == [("anthropic", "claude-3-7-sonnet-latest")]
    assert cleared == [True]
    assert broadcasts == [
        {
            "type": "model_changed",
            "provider": "anthropic",
            "model": "claude-3-7-sonnet-latest",
        }
    ]


def test_restore_saved_model_selection_reuses_last_manual_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(live_chat_app, "selected_model_provider", "openai")
    monkeypatch.setattr(live_chat_app, "selected_model_name", "gpt-4.1")
    monkeypatch.setattr(live_chat_app, "current_provider", "ollama")
    monkeypatch.setattr(live_chat_app, "current_model", "gpt-oss:20b")

    assert live_chat_app._restore_saved_model_selection() is True
    assert live_chat_app.current_provider == "openai"
    assert live_chat_app.current_model == "gpt-4.1"


@pytest.mark.asyncio
async def test_llm_stream_does_not_auto_switch_on_ollama_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_ollama_stream(_user_text: str):
        yield "Ollama error: local service unavailable"

    async def fake_compress_history() -> None:
        return None

    monkeypatch.setattr(live_chat_app, "_append_history", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(live_chat_app, "_compress_history_if_needed", fake_compress_history)
    monkeypatch.setattr(live_chat_app, "_llm_stream_ollama", fake_ollama_stream)
    monkeypatch.setattr(live_chat_app, "allow_model_auto_switching", False)
    monkeypatch.setattr(live_chat_app, "current_provider", "ollama")
    monkeypatch.setattr(live_chat_app, "current_model", "gpt-oss:20b")
    monkeypatch.setattr(live_chat_app, "_provider_failure_until", {})

    chunks = [chunk async for chunk in live_chat_app.llm_stream("hello")]

    assert chunks == ["Ollama error: local service unavailable"]
    assert live_chat_app.current_provider == "ollama"
    assert live_chat_app.current_model == "gpt-oss:20b"
