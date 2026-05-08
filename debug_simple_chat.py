import asyncio
import json

import websockets

WS = "ws://localhost:8765/ws"

async def test_simple_chat():
    async with websockets.connect(WS, open_timeout=5) as ws:
        # Receive initial message
        init_msg = await ws.recv()
        print(f"Initial message: {init_msg}")

        # Send a simple chat message
        test_msg = {
            "type": "input",
            "text": "Hello, how are you?",
        }
        await ws.send(json.dumps(test_msg))
        print("Sent test message")

        # Wait for response
        for i in range(20):  # Wait for up to 20 messages
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(raw)
                print(f"Received message {i+1}: {msg}")

                if msg.get("type") == "transcript" and msg.get("role") == "assistant":
                    text = msg.get("text", "")
                    print(f"Assistant transcript text: {text}")
                    if text and not text.startswith("🟢 Vision is online"):
                        print("SUCCESS: Received a response from the assistant")
                        return
                elif msg.get("type") == "state":
                    print(f"State: {msg.get('state')}")
                elif msg.get("type") == "stream_finalize":
                    text = msg.get("text", "")
                    print(f"Stream finalize text: {text}")
                    if text and not text.startswith("🟢 Vision is online"):
                        print("SUCCESS: Received a response from stream_finalize")
                        return
            except TimeoutError:
                print("Timeout waiting for message")
                break

        print("FAILED: Did not receive expected response")

if __name__ == "__main__":
    asyncio.run(test_simple_chat())
