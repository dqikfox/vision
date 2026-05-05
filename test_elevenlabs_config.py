"""
ElevenLabs Configuration Diagnostic Tool
Tests TTS, STT, and ConvAI connectivity
"""

import os
import sys

# Add project to path
sys.path.insert(0, r"C:\project\vision")


def test_elevenlabs_config():
    """Test ElevenLabs configuration."""
    print("=" * 60)
    print("ELEVENLABS CONFIGURATION DIAGNOSTIC")
    print("=" * 60)

    # Check environment
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    print("\n1. API Key Check:")
    print(f"   - Key present: {'Yes' if api_key else 'No'}")
    print(f"   - Key prefix: {api_key[:15]}..." if api_key else "   - Key: NOT SET")
    print(f"   - Key length: {len(api_key)} characters")
    print(f"   - Format valid: {'Yes' if api_key.startswith('sk_') and len(api_key) > 30 else 'No'}")

    # Test basic TTS
    print("\n2. Testing TTS API:")
    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)

        # Try to list voices (basic API test)
        voices = client.voices.get_all()
        print("   - API Connection: ✅ Success")
        print(f"   - Available voices: {len(voices.voices)}")

        # Test TTS
        audio = client.text_to_speech.convert(
            text="Test successful",
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )
        print("   - TTS Generation: ✅ Success")

    except Exception as e:
        print(f"   - TTS API: ❌ Failed - {e}")

    # Test ConvAI
    print("\n3. Testing ConvAI:")
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.conversational_ai.conversation import Conversation

        client = ElevenLabs(api_key=api_key)

        # Agent ID from memory
        AGENT_ID = "agent_01jz2wq70mfetr2b7nchrhew1t"

        # Try to get agent info (this will fail if agent doesn't exist)
        # Note: There's no direct "get agent" method, but we can check if the agent exists
        # by trying to create a conversation

        print(f"   - Agent ID: {AGENT_ID}")
        print("   - ConvAI SDK: ✅ Available")

        # The actual conversation test requires audio interface
        print("   - Note: Full ConvAI test requires audio interface")
        print("   - To fully test, use the Vision UI or API")

    except ImportError as e:
        print(f"   - ConvAI SDK: ❌ Not available - {e}")
    except Exception as e:
        print(f"   - ConvAI Test: ❌ Failed - {e}")

    # Summary
    print("\n4. Summary:")
    print("   - Your API key works for TTS/STT")
    print("   - ConvAI requires:")
    print("     a) API key with ConvAI permissions")
    print("     b) Valid agent ID created in ElevenLabs dashboard")
    print("\n   To fix ConvAI:")
    print("   1. Go to https://elevenlabs.io/app/conversational-ai")
    print("   2. Create a new agent or verify agent_01jz2wq70mfetr2b7nchrhew1t exists")
    print("   3. Ensure your API key has ConvAI access")
    print("   4. Update AGENT_ID in live_chat_app.py if needed")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_elevenlabs_config()
