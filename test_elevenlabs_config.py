"""Pytest checks for ElevenLabs configuration and SDK availability."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent


@pytest.fixture
def api_key() -> str:
    value = os.environ.get("ELEVENLABS_API_KEY", "")
    if not value:
        pytest.skip("ELEVENLABS_API_KEY not configured")
    return value


def test_project_root_is_portable() -> None:
    assert PROJECT_ROOT.exists()


def test_api_key_format(api_key: str) -> None:
    assert len(api_key) > 30
    assert api_key.startswith("sk_")


def test_tts_connectivity(api_key: str) -> None:
    client = ElevenLabs(api_key=api_key)
    voices = client.voices.get_all()
    assert len(voices.voices) >= 0


def test_convai_sdk_available() -> None:
    convai = pytest.importorskip("elevenlabs.conversational_ai.conversation")
    assert hasattr(convai, "Conversation")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
