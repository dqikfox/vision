#!/usr/bin/env python3
"""Test ElevenLabs ConvAI agent connection and voice training options."""

import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    print("ERROR: ELEVENLABS_API_KEY not found")
    exit(1)

client = ElevenLabs(api_key=api_key)
AGENT_ID = "agent_0701knwqnqy9e1aa3a3drdh30cva"

print("=" * 60)
print("ELEVENLABS AGENT TEST")
print("=" * 60)

# Get agent details
print("\n=== Agent Details ===")
try:
    agent = client.conversational_ai.agents.get(agent_id=AGENT_ID)
    print(f"Name: {agent.name}")
    print(f"ID: {agent.agent_id}")
    print(f"Version: {agent.version}")
    print(f"Created: {agent.created_at}")
except Exception as e:
    print(f"Error: {e}")

# Get agent settings
print("\n=== Agent Settings ===")
try:
    settings = client.conversational_ai.settings.get()
    print("Settings retrieved successfully")
    if hasattr(settings, "language"):
        print(f"Language: {settings.language}")
    if hasattr(settings, "voice_id"):
        print(f"Voice ID: {settings.voice_id}")
except Exception as e:
    print(f"Error: {e}")

# List all voices (for training reference)
print("\n=== Available Voices ===")
try:
    voices = client.voices.get_all()
    print(f"Total voices: {len(voices.voices)}")

    # Show custom/cloned voices
    custom = [v for v in voices.voices if v.category == "cloned"]
    print(f"\nCustom/cloned voices: {len(custom)}")
    for v in custom:
        print(f"  - {v.name} ({v.voice_id})")

    # Show premium voices
    premium = [v for v in voices.voices if v.category == "premade"][:5]
    print("\nSample premium voices:")
    for v in premium:
        print(f"  - {v.name} ({v.voice_id})")
except Exception as e:
    print(f"Error: {e}")

# Voice training info
print("\n=== Voice Training Options ===")
print("ElevenLabs offers several voice training methods:")
print("1. Voice Cloning - Upload 1-5 minutes of audio to clone a voice")
print("2. Voice Design - Create a voice from text description")
print("3. Professional Voice Cloning - Higher quality with 30+ minutes")
print("4. Voice Library - Use community-created voices")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
