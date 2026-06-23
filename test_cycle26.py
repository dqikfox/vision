"""
test_cycle26.py — Structural tests for cycle-26 improvements

All bare asyncio.create_task() fire-and-forget calls replaced with
_tracked_task() so exceptions are logged instead of silently swallowed.

Verified sites:
- brain_ai.ingest (post-response background ingestion)
- speak(spoken[:120]) in webhook handler
- _start_el_agent() / _stop_el_agent() (REST endpoints + WS handler)
- broadcast({"type":"stt_active",...}) after transcription
- broadcast({"type":"voice_settings",...}) after local voice set
"""

import re

APP = "live_chat_app.py"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Helper: find _tracked_task definition
# ---------------------------------------------------------------------------


def test_tracked_task_helper_exists():
    src = _read(APP)
    assert "def _tracked_task(" in src, "_tracked_task helper must be defined"
    assert "add_done_callback" in src, "_tracked_task must attach a done callback"
    assert "write_log" in src, "_tracked_task callback must log exceptions"


# ---------------------------------------------------------------------------
# brain_ai.ingest — must use _tracked_task, not bare create_task
# ---------------------------------------------------------------------------


def test_brain_ingest_uses_tracked_task():
    src = _read(APP)
    fn = re.search(
        r"def _maybe_run_brain_ai\(.*?(?=\nasync def |\ndef (?!_))",
        src,
        re.DOTALL,
    )
    # May be inlined — search for the ingest call
    ingest_ctx = re.search(
        r"(asyncio\.create_task|_tracked_task)\s*\(\s*\n?\s*brain_ai\.ingest\(",
        src,
        re.DOTALL,
    )
    assert ingest_ctx is not None, "brain_ai.ingest task call not found"
    assert ingest_ctx.group(1) == "_tracked_task", "brain_ai.ingest must use _tracked_task(), not asyncio.create_task()"


# ---------------------------------------------------------------------------
# speak() in webhook — must use _tracked_task
# ---------------------------------------------------------------------------


def test_webhook_speak_uses_tracked_task():
    src = _read(APP)
    # The webhook speak call uses speak(spoken[:120]) — verify it uses _tracked_task
    assert "_tracked_task(speak(spoken[:120]))" in src, (
        "Webhook handler must use _tracked_task(speak(spoken[:120])) not asyncio.create_task()"
    )
    assert "asyncio.create_task(speak(spoken[:120]))" not in src, (
        "Webhook speak call must not use bare asyncio.create_task()"
    )


# ---------------------------------------------------------------------------
# _start_el_agent / _stop_el_agent — both sites must use _tracked_task
# ---------------------------------------------------------------------------


def test_el_agent_start_uses_tracked_task():
    src = _read(APP)
    # Must have zero bare create_task calls for _start_el_agent
    bare = list(re.finditer(r"asyncio\.create_task\(_start_el_agent\(\)\)", src))
    assert not bare, f"Found {len(bare)} bare asyncio.create_task(_start_el_agent()) — must use _tracked_task() instead"
    tracked = list(re.finditer(r"_tracked_task\(_start_el_agent\(\)\)", src))
    assert len(tracked) >= 2, (
        f"Expected at least 2 _tracked_task(_start_el_agent()) calls (REST endpoint + WS handler), found {len(tracked)}"
    )


def test_el_agent_stop_uses_tracked_task():
    src = _read(APP)
    bare = list(re.finditer(r"asyncio\.create_task\(_stop_el_agent\(\)\)", src))
    assert not bare, f"Found {len(bare)} bare asyncio.create_task(_stop_el_agent()) — must use _tracked_task() instead"
    tracked = list(re.finditer(r"_tracked_task\(_stop_el_agent\(\)\)", src))
    assert len(tracked) >= 2, (
        f"Expected at least 2 _tracked_task(_stop_el_agent()) calls (REST endpoint + WS handler), found {len(tracked)}"
    )


# ---------------------------------------------------------------------------
# broadcast stt_active — must use _tracked_task
# ---------------------------------------------------------------------------


def test_stt_active_broadcast_uses_tracked_task():
    src = _read(APP)
    # Find stt_active broadcast
    ctx = re.search(
        r'(asyncio\.create_task|_tracked_task)\s*\(\s*\n?\s*broadcast\s*\(\s*\n?\s*\{[^}]*"type":\s*"stt_active"',
        src,
        re.DOTALL,
    )
    assert ctx is not None, "stt_active broadcast task not found"
    assert ctx.group(1) == "_tracked_task", (
        "broadcast({type:stt_active}) must use _tracked_task(), not asyncio.create_task()"
    )


# ---------------------------------------------------------------------------
# broadcast voice_settings — must use _tracked_task
# ---------------------------------------------------------------------------


def test_voice_settings_broadcast_uses_tracked_task():
    src = _read(APP)
    ctx = re.search(
        r'(asyncio\.create_task|_tracked_task)\s*\(\s*\n?\s*broadcast\s*\(\s*\n?\s*\{[^}]*"type":\s*"voice_settings"',
        src,
        re.DOTALL,
    )
    assert ctx is not None, "voice_settings broadcast task not found"
    assert ctx.group(1) == "_tracked_task", (
        "broadcast({type:voice_settings}) must use _tracked_task(), not asyncio.create_task()"
    )
