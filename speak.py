"""
speak.py — ElevenLabs real-time WebSocket TTS for Copilot dialogue.

Uses WebSocket streaming + PCM output for low-latency playback.
Audio starts playing ~300ms after the first text is sent.

Usage: python speak.py "Your text here"
"""

import asyncio
import base64
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import sounddevice as sd
import websockets

VOICE_ID    = "0iuMR9ISp6Q7mg6H70yo"   # Hitch
MODEL_ID    = "eleven_flash_v2_5"        # Lowest-latency ElevenLabs model
SAMPLE_RATE = 16_000
API_KEY     = os.environ.get("ELEVENLABS_API_KEY", "")


async def stream_tts(text: str) -> None:
    uri = (
        f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input"
        f"?model_id={MODEL_ID}&output_format=pcm_{SAMPLE_RATE}"
    )

    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        async with websockets.connect(uri, additional_headers={"xi-api-key": API_KEY}) as ws:
            # Initialise connection with voice settings
            await ws.send(json.dumps({
                "text": " ",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "use_speaker_boost": False,
                },
                "generation_config": {
                    "chunk_length_schedule": [50, 120, 160, 250],
                },
            }))

            # Send text + flush to start generating immediately
            await ws.send(json.dumps({"text": text, "flush": True}))

            # Close signal
            await ws.send(json.dumps({"text": ""}))

            # Play audio chunks as they arrive
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("audio"):
                    pcm = base64.b64decode(msg["audio"])
                    samples = np.frombuffer(pcm, dtype=np.int16)
                    stream.write(samples)
                if msg.get("isFinal"):
                    break


def speak(text: str) -> None:
    asyncio.run(stream_tts(text))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python speak.py \"text to speak\"")
        sys.exit(1)
    speak(" ".join(sys.argv[1:]))
