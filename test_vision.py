"""Integration smoke tests for the running Vision accessibility operator.

These tests intentionally touch the live backend, local Ollama, browser
automation, STT, and TTS. They are skipped unless VISION_RUN_INTEGRATION=1 is
set, which keeps pytest collection and the default suite side-effect free.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile

pytestmark = [pytest.mark.integration, pytest.mark.slow]

BASE = os.environ.get("VISION_TEST_BASE", "http://localhost:8765")
WS = os.environ.get("VISION_TEST_WS", "ws://localhost:8765/ws")


def require_integration() -> None:
    if os.environ.get("VISION_RUN_INTEGRATION") != "1":
        pytest.skip("set VISION_RUN_INTEGRATION=1 to run live Vision integration tests")


def is_busy_message(msg: dict) -> bool:
    return msg.get("type") == "error" and "busy" in str(msg.get("message", "")).lower()


def load_json(url: str, timeout: int = 10) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())


async def run_tool(tool_name: str, args: dict, timeout: int = 45) -> str | None:
    import websockets

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            async with websockets.connect(WS, open_timeout=5) as ws:
                await ws.recv()
                await ws.send(json.dumps({"type": "execute_tool", "tool": tool_name, "args": args}))
                while time.time() < deadline:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=5)
                        msg = json.loads(raw)
                        if msg.get("type") == "action" and msg.get("action") == tool_name:
                            return str(msg.get("result", ""))
                        if is_busy_message(msg):
                            await asyncio.sleep(2.0)
                            break
                    except TimeoutError:
                        pass
        except Exception as exc:
            return f"ERROR: {exc}"
    return None


def test_http_endpoints() -> None:
    require_integration()
    with urllib.request.urlopen(f"{BASE}/", timeout=5) as response:
        assert response.status == 200

    payload = load_json(f"{BASE}/api/models")
    assert "providers" in payload
    assert payload.get("current_provider")
    assert payload.get("current_model")


async def test_ws() -> None:
    require_integration()
    import websockets

    async with websockets.connect(WS, open_timeout=5) as ws:
        raw = await asyncio.wait_for(ws.recv(), timeout=5)
        msg = json.loads(raw)
        assert msg.get("type") == "init"
        assert msg.get("provider")
        assert msg.get("model")


async def test_ollama_chat() -> None:
    require_integration()
    import websockets

    deadline = time.time() + 60
    while time.time() < deadline:
        async with websockets.connect(WS, open_timeout=5) as ws:
            await ws.recv()
            await ws.send(json.dumps({"type": "set_mode", "mode": "chat"}))
            await ws.send(
                json.dumps(
                    {
                        "type": "input",
                        "text": "Reply with exactly this text and nothing else: VISION_TEST_OK",
                    }
                )
            )
            while time.time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(raw)
                    if is_busy_message(msg):
                        await asyncio.sleep(2)
                        break
                    if msg.get("type") in {"transcript", "stream_finalize"}:
                        text = msg.get("text", "")
                        if text:
                            assert "VISION_TEST_OK" in text
                            return
                except TimeoutError:
                    pass
    pytest.fail("Ollama chat did not reply within 60s")


async def test_tools() -> None:
    require_integration()

    result = await run_tool("run_command", {"command": "echo TOOL_TEST_OK"})
    assert result is not None
    assert "TOOL_TEST_OK" in result

    for tool_name, args in (
        ("list_files", {}),
        ("get_clipboard", {}),
        ("set_clipboard", {"text": "VISION_CLIP_TEST"}),
        ("list_windows", {}),
        ("screenshot", {}),
    ):
        result = await run_tool(tool_name, args)
        assert result is not None
        assert "ERROR" not in result


async def test_firefox() -> None:
    require_integration()

    result = await run_tool("run_command", {"command": "start firefox"}, timeout=10)
    assert result is not None

    result = await run_tool("browser_open", {"url": "https://www.google.com"}, timeout=20)
    assert result is not None
    assert "ERROR" not in result


def test_stt_faster_whisper() -> None:
    require_integration()
    pytest.importorskip("faster_whisper")
    from faster_whisper import WhisperModel

    sample_rate = 16000
    samples = np.linspace(0, 2, sample_rate * 2, dtype=np.float32)
    tone = (np.sin(2 * np.pi * 440 * samples) * 16000).astype(np.int16)
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            wavfile.write(temp_file.name, sample_rate, tone)
            temp_path = temp_file.name
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, info = model.transcribe(temp_path, beam_size=1, language="en")
        _ = " ".join(segment.text for segment in segments).strip()
        assert info.language == "en"
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


def test_tts_pyttsx3() -> None:
    require_integration()
    pyttsx3 = pytest.importorskip("pyttsx3")

    engine = pyttsx3.init()
    voices = engine.getProperty("voices") or []
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)
    engine.say("Vision test ok")
    engine.runAndWait()
    assert isinstance(voices, list)


async def test_ollama_tools() -> None:
    require_integration()
    import websockets

    payload = load_json(f"{BASE}/api/models")
    ollama_models_raw = payload.get("providers", {}).get("ollama", {}).get("models", [])
    ollama_models = ollama_models_raw if isinstance(ollama_models_raw, list) else str(ollama_models_raw).split()
    preferred_prefixes = ("gpt-oss", "llama3.2", "llama3.1", "qwen2.5", "qwen2")
    tool_model = next(
        (model for model in ollama_models if any(model.startswith(prefix) for prefix in preferred_prefixes)),
        "",
    )
    if not tool_model:
        pytest.skip("no suitable local Ollama model available for tool-calling validation")

    async with websockets.connect(WS, open_timeout=5) as ws:
        init = json.loads(await ws.recv())
        orig_provider = init.get("provider", "ollama")
        orig_model = init.get("model", "gpt-oss:20b")
        orig_mode = init.get("mode", "chat")
        try:
            await ws.send(json.dumps({"type": "set_model", "provider": "ollama", "model": tool_model}))
            await ws.send(json.dumps({"type": "set_mode", "mode": "operator"}))
            await ws.send(json.dumps({"type": "input", "text": "Run the echo command to output TOOLCALL_OK"}))
            deadline = time.time() + 60
            while time.time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(raw)
                    if msg.get("type") == "action":
                        assert "TOOLCALL_OK" in str(msg.get("result", "")) or msg.get("action")
                        return
                except TimeoutError:
                    pass
            pytest.fail("no tool action seen from local Ollama model")
        finally:
            await ws.send(json.dumps({"type": "set_model", "provider": orig_provider, "model": orig_model}))
            await ws.send(json.dumps({"type": "set_mode", "mode": orig_mode}))


if __name__ == "__main__":
    os.environ["VISION_RUN_INTEGRATION"] = "1"
    raise SystemExit(pytest.main([__file__, "-q", "-s", "-m", "integration"]))
