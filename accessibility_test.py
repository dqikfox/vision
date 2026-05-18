"""Test script to verify accessibility features for disabled users."""

import asyncio
import json

import requests
import websockets


def test_http_endpoints():
    """Test HTTP endpoints for accessibility features."""
    print("Testing HTTP endpoints...")

    # Test health endpoint
    try:
        response = requests.get("http://localhost:8765/api/health")
        if response.status_code == 200:
            print("✓ Health endpoint accessible")
        else:
            print("✗ Health endpoint failed")
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")

    # Test models endpoint
    try:
        response = requests.get("http://localhost:8765/api/models")
        if response.status_code == 200:
            print("✓ Models endpoint accessible")
        else:
            print("✗ Models endpoint failed")
    except Exception as e:
        print(f"✗ Models endpoint error: {e}")


async def test_websocket_connection():
    """Test WebSocket connection for real-time features."""
    print("\nTesting WebSocket connection...")

    uri = "ws://localhost:8765/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # Wait for initial message
            response = await websocket.recv()
            print("✓ WebSocket connection established")

            # Test model switching
            switch_message = {"type": "set_model", "provider": "ollama", "model": "cogito:latest"}

            await websocket.send(json.dumps(switch_message))
            print("Sent model switch command")

            # Wait for response
            response = await websocket.recv()
            print("✓ Model switch command processed")

            # Test voice settings
            voice_message = {
                "type": "set_voice_settings",
                "preferred_stt": "auto",
                "preferred_tts": "auto",
                "tts_rate": 175,
                "tts_voice_idx": 0,
            }

            await websocket.send(json.dumps(voice_message))
            print("Sent voice settings command")

            # Wait for response
            response = await websocket.recv()
            print("✓ Voice settings command processed")

    except Exception as e:
        print(f"✗ WebSocket test error: {e}")


def test_voice_settings():
    """Test voice settings functionality."""
    print("\nTesting voice settings...")

    # Test current voice settings
    try:
        response = requests.get("http://localhost:8765/api/health")
        data = response.json()

        # Check if ElevenLabs is available
        if data.get("elevenlabs"):
            print("✓ ElevenLabs integration available")
        else:
            print("⚠ ElevenLabs integration not available")

        # Check if STT is available
        if data.get("browser"):
            print("✓ Browser-based STT available")
        else:
            print("⚠ Browser-based STT not available")

    except Exception as e:
        print(f"✗ Voice settings test error: {e}")


def test_accessibility_features():
    """Test specific accessibility features for disabled users."""
    print("\nTesting accessibility features...")

    # Test screen reader compatibility
    try:
        response = requests.get("http://localhost:8765/api/health")
        data = response.json()

        # Check if OCR is available for visually impaired users
        if data.get("ocr"):
            print("✓ OCR functionality available for visually impaired users")
        else:
            print("⚠ OCR functionality not available")

        # Check if high contrast mode is supported
        if data.get("high_contrast", False):
            print("✓ High contrast mode available")
        else:
            print("○ High contrast mode not enabled (optional)")

        # Check if keyboard navigation is supported
        if data.get("keyboard_nav", False):
            print("✓ Keyboard navigation support confirmed")
        else:
            print("○ Keyboard navigation support not reported")

    except Exception as e:
        print(f"✗ Accessibility features test error: {e}")


def test_customization_options():
    """Test customization options for different disability needs."""
    print("\nTesting customization options...")

    # Test voice rate customization
    try:
        response = requests.get("http://localhost:8765/api/health")
        data = response.json()

        # Check if customizable voice rate is available
        voice_settings = data.get("voice_settings", {})
        if "rate" in voice_settings:
            print("✓ Voice rate customization available")
        else:
            print("○ Voice rate customization not reported")

        # Check if multiple voice options are available
        if data.get("voices", 0) > 1:
            print("✓ Multiple voice options available")
        else:
            print("○ Limited voice options available")

    except Exception as e:
        print(f"✗ Customization options test error: {e}")


def test_accessibility_api_endpoints():
    """Test the new accessibility API endpoints."""
    print("\nTesting accessibility API endpoints...")

    # Test getting accessibility settings
    try:
        response = requests.get("http://localhost:8765/api/accessibility/settings")
        if response.status_code == 200:
            data = response.json()
            print("✓ Accessibility settings endpoint accessible")

            # Check if all expected settings are present
            expected_keys = [
                "high_contrast",
                "keyboard_navigation",
                "voice_rate",
                "voice_pitch",
                "voice_volume",
                "magnification",
            ]
            missing_keys = [key for key in expected_keys if key not in data]
            if not missing_keys:
                print("✓ All accessibility settings available")
            else:
                print(f"○ Some accessibility settings missing: {missing_keys}")
        else:
            print("✗ Accessibility settings endpoint failed")
    except Exception as e:
        print(f"✗ Accessibility settings endpoint error: {e}")

    # Test updating accessibility settings
    try:
        update_data = {"high_contrast": True, "voice_rate": 200}
        response = requests.post("http://localhost:8765/api/accessibility/settings", json=update_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "updated":
                print("✓ Accessibility settings update successful")
            else:
                print("○ Accessibility settings update returned unexpected status")
        else:
            print("✗ Accessibility settings update failed")
    except Exception as e:
        print(f"✗ Accessibility settings update error: {e}")


def main():
    """Run all accessibility tests."""
    print("=== Vision Accessibility Test Suite ===\n")

    test_http_endpoints()
    test_voice_settings()
    test_accessibility_features()
    test_customization_options()
    test_accessibility_api_endpoints()

    # Run async tests
    asyncio.run(test_websocket_connection())

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
