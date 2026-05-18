#!/usr/bin/env python3
"""Pytest checks for ElevenLabs ConvAI agent access and voice availability."""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

AGENT_ID = "agent_0701knwqnqy9e1aa3a3drdh30cva"


@pytest.fixture
def api_key() -> str:
    value = os.environ.get("ELEVENLABS_API_KEY", "")
    if not value:
        pytest.skip("ELEVENLABS_API_KEY not configured")
    return value


@pytest.fixture
def client(api_key: str) -> ElevenLabs:
    return ElevenLabs(api_key=api_key)


def test_agent_details(client: ElevenLabs) -> None:
    agent = client.conversational_ai.agents.get(agent_id=AGENT_ID)
    assert agent.agent_id == AGENT_ID
    assert bool(agent.name)


def test_agent_settings(client: ElevenLabs) -> None:
    settings = client.conversational_ai.settings.get()
    assert settings is not None


def test_voices_listing(client: ElevenLabs) -> None:
    voices = client.voices.get_all()
    assert len(voices.voices) >= 0
