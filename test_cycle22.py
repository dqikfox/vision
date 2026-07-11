"""
test_cycle22.py — Structural tests for cycle-22 improvements

Tests verify:
1. Memory.__init__ initialises _save_lock (threading.Lock)
2. Memory.save() acquires _save_lock before writing
3. _handle_invalid_elevenlabs_auth wraps preferred_stt/tts mutations in _global_state_lock
4. _fast_completion closes AsyncOpenAI client (try/finally + client.close())
5. _pyttsx3_tts wraps run_in_executor in asyncio.wait_for with timeout
"""

import re

APP = "live_chat_app.py"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _find_fn(src: str, name: str) -> str:
    """Extract function/method body (from def to next def/class at same indentation)."""
    m = re.search(
        rf"(def {re.escape(name)}\(.*?)(?=\n    def |\nclass |\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert m is not None, f"Function {name!r} not found in {APP}"
    return m.group(1)


# ---------------------------------------------------------------------------
# 1. Memory._save_lock initialised in __init__
# ---------------------------------------------------------------------------


def test_memory_init_creates_save_lock():
    src = _read(APP)
    m = re.search(
        r"class Memory:.*?def __init__\(self\).*?(?=\n    def )",
        src,
        re.DOTALL,
    )
    assert m is not None, "Memory.__init__ not found"
    body = m.group()
    assert "_save_lock" in body, "Memory.__init__ must initialise self._save_lock"
    assert "threading.Lock()" in body, "Memory._save_lock must be a threading.Lock()"


def test_memory_save_lock_assigned_before_load():
    """Lock must be created before self._load() to avoid races during init."""
    src = _read(APP)
    # Scope to Memory class block first
    cls = re.search(r"class Memory:.*?(?=\nclass |\Z)", src, re.DOTALL)
    assert cls is not None, "Memory class not found"
    cls_body = cls.group()
    m = re.search(
        r"def __init__\(self\) -> None:(.*?)(?=\n    def )",
        cls_body,
        re.DOTALL,
    )
    assert m is not None
    body = m.group(1)
    lock_pos = body.find("_save_lock")
    load_pos = body.find("_load()")
    assert lock_pos != -1, "_save_lock not found in Memory.__init__"
    assert load_pos != -1, "_load() not found in Memory.__init__"
    assert lock_pos < load_pos, "_save_lock must be assigned before self._load()"


# ---------------------------------------------------------------------------
# 2. Memory.save() acquires _save_lock
# ---------------------------------------------------------------------------


def test_memory_save_acquires_lock():
    src = _read(APP)
    m = re.search(
        r"def save\(self\) -> None:(.*?)(?=\n    def |\nclass )",
        src,
        re.DOTALL,
    )
    assert m is not None, "Memory.save() not found"
    body = m.group(1)
    assert "_save_lock" in body, "Memory.save() must acquire self._save_lock"
    assert "with self._save_lock:" in body, "Memory.save() must use 'with self._save_lock:'"


def test_memory_save_atomic_rename_inside_lock():
    """The atomic rename (Path.replace) must be inside the lock block."""
    src = _read(APP)
    m = re.search(
        r"def save\(self\) -> None:(.*?)(?=\n    def |\nclass )",
        src,
        re.DOTALL,
    )
    assert m is not None
    body = m.group(1)
    lock_pos = body.find("with self._save_lock:")
    replace_pos = body.find(".replace(MEMORY_FILE)")
    assert lock_pos != -1
    assert replace_pos != -1
    assert replace_pos > lock_pos, "Atomic rename must occur inside the _save_lock block"


# ---------------------------------------------------------------------------
# 3. _handle_invalid_elevenlabs_auth under _global_state_lock
# ---------------------------------------------------------------------------


def test_elevenlabs_auth_uses_global_state_lock():
    src = _read(APP)
    fn = re.search(
        r"async def _handle_invalid_elevenlabs_auth\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_handle_invalid_elevenlabs_auth not found"
    body = fn.group()
    assert "_global_state_lock" in body, (
        "_handle_invalid_elevenlabs_auth must acquire _global_state_lock before mutating preferred_stt/preferred_tts"
    )


def test_elevenlabs_auth_lock_before_stt_mutation():
    """preferred_stt mutation must occur inside the _global_state_lock block."""
    src = _read(APP)
    fn = re.search(
        r"async def _handle_invalid_elevenlabs_auth\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    lock_pos = body.find("_global_state_lock")
    stt_pos = body.find('preferred_stt = "local"')
    assert lock_pos != -1
    assert stt_pos != -1
    assert stt_pos > lock_pos, "preferred_stt mutation must come after _global_state_lock acquisition"


# ---------------------------------------------------------------------------
# 4. _fast_completion closes clients via try/finally
# ---------------------------------------------------------------------------


def test_fast_completion_closes_ollama_client():
    src = _read(APP)
    fn = re.search(
        r"async def _fast_completion\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_fast_completion not found"
    body = fn.group()
    assert "await client.close()" in body, "_fast_completion must call await client.close() to release connection pools"


def test_fast_completion_client_close_in_finally():
    """client.close() must be inside a finally block so it runs even on error."""
    src = _read(APP)
    fn = re.search(
        r"async def _fast_completion\(.*?(?=\nasync def |\ndef )",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group()
    # Check for 'finally:' followed by 'await client.close()' within reasonable proximity
    finally_match = list(re.finditer(r"finally:", body))
    assert finally_match, "_fast_completion must use try/finally to close clients"
    close_match = list(re.finditer(r"await client\.close\(\)", body))
    assert close_match, "client.close() not found in _fast_completion"
    # Each finally block should have a close call after it
    for fm in finally_match:
        nearby_body = body[fm.start() : fm.start() + 200]
        assert "await client.close()" in nearby_body, "client.close() must appear immediately inside the finally block"


# ---------------------------------------------------------------------------
# 5. _pyttsx3_tts uses asyncio.wait_for with timeout
# ---------------------------------------------------------------------------


def test_pyttsx3_tts_has_wait_for():
    src = _read(APP)
    # _pyttsx3_tts is defined as a nested function inside a larger async def
    fn = re.search(
        r"async def _pyttsx3_tts\(text: str\)(.*?)(?=\n        async def |\n    async def |\n    def )",
        src,
        re.DOTALL,
    )
    assert fn is not None, "_pyttsx3_tts nested function not found"
    body = fn.group(1)
    assert "asyncio.wait_for" in body, "_pyttsx3_tts must wrap run_in_executor in asyncio.wait_for"


def test_pyttsx3_tts_timeout_value():
    src = _read(APP)
    fn = re.search(
        r"async def _pyttsx3_tts\(text: str\)(.*?)(?=\n        async def |\n    async def |\n    def )",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    assert "timeout=30" in body or "timeout=30.0" in body, "_pyttsx3_tts asyncio.wait_for must specify a 30s timeout"


def test_pyttsx3_tts_handles_timeout_error():
    src = _read(APP)
    fn = re.search(
        r"async def _pyttsx3_tts\(text: str\)(.*?)(?=\n        async def |\n    async def |\n    def )",
        src,
        re.DOTALL,
    )
    assert fn is not None
    body = fn.group(1)
    assert "TimeoutError" in body, "_pyttsx3_tts must catch asyncio.TimeoutError from the wait_for"
