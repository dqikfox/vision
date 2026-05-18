#!/usr/bin/env python3
"""Diagnose and fix ElevenLabs voice integration issues."""

import os
import sys
import traceback

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

print("=" * 70)
print("ELEVENLABS VOICE DIAGNOSTIC")
print("=" * 70)

# Step 1: Check environment
print("\n1. ENVIRONMENT CHECK")
print("-" * 40)
load_dotenv()
api_key = os.environ.get("ELEVENLABS_API_KEY", "")
print(f"ELEVENLABS_API_KEY loaded: {bool(api_key)}")
if api_key:
    print("API key present")
else:
    print("ERROR: No API key found!")
    sys.exit(1)

# Step 2: Test ElevenLabs connection
print("\n2. ELEVENLABS API CONNECTION")
print("-" * 40)
try:
    client = ElevenLabs(api_key=api_key)

    # Test voices endpoint
    voices = client.voices.get_all()
    print("✓ Connected successfully")
    print(f"✓ Available voices: {len(voices.voices)}")

    # Check for custom voice
    custom = [v for v in voices.voices if v.voice_id == "0iuMR9ISp6Q7mg6H70yo"]
    if custom:
        print(f"✓ Custom voice 'Hitch' found: {custom[0].name}")
    else:
        print("⚠ Custom voice 'Hitch' not found in account")

except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)

# Step 3: Test TTS
print("\n3. TEXT-TO-SPEECH TEST")
print("-" * 40)
try:
    test_text = "Vision is online. Voice systems operational."
    print(f"Testing TTS with: '{test_text}'")

    audio = client.text_to_speech.convert(
        text=test_text,
        voice_id="0iuMR9ISp6Q7mg6H70yo",
        model_id="eleven_flash_v2_5",
        voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True),
    )

    # Save to file
    output_file = "vision_online_test.mp3"
    with open(output_file, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    print(f"✓ TTS successful - audio saved to: {output_file}")

except Exception as e:
    print(f"✗ TTS failed: {e}")
    traceback.print_exc()

# Step 4: Check ConvAI Agent
print("\n4. CONVAI AGENT CHECK")
print("-" * 40)
try:
    AGENT_ID = "agent_0701knwqnqy9e1aa3a3drdh30cva"
    agent = client.conversational_ai.agents.get(agent_id=AGENT_ID)
    print(f"✓ Agent found: {agent.name}")
    print(f"✓ Agent ID: {agent.agent_id}")
except Exception as e:
    print(f"✗ Agent check failed: {e}")

# Step 5: Summary
print("\n" + "=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)
print("""
If all checks passed, the issue is likely:

1. VISION NOT RESTARTED - The backend needs restart to pick up the API key
   Fix: Restart python live_chat_app.py

2. VOICE SWITCHER NOT WORKING - The UI might not be sending the right message
   Fix: Check browser console for errors when switching voice providers

3. _elevenlabs_auth_failed FLAG - If auth ever failed, it stays failed until restart
   Fix: Restart the backend

RECOMMENDED ACTIONS:
1. Stop Vision (Ctrl+C)
2. Verify .env has ELEVENLABS_API_KEY
3. Restart: python live_chat_app.py
4. Check health: http://localhost:8765/api/health
5. Try voice switcher in UI
""")

print("=" * 70)
