from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

import live_chat_app


def test_active_elevenlabs_voice_id_prefers_saved_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(live_chat_app, "tts_voice_id", "hitch-voice-id")
    assert live_chat_app._active_elevenlabs_voice_id() == "hitch-voice-id"

    monkeypatch.setattr(live_chat_app, "tts_voice_id", "")
    assert live_chat_app._active_elevenlabs_voice_id() == live_chat_app.VOICE_ID


@pytest.mark.asyncio
async def test_broadcast_voice_settings_includes_elevenlabs_voice_id(monkeypatch: pytest.MonkeyPatch) -> None:
    broadcasts: list[dict[str, object]] = []

    async def fake_broadcast(message: dict[str, object]) -> None:
        broadcasts.append(message)

    monkeypatch.setattr(live_chat_app, "broadcast", fake_broadcast)
    monkeypatch.setattr(live_chat_app, "preferred_stt", "local")
    monkeypatch.setattr(live_chat_app, "preferred_tts", "elevenlabs")
    monkeypatch.setattr(live_chat_app, "tts_rate", 175)
    monkeypatch.setattr(live_chat_app, "tts_voice_idx", 0)
    monkeypatch.setattr(live_chat_app, "tts_voice_id", "hitch-voice-id")

    await live_chat_app._broadcast_voice_settings_update()

    assert broadcasts == [
        {
            "type": "voice_settings",
            "preferred_stt": "local",
            "preferred_tts": "elevenlabs",
            "tts_rate": 175,
            "tts_voice_idx": 0,
            "tts_voice_id": "hitch-voice-id",
        }
    ]


@pytest.mark.asyncio
async def test_api_voices_returns_elevenlabs_provider_voices(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEngine:
        def getProperty(self, name: str):
            if name == "voices":
                return []
            raise AssertionError(f"unexpected property {name}")

        def stop(self) -> None:
            return None

    class FakeVoicesApi:
        def get_all(self) -> SimpleNamespace:
            return SimpleNamespace(voices=[SimpleNamespace(voice_id="hitch-voice-id", name="Hitch")])

    class FakeElevenLabs:
        def __init__(self, **_kwargs) -> None:
            self.voices = FakeVoicesApi()

    monkeypatch.setitem(sys.modules, "pyttsx3", SimpleNamespace(init=lambda: FakeEngine()))
    monkeypatch.setattr(live_chat_app, "ElevenLabs", FakeElevenLabs)
    monkeypatch.setattr(live_chat_app, "_load_key", lambda provider, env: "fake-key" if env == "ELEVENLABS_API_KEY" else "")
    monkeypatch.setattr(live_chat_app, "_elevenlabs_auth_failed", False)

    response = await live_chat_app.api_voices()
    payload = json.loads(response.body)

    assert payload["providers"]["elevenlabs"]["available"] is True
    assert payload["providers"]["elevenlabs"]["voices"] == [
        {
            "id": "hitch-voice-id",
            "name": "Hitch",
            "index": 0,
            "type": "elevenlabs",
        }
    ]
