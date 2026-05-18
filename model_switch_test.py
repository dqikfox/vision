"""Simple test script to verify model switching functionality."""

import asyncio
import json

import websockets


async def test_model_switch():
    uri = "ws://localhost:8765/ws"

    try:
        async with websockets.connect(uri) as websocket:
            # Wait for initial message
            response = await websocket.recv()
            print(f"Connected: {response}")

            # Switch to OpenAI GPT-4o
            switch_message = {"type": "set_model", "provider": "openai", "model": "gpt-4o"}

            await websocket.send(json.dumps(switch_message))
            print("Sent model switch command to OpenAI GPT-4o")

            # Wait for response
            response = await websocket.recv()
            print(f"Response: {response}")

            # Switch back to Ollama
            switch_message = {"type": "set_model", "provider": "ollama", "model": "cogito:latest"}

            await websocket.send(json.dumps(switch_message))
            print("Sent model switch command to Ollama cogito:latest")

            # Wait for response
            response = await websocket.recv()
            print(f"Response: {response}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_model_switch())
