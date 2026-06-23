"""Cycle 12 regression tests.

Covers:
- _oai_client_cache LRU eviction when exceeding _OAI_CACHE_MAX entries
- _run_automation_routine TimeoutExpired handler returns graceful payload
- /api/rag/index 60s minimum interval between rebuilds
- voice_cli._tts_worker queue.get() timeout (queue.Empty continue)
- voice_cli._speak_eleven temp file cleanup on subprocess failure
- vision_mcp_server httpx.Timeout has connect deadline
- quality.yml pytest step has no continue-on-error
- vision_rag build_index explicit conn.close() in finally
- live_chat_ui escHtml used in pickerBody error
"""

from __future__ import annotations

import importlib
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_source(name: str, path: Path) -> types.ModuleType:
    """Import a module from an absolute path without executing package __init__."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    return mod  # intentionally not exec'd; tests import selectively


# ---------------------------------------------------------------------------
# 1. _oai_client_cache LRU eviction
# ---------------------------------------------------------------------------


class TestOaiClientCacheLRU(unittest.TestCase):
    """get_oai_client() evicts oldest entry when cache exceeds _OAI_CACHE_MAX."""

    def test_cache_size_capped(self):
        # Import only the relevant pieces via exec to avoid heavy side effects
        ns: dict = {}
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")

        # Extract the constant and dict declaration
        self.assertIn("_OAI_CACHE_MAX = 20", src)
        self.assertIn("_oai_client_cache: dict[str, AsyncOpenAI] = {}", src)

    def test_eviction_logic_present(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        self.assertIn("_OAI_CACHE_MAX", src)
        self.assertIn("len(_oai_client_cache) >= _OAI_CACHE_MAX", src)
        self.assertIn("oldest_key, old_client = next(iter(_oai_client_cache.items()))", src)
        self.assertIn("_oai_client_cache.pop(oldest_key, None)", src)
        self.assertIn("old_client._client.close()", src)

    def test_eviction_is_lru_order(self):
        """Verify the eviction reads the first (oldest) key, not a random one."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        # The pattern must use next(iter(...)) which gives insertion-order oldest
        self.assertIn("next(iter(_oai_client_cache.items()))", src)


# ---------------------------------------------------------------------------
# 2. _run_automation_routine TimeoutExpired handler
# ---------------------------------------------------------------------------


class TestAutomationTimeoutHandler(unittest.TestCase):
    def test_timeout_handler_present(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        self.assertIn("except subprocess.TimeoutExpired:", src)
        self.assertIn('write_log("automation_timeout"', src)
        self.assertIn('"exit_code": -1', src)

    def test_timeout_payload_shape(self):
        """Verify timeout block returns a dict with ok=False and exit_code=-1."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("except subprocess.TimeoutExpired:")
        snippet = src[idx : idx + 400]
        self.assertIn('"ok": False', snippet)
        self.assertIn('"exit_code": -1', snippet)
        self.assertIn("300 seconds", snippet)


# ---------------------------------------------------------------------------
# 3. /api/rag/index 60s minimum interval
# ---------------------------------------------------------------------------


class TestRagMinInterval(unittest.TestCase):
    def test_rag_last_build_times_declared(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        self.assertIn("_rag_last_build_times: dict[str, float] = {}", src)

    def test_min_interval_logic_present(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        self.assertIn("_rag_last_build_times", src)
        self.assertIn("60.0", src)
        self.assertIn("Minimum 60s between rebuilds", src)
        self.assertIn("rag_index_last:", src)

    def test_last_ts_updated_after_pass(self):
        """After the interval check passes, the timestamp must be stored."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        self.assertIn("_rag_last_build_times[last_key] = now_ts", src)


# ---------------------------------------------------------------------------
# 4. voice_cli._tts_worker queue.Empty continue
# ---------------------------------------------------------------------------


class TestTTSWorkerQueueTimeout(unittest.TestCase):
    def test_queue_get_has_timeout(self):
        src = (ROOT / "voice_cli.py").read_text(encoding="utf-8")
        self.assertIn("_tts_queue.get(timeout=2.0)", src)

    def test_empty_exception_handled(self):
        src = (ROOT / "voice_cli.py").read_text(encoding="utf-8")
        self.assertIn("except queue.Empty:", src)

    def test_worker_continues_on_empty(self):
        """queue.Empty should result in 'continue', not 'break'."""
        src = (ROOT / "voice_cli.py").read_text(encoding="utf-8")
        idx = src.index("except queue.Empty:")
        snippet = src[idx : idx + 60]
        self.assertIn("continue", snippet)


# ---------------------------------------------------------------------------
# 5. voice_cli._speak_eleven temp file cleanup on subprocess failure
# ---------------------------------------------------------------------------


class TestSpeakElevenTempCleanup(unittest.TestCase):
    def test_finally_block_present(self):
        src = (ROOT / "voice_cli.py").read_text(encoding="utf-8")
        idx = src.index("def _speak_eleven(text: str):")
        snippet = src[idx : idx + 1200]
        self.assertIn("finally:", snippet)
        self.assertIn("os.unlink(fname)", snippet)

    def test_subprocess_has_timeout(self):
        """subprocess.run must have an explicit timeout to prevent hang."""
        src = (ROOT / "voice_cli.py").read_text(encoding="utf-8")
        idx = src.index("def _speak_eleven(text: str):")
        snippet = src[idx : idx + 1200]
        self.assertIn("timeout=120", snippet)

    def test_fname_initialised_before_with(self):
        """fname = None must be set before the NamedTemporaryFile context so
        the finally block can safely call unlink even if the file was never created."""
        src = (ROOT / "voice_cli.py").read_text(encoding="utf-8")
        idx = src.index("def _speak_eleven(text: str):")
        snippet = src[idx : idx + 1200]
        self.assertIn("fname = None", snippet)


# ---------------------------------------------------------------------------
# 6. vision_mcp_server httpx.Timeout with connect deadline
# ---------------------------------------------------------------------------


class TestMCPHttpxTimeout(unittest.TestCase):
    def test_granular_timeout_used(self):
        src = (ROOT / "vision_mcp_server.py").read_text(encoding="utf-8")
        self.assertIn("httpx.Timeout(VISION_MCP_TIMEOUT, connect=3.0)", src)

    def test_not_scalar_timeout(self):
        """Old scalar timeout=VISION_MCP_TIMEOUT should be gone."""
        src = (ROOT / "vision_mcp_server.py").read_text(encoding="utf-8")
        # Should not have plain  timeout=VISION_MCP_TIMEOUT  as a standalone arg
        import re

        scalar_pat = re.compile(r"timeout=VISION_MCP_TIMEOUT[^)]")
        self.assertIsNone(scalar_pat.search(src), "Scalar timeout still present")


# ---------------------------------------------------------------------------
# 7. quality.yml pytest step has no continue-on-error
# ---------------------------------------------------------------------------


class TestQualityYmlTests(unittest.TestCase):
    def test_pytest_step_no_continue_on_error(self):
        src = (ROOT / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")
        lines = src.splitlines()
        in_tests_job = False
        in_pytest_step = False
        for line in lines:
            if "Unit & Integration Tests" in line:
                in_tests_job = True
            if in_tests_job and "Run unit tests" in line:
                in_pytest_step = True
            if in_pytest_step and "continue-on-error" in line:
                self.fail("pytest step still has continue-on-error in tests job")
            if in_pytest_step and line.strip().startswith("- name:") and "Run unit tests" not in line:
                in_pytest_step = False


# ---------------------------------------------------------------------------
# 8. vision_rag build_index conn.close() in finally
# ---------------------------------------------------------------------------


class TestRagBuildIndexConnClose(unittest.TestCase):
    def test_explicit_try_finally_pattern(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        snippet = src[idx : idx + 6000]
        self.assertIn("conn = self._connect()", snippet)
        self.assertIn("try:", snippet)
        self.assertIn("finally:", snippet)
        self.assertIn("conn.close()", snippet)

    def test_rollback_on_exception(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        snippet = src[idx : idx + 6000]
        self.assertIn("conn.rollback()", snippet)

    def test_wal_checkpoint_in_finally(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        snippet = src[idx : idx + 6000]
        self.assertIn("PRAGMA wal_checkpoint(TRUNCATE)", snippet)

    def test_no_with_connect_in_build_index(self):
        """build_index must NOT use 'with self._connect()' anymore."""
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        end_idx = src.index("\n    def ", idx + 1)
        snippet = src[idx:end_idx]
        self.assertNotIn("with self._connect()", snippet)


# ---------------------------------------------------------------------------
# 9. live_chat_ui escHtml used in pickerBody error
# ---------------------------------------------------------------------------


class TestPickerBodyXSSFix(unittest.TestCase):
    def test_escHtml_used_in_error_display(self):
        src = (ROOT / "live_chat_ui.html").read_text(encoding="utf-8")
        self.assertIn("escHtml(String(e.message", src)

    def test_bare_e_message_not_in_innerHTML(self):
        """Bare e.message without escaping should not appear in innerHTML."""
        src = (ROOT / "live_chat_ui.html").read_text(encoding="utf-8")
        import re

        # Pattern: innerHTML template literal containing ${e.message} without escHtml
        bare = re.compile(r"innerHTML\s*=.*\$\{e\.message\}", re.DOTALL)
        self.assertIsNone(bare.search(src), "Bare e.message still in innerHTML")


if __name__ == "__main__":
    unittest.main(verbosity=2)
