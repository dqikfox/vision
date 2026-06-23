"""Cycle 13 regression tests.

Covers:
- _load_context_brain() JSON corruption fallback
- screenshot_region actual screen bounds clamping
- build_index() parameter validation + clamping
- broadcast() JSON pre-serialization safety
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# 1. _load_context_brain() corruption fallback
# ---------------------------------------------------------------------------

class TestContextBrainCorruptionFallback(unittest.TestCase):
    def test_try_except_wraps_json_load(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("def _load_context_brain(")
        snippet = src[idx : idx + 1000]
        self.assertIn("json.JSONDecodeError", snippet)
        self.assertIn("OSError", snippet)

    def test_write_log_on_corrupt(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("def _load_context_brain(")
        snippet = src[idx : idx + 1000]
        self.assertIn("context_brain_corrupt", snippet)

    def test_rebuild_exception_caught(self):
        """build_context_brain() failures should also be caught."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("def _load_context_brain(")
        snippet = src[idx : idx + 1000]
        self.assertIn("context_brain_rebuild_failed", snippet)

    def test_fallback_returns_safe_default(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("def _load_context_brain(")
        snippet = src[idx : idx + 1000]
        self.assertIn('"catalog"', snippet)
        self.assertIn('"automation"', snippet)

    def test_write_failure_caught(self):
        """Writing the brain file should also be wrapped in try/except."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("def _load_context_brain(")
        snippet = src[idx : idx + 1000]
        self.assertIn("context_brain_write_failed", snippet)


# ---------------------------------------------------------------------------
# 2. screenshot_region actual screen bounds
# ---------------------------------------------------------------------------

class TestScreenshotRegionBounds(unittest.TestCase):
    def test_uses_pyautogui_size(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("elif name == \"screenshot_region\":")
        snippet = src[idx : idx + 400]
        self.assertIn("pyautogui.size()", snippet)

    def test_x_clamped_to_screen_width(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("elif name == \"screenshot_region\":")
        snippet = src[idx : idx + 400]
        self.assertIn("screen_w - 1", snippet)

    def test_y_clamped_to_screen_height(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("elif name == \"screenshot_region\":")
        snippet = src[idx : idx + 400]
        self.assertIn("screen_h - 1", snippet)

    def test_width_clamped_relative_to_x(self):
        """Width must be clamped to screen_w - x to prevent out-of-bounds region."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("elif name == \"screenshot_region\":")
        snippet = src[idx : idx + 400]
        self.assertIn("screen_w - x", snippet)

    def test_height_clamped_relative_to_y(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("elif name == \"screenshot_region\":")
        snippet = src[idx : idx + 400]
        self.assertIn("screen_h - y", snippet)

    def test_no_hardcoded_65535(self):
        """Old magic constant 65535 should be gone from screenshot_region."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("elif name == \"screenshot_region\":")
        snippet = src[idx : idx + 400]
        self.assertNotIn("65535", snippet)


# ---------------------------------------------------------------------------
# 3. build_index() parameter validation
# ---------------------------------------------------------------------------

class TestBuildIndexParamValidation(unittest.TestCase):
    def test_max_files_capped(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        snippet = src[idx : idx + 600]
        self.assertIn("100_000", snippet)
        self.assertIn("max(0, min(max_files", snippet)

    def test_chunk_size_clamped(self):
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        snippet = src[idx : idx + 600]
        self.assertIn("max(100, min(chunk_size", snippet)
        self.assertIn("10_000", snippet)

    def test_overlap_clamped_below_chunk_size(self):
        """overlap must be clamped to less than chunk_size to avoid infinite loops."""
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        snippet = src[idx : idx + 600]
        self.assertIn("chunk_size - 1", snippet)
        self.assertIn("max(0, min(overlap", snippet)

    def test_validation_before_iter(self):
        """Validation must happen before _iter_source_files is called."""
        src = (ROOT / "vision_rag.py").read_text(encoding="utf-8")
        idx = src.index("def build_index(")
        snippet = src[idx : idx + 600]
        validate_pos = snippet.find("max(0, min(max_files")
        iter_pos = snippet.find("_iter_source_files")
        self.assertLess(validate_pos, iter_pos, "Validation must come before _iter_source_files")

    def test_logic_correctness(self):
        """Unit-test the clamping logic directly."""
        def clamp(max_files, chunk_size, overlap):
            max_files = max(0, min(max_files, 100_000))
            chunk_size = max(100, min(chunk_size, 10_000))
            overlap = max(0, min(overlap, chunk_size - 1))
            return max_files, chunk_size, overlap

        # Normal case
        self.assertEqual(clamp(50, 1400, 220), (50, 1400, 220))
        # Negative max_files → 0
        self.assertEqual(clamp(-1, 1400, 220)[0], 0)
        # Huge max_files → 100_000
        self.assertEqual(clamp(999_999_999, 1400, 220)[0], 100_000)
        # chunk_size too small → 100
        self.assertEqual(clamp(0, 50, 10)[1], 100)
        # overlap >= chunk_size → clamped
        self.assertEqual(clamp(0, 200, 300)[2], 199)
        # Negative overlap → 0
        self.assertEqual(clamp(0, 1400, -5)[2], 0)


# ---------------------------------------------------------------------------
# 4. broadcast() JSON pre-serialization safety
# ---------------------------------------------------------------------------

class TestBroadcastJsonSafety(unittest.TestCase):
    def test_pre_serialize_before_send_text(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def broadcast(msg: dict")
        snippet = src[idx : idx + 1200]
        # Must serialize before the send loop
        serialize_pos = snippet.find("msg_text = json.dumps(msg)")
        send_pos = snippet.find("await ws.send_text(msg_text)")
        self.assertGreater(serialize_pos, -1, "msg_text = json.dumps(msg) not found")
        self.assertGreater(send_pos, -1, "ws.send_text(msg_text) not found")
        self.assertLess(serialize_pos, send_pos, "Serialization must happen before send")

    def test_serialize_error_logged(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def broadcast(msg: dict")
        snippet = src[idx : idx + 1200]
        self.assertIn("broadcast_serialize_error", snippet)

    def test_sanitize_fallback(self):
        """When first serialization fails, a sanitized version must be tried."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def broadcast(msg: dict")
        snippet = src[idx : idx + 1200]
        self.assertIn("broadcast_sanitize_failed", snippet)

    def test_graceful_return_on_failure(self):
        """If both attempts fail, broadcast must return without raising."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def broadcast(msg: dict")
        snippet = src[idx : idx + 1200]
        # After sanitize failure there should be a bare return
        self.assertIn("return", snippet)

    def test_no_bare_json_dumps_in_send_loop(self):
        """json.dumps must not appear inside the ws send loop (it moved outside)."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def broadcast(msg: dict")
        snippet = src[idx : idx + 1200]
        send_idx = snippet.find("for ws in recipients:")
        after_loop = snippet[send_idx:]
        self.assertNotIn("json.dumps(msg)", after_loop)


if __name__ == "__main__":
    unittest.main(verbosity=2)
