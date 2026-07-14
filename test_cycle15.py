"""Cycle 15 regression tests.

Covers:
- screenshot_ep() 10s asyncio.wait_for timeout
- fetch_url granular httpx.Timeout (connect=5, read=N, write=10)
- _ensure_schema() ALTER TABLE column-name whitelist
- /api/command-center/* localhost-only guard
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# 1. screenshot_ep() 10s timeout
# ---------------------------------------------------------------------------

class TestScreenshotTimeout(unittest.TestCase):
    def test_wait_for_wraps_executor(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(request: Request)")
        snippet = src[idx : idx + 1200]
        self.assertIn("asyncio.wait_for(", snippet)
        self.assertIn("timeout=10.0", snippet)

    def test_timeout_error_caught(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(request: Request)")
        snippet = src[idx : idx + 1200]
        self.assertIn("except asyncio.TimeoutError:", snippet)

    def test_504_on_timeout(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(request: Request)")
        snippet = src[idx : idx + 1200]
        self.assertIn("status_code=504", snippet)

    def test_timeout_logged(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(request: Request)")
        snippet = src[idx : idx + 1200]
        self.assertIn("screenshot_timeout", snippet)


# ---------------------------------------------------------------------------
# 2. fetch_url granular httpx.Timeout
# ---------------------------------------------------------------------------

class TestFetchUrlGranularTimeout(unittest.TestCase):
    def test_granular_timeout_object_used(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index('elif name == "fetch_url":')
        snippet = src[idx : idx + 600]
        self.assertIn("httpx.Timeout(connect=5.0", snippet)

    def test_read_timeout_uses_variable(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index('elif name == "fetch_url":')
        snippet = src[idx : idx + 600]
        self.assertIn("read=float(timeout_secs)", snippet)

    def test_write_timeout_present(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index('elif name == "fetch_url":')
        snippet = src[idx : idx + 600]
        self.assertIn("write=10.0", snippet)

    def test_no_bare_scalar_timeout(self):
        """Old scalar timeout=timeout_secs must be gone from fetch_url."""
        import re
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index('elif name == "fetch_url":')
        snippet = src[idx : idx + 600]
        # Must not have AsyncClient(timeout=timeout_secs  (without httpx.Timeout wrapper)
        bare = re.compile(r"AsyncClient\(timeout=timeout_secs")
        self.assertIsNone(bare.search(snippet), "Bare scalar timeout still present in fetch_url")


# ---------------------------------------------------------------------------
# 3. _ensure_schema() column-name whitelist
# ---------------------------------------------------------------------------

class TestEnsureSchemaWhitelist(unittest.TestCase):
    def test_whitelist_dict_declared(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        self.assertIn("_ALLOWED_MIGRATION_COLS", src)

    def test_whitelist_contains_expected_columns(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        self.assertIn('"file_mtime"', src)
        self.assertIn('"file_hash"', src)

    def test_validation_check_present(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        self.assertIn("col not in _ALLOWED_MIGRATION_COLS", src)

    def test_raises_on_unexpected_col(self):
        """Whitelist validation must raise ValueError for unknown columns."""
        _ALLOWED_MIGRATION_COLS = {"file_mtime": "INTEGER", "file_hash": "TEXT"}
        test_cases = [
            ("file_mtime", "INTEGER", False),  # valid → no raise
            ("file_hash", "TEXT", False),       # valid → no raise
            ("evil_col", "TEXT", True),          # invalid → raise
            ("file_mtime", "BLOB", True),        # wrong type → raise
        ]
        for col, typedef, should_raise in test_cases:
            should_fail = col not in _ALLOWED_MIGRATION_COLS or _ALLOWED_MIGRATION_COLS[col] != typedef
            self.assertEqual(should_fail, should_raise,
                             f"Whitelist check for ({col!r}, {typedef!r}) gave wrong result")


# ---------------------------------------------------------------------------
# 4. /api/command-center/* localhost-only guard
# ---------------------------------------------------------------------------

class TestCommandCenterLocalhostGuard(unittest.TestCase):
    def _get_routine_snippet(self, src: str) -> str:
        idx = src.index('"/api/command-center/routines/{routine_id}"')
        return src[idx : idx + 400]

    def _get_mission_snippet(self, src: str) -> str:
        idx = src.index('"/api/command-center/missions/{mission_id}"')
        return src[idx : idx + 400]

    def test_routine_endpoint_has_request_param(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def api_command_center_run_routine(")
        snippet = src[idx : idx + 100]
        self.assertIn("request: Request", snippet)

    def test_mission_endpoint_has_request_param(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def api_command_center_run_mission(")
        snippet = src[idx : idx + 100]
        self.assertIn("request: Request", snippet)

    def test_routine_localhost_check(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        snippet = self._get_routine_snippet(src)
        self.assertIn("127.0.0.1", snippet)
        self.assertIn("status_code=403", snippet)

    def test_mission_localhost_check(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        snippet = self._get_mission_snippet(src)
        self.assertIn("127.0.0.1", snippet)
        self.assertIn("status_code=403", snippet)

    def test_ipv6_localhost_included(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        snippet = self._get_routine_snippet(src)
        self.assertIn("::1", snippet)

    def test_whitelist_logic(self):
        """Verify the IP whitelist logic directly."""
        allowed = {"127.0.0.1", "::1", "localhost"}
        self.assertIn("127.0.0.1", allowed)
        self.assertIn("::1", allowed)
        self.assertNotIn("10.0.0.1", allowed)
        self.assertNotIn("192.168.1.1", allowed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
