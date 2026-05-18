"""
Quick diagnostic: Test if voice transcription is working
"""
import asyncio
import json

import websockets


async def test_voice():
    uri = "ws://localhost:8765/ws"

    print("Connecting to Vision backend...")
    async with websockets.connect(uri) as ws:
        print("✅ Connected!")

        # Listen for messages
        print("\n📡 Listening for WebSocket messages...")
        print("👉 Now click the microphone button in the web UI and speak!")
        print("   (Or say 'hey vision' if wake word is enabled)")
        print("\nWaiting for messages...\n")

        try:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                msg_type = data.get("type", "unknown")

                # Show relevant voice messages
                if msg_type in ["state", "partial_transcript", "transcript", "volume"]:
                    if msg_type == "state":
                        state = data.get("state")
                        print(f"🔄 STATE: {state}")
                    elif msg_type == "partial_transcript":
                        text = data.get("text", "")
                        if text:
                            print(f"📝 PARTIAL: {text}")
                    elif msg_type == "transcript":
                        text = data.get("text", "")
                        print(f"✅ TRANSCRIPT: {text}")
                    elif msg_type == "volume":
                        level = data.get("level", 0)
                        if level > 0.05:  # Only show if significant
                            bars = "█" * int(level * 20)
                            print(f"🎤 VOLUME: {bars} ({level:.2f})")
                else:
                    # Show other message types for debugging
                    print(f"📨 {msg_type}: {data}")

        except KeyboardInterrupt:
            print("\n\n👋 Disconnected")

if __name__ == "__main__":
    asyncio.run(test_voice())
