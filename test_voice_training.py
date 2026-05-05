#!/usr/bin/env python3
"""Voice training and testing script for ElevenLabs."""

import os

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

load_dotenv()

api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    print("ERROR: ELEVENLABS_API_KEY not found")
    exit(1)

client = ElevenLabs(api_key=api_key)


def test_tts_voice(voice_id, voice_name, text="Hello! This is a test of the Vision voice system."):
    """Test TTS with a specific voice."""
    print(f"\nTesting voice: {voice_name} ({voice_id[:8]}...)")
    try:
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2_5",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True),
        )

        # Save audio file
        filename = f"test_voice_{voice_name.replace(' ', '_').replace('-', '_')[:20]}.mp3"
        with open(filename, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        print(f"  ✓ Audio saved to: {filename}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def list_voice_training_options():
    """Show voice training options."""
    print("\n" + "=" * 60)
    print("VOICE TRAINING OPTIONS")
    print("=" * 60)

    print("\n1. INSTANT VOICE CLONING")
    print("   - Upload 1-5 minutes of clear audio")
    print("   - Quick results (minutes)")
    print("   - Good quality for most use cases")

    print("\n2. PROFESSIONAL VOICE CLONING")
    print("   - Upload 30+ minutes of high-quality audio")
    print("   - Best results for production")
    print("   - Takes longer to process")

    print("\n3. VOICE DESIGN (Text-to-Voice)")
    print("   - Describe the voice you want")
    print("   - AI generates a unique voice")
    print("   - No audio samples needed")

    print("\n4. VOICE LIBRARY")
    print("   - Browse community-created voices")
    print("   - Filter by accent, age, gender, use case")
    print("   - Add to your collection")


def clone_voice_sample():
    """Demonstrate voice cloning process."""
    print("\n" + "=" * 60)
    print("VOICE CLONING DEMO")
    print("=" * 60)

    print("\nTo clone a voice, you would:")
    print("1. Prepare audio files (MP3/WAV, 1-5 minutes)")
    print("2. Use: client.voices.add(name='My Voice', files=[open('sample.mp3', 'rb')])")
    print("3. Wait for processing (usually 1-5 minutes)")
    print("4. Get voice_id to use in TTS")

    # Show example code
    print("\nExample code:")
    print("""
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key="your-api-key")

    # Clone voice from audio files
    voice = client.voices.add(
        name="My Custom Voice",
        description="A cloned voice for Vision",
        files=[
            open("sample1.mp3", "rb"),
            open("sample2.mp3", "rb")
        ]
    )

    print(f"Voice ID: {voice.voice_id}")
    """)


def main():
    print("=" * 60)
    print("ELEVENLABS VOICE TRAINING & TESTING")
    print("=" * 60)

    # Test different voices
    print("\n" + "=" * 60)
    print("TESTING TTS WITH DIFFERENT VOICES")
    print("=" * 60)

    test_voices = [
        ("0iuMR9ISp6Q7mg6H70yo", "Hitch"),  # Default Vision voice
        ("CwhRBWXzGAHq8TQ4Fs17", "Roger"),
        ("EXAVITQu4vr4xnSDxMaL", "Sarah"),
    ]

    for voice_id, voice_name in test_voices:
        test_tts_voice(voice_id, voice_name)

    # Show training options
    list_voice_training_options()

    # Show cloning demo
    clone_voice_sample()

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
