import asyncio
import json
import websockets

WS = "ws://localhost:8765/ws"

async def test_ollama():
    async with websockets.connect(WS, open_timeout=5) as ws:
        # Receive initial message
        init_msg = await ws.recv()
        print(f"Initial message: {init_msg}")

        # Parse initial message to see current mode and provider
        init_data = json.loads(init_msg)
        print(f"Current mode: {init_data.get('mode', 'unknown')}")
        print(f"Current provider: {init_data.get('provider', 'unknown')}")
        print(f"Current model: {init_data.get('model', 'unknown')}")

        # Switch to Ollama provider
        await ws.send(json.dumps({"type": "set_model", "provider": "ollama", "model": "qwen2.5-coder:1.5b-base"}))
        print("Sent set_model command to Ollama")

        # Wait a bit
        await asyncio.sleep(1)

        # Explicitly set mode to chat
        await ws.send(json.dumps({"type": "set_mode", "mode": "chat"}))
        print("Sent set_mode command")

        # Wait a bit
        await asyncio.sleep(1)

        # Send test message
        test_msg = {
            "type": "input",
            "text": "Reply with exactly this text and nothing else: VISION_TEST_OK",
        }
        await ws.send(json.dumps(test_msg))
        print("Sent test message")

        # Wait for response
        for i in range(30):  # Wait for up to 30 messages
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(raw)
                print(f"Received message {i+1}: {msg}")

                if msg.get("type") == "transcript" and msg.get("role") == "assistant":
                    text = msg.get("text", "")
                    print(f"Assistant transcript text: {text}")
                    if "VISION_TEST_OK" in text:
                        print("SUCCESS: Found VISION_TEST_OK in response")
                        return
                    else:
                        print("Found assistant transcript but doesn't contain VISION_TEST_OK")
                elif msg.get("type") == "state":
                    print(f"State: {msg.get('state')}")
                elif msg.get("type") == "stream_finalize":
                    text = msg.get("text", "")
                    print(f"Stream finalize text: {text}")
                    if "VISION_TEST_OK" in text:
                        print("SUCCESS: Found VISION_TEST_OK in stream_finalize")
                        return
                    else:
                        print("Found stream_finalize but doesn't contain VISION_TEST_OK")
            except asyncio.TimeoutError:
                print("Timeout waiting for message")
                break

        print("FAILED: Did not receive expected response")

if __name__ == "__main__":
    asyncio.run(test_ollama())
