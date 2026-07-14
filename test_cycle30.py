"""Structural tests for cycle 30 fixes.

1. tts_rate clamped to [50, 300]
2. preferred_stt validated against allowed set
3. preferred_tts validated against allowed set
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).parent / "live_chat_app.py"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _voice_settings_block() -> str:
    src = _read(APP)
    m = re.search(
        r'elif t == "set_voice_settings":(.*?)(?=\n            elif t ==|\Z)',
        src,
        re.DOTALL,
    )
    assert m is not None, "set_voice_settings WS handler not found"
    return m.group(1)


# ---------------------------------------------------------------------------
# tts_rate bounds
# ---------------------------------------------------------------------------


def test_tts_rate_clamped():
    body = _voice_settings_block()
    assert "max(50, min(300," in body or "min(300, max(50," in body, (
        "tts_rate must be clamped to [50, 300] using max/min"
    )


def test_tts_rate_still_int_guarded():
    body = _voice_settings_block()
    # int() conversion must still be inside try/except (ValueError, TypeError)
    assert "(ValueError, TypeError)" in body
    tts_pos = body.find("tts_rate = max(")
    if tts_pos == -1:
        tts_pos = body.find("tts_rate = min(")
    assert tts_pos != -1, "tts_rate clamped assignment not found"
    preceding = body[:tts_pos]
    assert "try:" in preceding, "tts_rate must be inside a try block"


# ---------------------------------------------------------------------------
# preferred_stt validation
# ---------------------------------------------------------------------------


def test_preferred_stt_validated():
    body = _voice_settings_block()
    # Must check against allowed set
    assert '"auto"' in body and '"groq"' in body and '"local"' in body, (
        "preferred_stt must be validated against {auto, elevenlabs, groq, local}"
    )
    # Must not be a bare assignment
    lines = [l.strip() for l in body.splitlines() if "preferred_stt = msg.get" in l]
    assert not lines, "preferred_stt must not be set via bare msg.get(); must be validated first"


def test_preferred_stt_only_updated_when_key_present():
    body = _voice_settings_block()
    # Must guard with 'if "preferred_stt" in msg'
    assert '"preferred_stt" in msg' in body, "preferred_stt must only update when key is present in msg"


# ---------------------------------------------------------------------------
# preferred_tts validation
# ---------------------------------------------------------------------------


def test_preferred_tts_validated():
    body = _voice_settings_block()
    # TTS set only has auto/elevenlabs/local
    assert '"auto"' in body, "preferred_tts validation missing 'auto'"
    assert '"elevenlabs"' in body, "preferred_tts validation missing 'elevenlabs'"
    # Must not be a bare assignment
    lines = [l.strip() for l in body.splitlines() if "preferred_tts = msg.get" in l]
    assert not lines, "preferred_tts must not be set via bare msg.get(); must be validated first"


def test_preferred_tts_only_updated_when_key_present():
    body = _voice_settings_block()
    assert '"preferred_tts" in msg' in body, "preferred_tts must only update when key is present in msg"
