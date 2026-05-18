#!/usr/bin/env python3
"""Comprehensive Voice System Test for Vision
Tests ElevenLabs integration, voice switching, and TTS functionality.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# Add vision to path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

print("=" * 70)
print("VISION VOICE SYSTEM TEST")
print("=" * 70)

# Test 1: Environment
print("\n[1/6] Environment Check")
print("-" * 40)
api_key = os.environ.get("ELEVENLABS_API_KEY")
if api_key:
    print("✓ ELEVENLABS_API_KEY loaded")
else:
    print("✗ ELEVENLABS_API_KEY not found in environment")
    sys.exit(1)

# Test 2: Import live_chat_app
print("\n[2/6] Import live_chat_app")
print("-" * 40)
try:
    from live_chat_app import TTS_MODEL, VOICE_ID, _elevenlabs_voice_available, _normalize_preferred_tts, preferred_tts

    print("✓ Module imported successfully")
    print(f"  - VOICE_ID: {VOICE_ID}")
    print(f"  - TTS_MODEL: {TTS_MODEL}")
    print(f"  - Current preferred_tts: {preferred_tts}")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 3: ElevenLabs Availability
print("\n[3/6] ElevenLabs Availability")
print("-" * 40)
try:
    available = _elevenlabs_voice_available()
    print(f"✓ ElevenLabs voice available: {available}")
    if not available:
        print("  Note: If API key is correct, restart Vision to apply changes")
except Exception as e:
    print(f"✗ Check failed: {e}")

# Test 4: Voice Normalization
print("\n[4/6] Voice Provider Normalization")
print("-" * 40)
test_cases = ["auto", "elevenlabs", "local", "invalid", "ELEVENLABS"]
for case in test_cases:
    result = _normalize_preferred_tts(case)
    status = "✓" if result in ["auto", "elevenlabs", "local"] else "✗"
    print(f"  {status} '{case}' -> '{result}'")

# Test 5: ElevenLabs API Connection
print("\n[5/6] ElevenLabs API Connection")
print("-" * 40)
try:
    client = ElevenLabs(api_key=api_key)

    # Test voices
    voices = client.voices.get_all()
    print("✓ Connected to ElevenLabs API")
    print(f"  - Total voices: {len(voices.voices)}")

    # Check if Hitch voice exists
    hitch = [v for v in voices.voices if v.voice_id == VOICE_ID]
    if hitch:
        print(f"✓ Hitch voice found: {hitch[0].name}")
    else:
        print(f"⚠ Hitch voice ({VOICE_ID}) not in account")
        print("  Using default voice instead")

except Exception as e:
    print(f"✗ API connection failed: {e}")

# Test 6: TTS Test
print("\n[6/6] Text-to-Speech Test")
print("-" * 40)
try:
    client = ElevenLabs(api_key=api_key)

    test_text = "Vision voice systems operational. ElevenLabs integration active."
    print(f"  Testing TTS with: '{test_text[:50]}...'")

    audio = client.text_to_speech.convert(
        text=test_text,
        voice_id=VOICE_ID,
        model_id=TTS_MODEL,
        voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True),
    )

    # Save test audio
    output_file = "voice_test_output.mp3"
    with open(output_file, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    print("✓ TTS successful!")
    print(f"  - Audio saved to: {output_file}")
    print(f"  - Voice: Hitch ({VOICE_ID})")
    print(f"  - Model: {TTS_MODEL}")

except Exception as e:
    print(f"✗ TTS failed: {e}")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("""
If all tests passed, the voice system is working correctly.

To use ElevenLabs in Vision:
1. Make sure ELEVENLABS_API_KEY is set in .env file
2. Restart Vision: python live_chat_app.py
3. Open the UI and go to Settings (top panel)
4. Under "VOICE OUTPUT", select "ElevenLabs"
5. The system should now use Hitch voice for TTS

If voice switcher still doesn't work:
- Check browser console for JavaScript errors
- Verify WebSocket connection is active
- Try refreshing the page after changing settings
""")

print("=" * 70)
