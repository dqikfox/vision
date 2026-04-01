"""
voice_toggle.py — Two-way voice companion for Copilot chat.

Hotkeys:
  F9  — hold to record your voice → transcribes via ElevenLabs STT
          → copies result to clipboard, prints to console
  F10 — toggle TTS on/off (Copilot spoken responses)
  F11 — re-speak the last Copilot TTS line
  ESC — quit

Beep feedback (works even when TTS is off):
  F9 press   → low beep  (recording started)
  F9 release → high beep (recording stopped, transcribing)
  F10 ON     → two short high beeps
  F10 OFF    → one long low beep
  Transcribed → three quick beeps

Usage:
  set ELEVENLABS_API_KEY=sk_...
  python voice_toggle.py
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import warnings

warnings.filterwarnings("ignore")

import keyboard
import numpy as np
import pyperclip
import sounddevice as sd
import websockets
import winsound
from scipy.io import wavfile

API_KEY     = os.environ.get("ELEVENLABS_API_KEY", "")
VOICE_ID    = "0iuMR9ISp6Q7mg6H70yo"  # Hitch
MODEL_ID    = "eleven_flash_v2_5"       # Fastest ElevenLabs model
SAMPLE_RATE = 16_000
DEBOUNCE_S  = 0.4# minimum seconds between F10 toggles

tts_enabled    = True
recording      = False
audio_chunks   = []
last_tts_text  = ""
last_f10_time  = 0.0
record_lock    = threading.Lock()
f10_lock       = threading.Lock()


# ── beep feedback ─────────────────────────────────────────────────────────────

def beep(freq: int, ms: int):
    """Blocking beep — call from a thread if you need non-blocking."""
    winsound.Beep(freq, ms)


def _async_beep(freq: int, ms: int):
    threading.Thread(target=winsound.Beep, args=(freq, ms), daemon=True).start()


def beep_record_start():   _async_beep(400, 120)
def beep_record_stop():    _async_beep(880, 120)

def beep_transcribed():
    def _seq():
        for _ in range(3):
            winsound.Beep(1000, 80)
            time.sleep(0.12)
    threading.Thread(target=_seq, daemon=True).start()

def beep_tts_on():
    def _seq():
        winsound.Beep(900, 80)
        time.sleep(0.1)
        winsound.Beep(900, 80)
    threading.Thread(target=_seq, daemon=True).start()

def beep_tts_off():        _async_beep(300, 350)
def beep_replay():         _async_beep(660, 100)


# ── TTS (ElevenLabs) ──────────────────────────────────────────────────────────

def speak(text: str):
    global last_tts_text
    last_tts_text = text
    if not tts_enabled:
        return
    threading.Thread(target=_speak_blocking, args=(text,), daemon=True).start()


async def _stream_tts(text: str) -> None:
    uri = (
        f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input"
        f"?model_id={MODEL_ID}&output_format=pcm_{SAMPLE_RATE}"
    )
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({
                "text": " ",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "use_speaker_boost": False},
                "generation_config": {"chunk_length_schedule": [50, 120, 160, 250]},
                "xi_api_key": API_KEY,
            }))
            await ws.send(json.dumps({"text": text, "flush": True}))
            await ws.send(json.dumps({"text": ""}))
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("audio"):
                    samples = np.frombuffer(base64.b64decode(msg["audio"]), dtype=np.int16)
                    stream.write(samples)
                if msg.get("isFinal"):
                    break


def _speak_blocking(text: str):
    try:
        asyncio.run(_stream_tts(text))
    except Exception as e:
        log(f"TTS error: {e}")


# ── STT (ElevenLabs) ──────────────────────────────────────────────────────────

def transcribe_wav(wav_path: str) -> str:
    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=API_KEY)
        with open(wav_path, "rb") as f:
            result = client.speech_to_text.convert(
                file=f,
                model_id="scribe_v1",
                tag_audio_events=False,
                timestamps_granularity="none",
            )
        return result.text.strip()
    except Exception as e:
        log(f"STT error: {e}")
        return ""


# ── recording ─────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[voice] {msg}", flush=True)


def start_recording():
    global recording, audio_chunks
    with record_lock:
        if recording:
            return
        recording = True
        audio_chunks = []
    beep_record_start()
    log("🎙  Recording…")


def stop_recording_and_transcribe():
    global recording, audio_chunks
    with record_lock:
        if not recording:
            return
        recording = False
        chunks = list(audio_chunks)
        audio_chunks = []

    beep_record_stop()

    if not chunks:
        log("No audio captured.")
        return

    audio_np = np.concatenate(chunks, axis=0)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    wavfile.write(wav_path, SAMPLE_RATE, audio_np)

    log("⏳  Transcribing…")
    text = transcribe_wav(wav_path)
    os.unlink(wav_path)

    if text:
        pyperclip.copy(text)
        threading.Thread(target=beep_transcribed, daemon=True).start()
        log(f"📋  Transcribed + pasting:\n    → {text}")
        time.sleep(0.15)  # let beep thread start before we steal focus
        keyboard.press_and_release("ctrl+v")
        time.sleep(0.05)
        keyboard.press_and_release("enter")
    else:
        log("Could not transcribe audio.")


def audio_callback(indata, frames, time_info, status):
    if recording:
        audio_chunks.append(indata.copy())


# ── hotkeys ───────────────────────────────────────────────────────────────────

def on_f9_press(e):
    start_recording()


def on_f9_release(e):
    threading.Thread(target=stop_recording_and_transcribe, daemon=True).start()


def on_f10(e):
    global tts_enabled, last_f10_time
    with f10_lock:
        now = time.monotonic()
        if now - last_f10_time < DEBOUNCE_S:
            return          # ignore key-repeat
        last_f10_time = now
        tts_enabled = not tts_enabled

    if tts_enabled:
        threading.Thread(target=beep_tts_on, daemon=True).start()
        log("TTS  ON  ✅")
    else:
        threading.Thread(target=beep_tts_off, daemon=True).start()
        log("TTS  OFF 🔇")


def on_f11(e):
    if last_tts_text:
        beep_replay()
        log("🔁  Re-speaking…")
        speak(last_tts_text)
    else:
        log("Nothing to re-speak yet.")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if not API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    print("━" * 54)
    print("  Copilot Voice Toggle")
    print("  F9  hold  → record mic  (beep start / beep stop)")
    print("  F10       → toggle TTS  (2 beeps=ON / 1 low=OFF)")
    print("  F11       → replay last Copilot line")
    print("  ESC       → quit")
    print("━" * 54)

    keyboard.on_press_key("f9",  on_f9_press,  suppress=False)
    keyboard.on_release_key("f9", on_f9_release)
    keyboard.on_press_key("f10", on_f10,       suppress=False)
    keyboard.on_press_key("f11", on_f11,       suppress=False)

    speak("Voice toggle ready. Hold F9 to speak. F10 mutes me. F11 replays.")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        callback=audio_callback,
    ):
        keyboard.wait("esc")

    log("Exiting.")


if __name__ == "__main__":
    main()
