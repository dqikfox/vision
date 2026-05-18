"""Regression tests for STT fallback behavior."""

import asyncio
import sys
from types import SimpleNamespace

import numpy as np
import pytest

import live_chat_app


def _install_fake_faster_whisper(monkeypatch: pytest.MonkeyPatch, transcript: str) -> None:
    class FakeWhisperModel:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def transcribe(self, *_args, **_kwargs):
            return [SimpleNamespace(text=transcript)], None

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=FakeWhisperModel))


def _install_fake_elevenlabs(monkeypatch: pytest.MonkeyPatch, transcript: str) -> None:
    class FakeSpeechToText:
        def convert(self, **_kwargs):
            return SimpleNamespace(text=transcript)

    class FakeElevenLabs:
        def __init__(self, **_kwargs) -> None:
            self.speech_to_text = FakeSpeechToText()

    monkeypatch.setattr(live_chat_app, "ElevenLabs", FakeElevenLabs)


@pytest.mark.asyncio
async def test_local_blank_result_falls_back_to_elevenlabs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Blank local transcripts should not block fallback to a working provider."""
    _install_fake_faster_whisper(monkeypatch, "   ")
    _install_fake_elevenlabs(monkeypatch, "fallback transcript")

    broadcasts: list[dict[str, object]] = []
    logs: list[tuple[str, str]] = []

    async def fake_broadcast(message: dict[str, object]) -> None:
        broadcasts.append(message)

    monkeypatch.setattr(live_chat_app, "broadcast", fake_broadcast)
    monkeypatch.setattr(live_chat_app, "write_log", lambda event, detail: logs.append((event, detail)))
    monkeypatch.setattr(live_chat_app, "_load_key", lambda provider, env: "fake-key" if env == "ELEVENLABS_API_KEY" else "")
    monkeypatch.setattr(live_chat_app, "preferred_stt", "local")
    monkeypatch.setattr(live_chat_app, "continuous_listening", False)
    monkeypatch.setattr(live_chat_app, "_stt_failure_until", 0.0)
    monkeypatch.setattr(live_chat_app, "_stt_groq_failure_until", 0.0)
    monkeypatch.setattr(live_chat_app, "_faster_whisper_model", None)
    monkeypatch.setattr(live_chat_app, "_elevenlabs_auth_failed", False)
    monkeypatch.setattr(live_chat_app, "last_stt_provider", "")

    text = await live_chat_app.transcribe([np.zeros(1600, dtype=np.int16)])
    await asyncio.sleep(0)

    assert text == "fallback transcript"
    assert live_chat_app.last_stt_provider == "elevenlabs"
    assert ("stt/local", "<empty>") in logs
    assert ("stt/elevenlabs", "fallback transcript") in logs
    assert broadcasts[-1] == {
        "type": "stt_active",
        "provider": "elevenlabs",
        "cascade": ["local✗", "elevenlabs"],
    }


@pytest.mark.asyncio
async def test_auto_mode_continues_past_blank_local_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto mode should continue through the cascade when the first provider returns blank text."""
    _install_fake_faster_whisper(monkeypatch, "")
    _install_fake_elevenlabs(monkeypatch, "hello vision")

    broadcasts: list[dict[str, object]] = []

    async def fake_broadcast(message: dict[str, object]) -> None:
        broadcasts.append(message)

    monkeypatch.setattr(live_chat_app, "broadcast", fake_broadcast)
    monkeypatch.setattr(live_chat_app, "write_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(live_chat_app, "_load_key", lambda provider, env: "fake-key" if env == "ELEVENLABS_API_KEY" else "")
    monkeypatch.setattr(live_chat_app, "preferred_stt", "auto")
    monkeypatch.setattr(live_chat_app, "continuous_listening", True)
    monkeypatch.setattr(live_chat_app, "_stt_failure_until", 0.0)
    monkeypatch.setattr(live_chat_app, "_stt_groq_failure_until", 0.0)
    monkeypatch.setattr(live_chat_app, "_faster_whisper_model", None)
    monkeypatch.setattr(live_chat_app, "_elevenlabs_auth_failed", False)
    monkeypatch.setattr(live_chat_app, "last_stt_provider", "")

    text = await live_chat_app.transcribe([np.zeros(1600, dtype=np.int16)])
    await asyncio.sleep(0)

    assert text == "hello vision"
    assert live_chat_app.last_stt_provider == "elevenlabs"
    assert broadcasts[-1]["provider"] == "elevenlabs"
    assert broadcasts[-1]["cascade"] == ["local✗", "elevenlabs"]
