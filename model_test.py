"""Test model switching functionality."""

import asyncio
import json

import websockets


async def test_model_switching():
    """Test switching between different providers and models."""
    uri = "ws://localhost:8765/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # Wait for initial message
            response = await websocket.recv()
            print(f"Connected: {response}")

            # Test switching to different providers
            test_cases = [
                {"provider": "openai", "model": "gpt-4o"},
                {"provider": "github", "model": "gpt-4o"},
                {"provider": "ollama", "model": "cogito:latest"},
            ]

            for test_case in test_cases:
                print(f"\nTesting switch to {test_case['provider']}/{test_case['model']}")

                # Switch model
                switch_message = {"type": "set_model", "provider": test_case["provider"], "model": test_case["model"]}

                await websocket.send(json.dumps(switch_message))
                print(f"Sent model switch command to {test_case['provider']}/{test_case['model']}")

                # Wait for responses
                for i in range(3):  # Wait for up to 3 messages
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print(f"Response: {response}")

                        # Check if this is the model_changed message
                        data = json.loads(response)
                        if data.get("type") == "model_changed":
                            if (
                                data.get("provider") == test_case["provider"]
                                and data.get("model") == test_case["model"]
                            ):
                                print(f"✓ Successfully switched to {test_case['provider']}/{test_case['model']}")
                                break
                            else:
                                print("⚠ Model changed but not to expected provider/model")
                    except TimeoutError:
                        print("Timeout waiting for response")
                        break

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_model_switching())
