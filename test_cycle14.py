"""Cycle 14 regression tests.

Covers:
- _activate_provider() global mutations wrapped in _global_state_lock
- set_continuous WS handler locks global write
- /screenshot endpoint has rate limiting
- yamlCode.innerHTML uses escHtml(webhookUrl)
- quality.yml coverage threshold bumped to 60%
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# 1. _activate_provider() uses _global_state_lock
# ---------------------------------------------------------------------------


class TestActivateProviderLock(unittest.TestCase):
    def test_global_state_lock_acquired(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def _activate_provider(provider: str)")
        snippet = src[idx : idx + 600]
        self.assertIn("async with _global_state_lock:", snippet)

    def test_mutations_inside_lock(self):
        """current_provider and current_model must be set inside the lock block."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def _activate_provider(provider: str)")
        snippet = src[idx : idx + 600]
        lock_pos = snippet.index("async with _global_state_lock:")
        provider_pos = snippet.index("current_provider = provider")
        model_pos = snippet.index("current_model = _provider_default_model(provider)")
        # Both assignments must come after the lock acquisition
        self.assertGreater(provider_pos, lock_pos)
        self.assertGreater(model_pos, lock_pos)

    def test_early_return_before_lock(self):
        """The early-return guard should remain BEFORE the lock to avoid unnecessary locking."""
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def _activate_provider(provider: str)")
        snippet = src[idx : idx + 600]
        early_return_pos = snippet.index("return")
        lock_pos = snippet.index("async with _global_state_lock:")
        self.assertLess(early_return_pos, lock_pos)


# ---------------------------------------------------------------------------
# 2. set_continuous WS handler locks global write
# ---------------------------------------------------------------------------


class TestSetContinuousLock(unittest.TestCase):
    def test_lock_wraps_continuous_listening_write(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index('elif t == "set_continuous":')
        snippet = src[idx : idx + 300]
        self.assertIn("async with _global_state_lock:", snippet)
        lock_pos = snippet.index("async with _global_state_lock:")
        assign_pos = snippet.index("continuous_listening = bool")
        self.assertGreater(assign_pos, lock_pos)


# ---------------------------------------------------------------------------
# 3. /screenshot endpoint has rate limiting
# ---------------------------------------------------------------------------


class TestScreenshotRateLimit(unittest.TestCase):
    def test_request_param_added(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(")
        snippet = src[idx : idx + 100]
        self.assertIn("request: Request", snippet)

    def test_rate_limit_check_present(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(")
        snippet = src[idx : idx + 400]
        self.assertIn("_check_rate_limit", snippet)
        self.assertIn("screenshot:", snippet)

    def test_max_10_per_minute(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(")
        snippet = src[idx : idx + 400]
        self.assertIn("max_calls=10", snippet)
        self.assertIn("window_secs=60.0", snippet)

    def test_returns_429_on_limit(self):
        src = (ROOT / "live_chat_app.py").read_text(encoding="utf-8")
        idx = src.index("async def screenshot_ep(")
        snippet = src[idx : idx + 400]
        self.assertIn("status_code=429", snippet)


# ---------------------------------------------------------------------------
# 4. yamlCode.innerHTML uses escHtml(webhookUrl)
# ---------------------------------------------------------------------------


class TestYamlCodeXSSFix(unittest.TestCase):
    def test_escHtml_wraps_webhookUrl(self):
        src = (ROOT / "live_chat_ui.html").read_text(encoding="utf-8")
        self.assertIn("escHtml(webhookUrl)", src)

    def test_bare_webhookUrl_not_in_innerHTML(self):
        """Bare ${webhookUrl} must not appear inside innerHTML template."""
        import re

        src = (ROOT / "live_chat_ui.html").read_text(encoding="utf-8")
        # Find yamlCode.innerHTML assignment and verify it uses escHtml
        pattern = re.compile(r"yamlCode\.innerHTML\s*=.*?\$\{webhookUrl\}", re.DOTALL)
        self.assertIsNone(pattern.search(src), "Bare ${webhookUrl} still in yamlCode.innerHTML")

    def test_escHtml_used_not_textContent(self):
        """The HTML structure requires innerHTML but it must use escHtml for the URL."""
        src = (ROOT / "live_chat_ui.html").read_text(encoding="utf-8")
        # The line should contain both yamlCode.innerHTML and escHtml(webhookUrl)
        lines = src.splitlines()
        for line in lines:
            if "yamlCode.innerHTML" in line:
                self.assertIn("escHtml(webhookUrl)", line, "yamlCode.innerHTML must use escHtml(webhookUrl)")
                return
        self.fail("yamlCode.innerHTML line not found")


# ---------------------------------------------------------------------------
# 5. quality.yml coverage threshold bumped to 60%
# ---------------------------------------------------------------------------


class TestCoverageThreshold(unittest.TestCase):
    def test_threshold_at_least_60(self):
        src = (ROOT / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")
        import re

        m = re.search(r"--cov-fail-under=(\d+)", src)
        self.assertIsNotNone(m, "--cov-fail-under not found in quality.yml")
        threshold = int(m.group(1))
        self.assertGreaterEqual(threshold, 60, f"Coverage threshold {threshold}% is below 60%")


if __name__ == "__main__":
    unittest.main(verbosity=2)
