import asyncio
import json

import websockets

WS = "ws://localhost:8765/ws"

async def test_chat():
    async with websockets.connect(WS, open_timeout=5) as ws:
        # Receive initial message
        init_msg = await ws.recv()
        print(f"Initial message: {init_msg}")

        # Set mode to chat
        await ws.send(json.dumps({"type": "set_mode", "mode": "chat"}))

        # Send test message
        await ws.send(
            json.dumps(
                {
                    "type": "input",
                    "text": "Reply with exactly this text and nothing else: VISION_TEST_OK",
                }
            )
        )

        # Wait for response
        for i in range(10):  # Wait for up to 10 messages
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(raw)
                print(f"Received message: {msg}")

                if msg.get("type") in {"transcript", "stream_finalize"}:
                    text = msg.get("text", "")
                    if text:
                        print(f"Transcript text: {text}")
                        if "VISION_TEST_OK" in text:
                            print("SUCCESS: Found VISION_TEST_OK in response")
                            return
                        else:
                            print("Found transcript but doesn't contain VISION_TEST_OK")
            except TimeoutError:
                print("Timeout waiting for message")
                break

        print("FAILED: Did not receive expected response")

if __name__ == "__main__":
    asyncio.run(test_chat())
