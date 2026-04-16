"""
elite_safety.py — Security checks, safe patterns, vulnerability detection
=========================================================================
Prevents common vulnerabilities: injection, secrets exposure, unsafe async.
"""

import re
from typing import List, Optional
from dataclasses import dataclass

# ──────────────────────────────────────────────────────────────────────────────
# Secret Detection
# ──────────────────────────────────────────────────────────────────────────────

SENSITIVE_PATTERNS = {
    "api_key": re.compile(
        r"(?i)(api[_-]?key|secret|token)\s*[:=]?\s*['\"]?"
        r"([a-zA-Z0-9\-._~+/]+=*)['\"]?",
        re.IGNORECASE,
    ),
    "aws_key": re.compile(r"(AKIA[0-9A-Z]{16})"),
    "github_token": re.compile(r"ghp_[0-9a-zA-Z]{36}"),
    "password": re.compile(
        r"(?i)(password|passwd|pwd)\s*[:=]?\s*['\"]([^'\"]+)['\"]"
    ),
    "database_url": re.compile(r"(mongodb|postgres|mysql|redis):\/\/.*?@"),
    "private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |PGP )?PRIVATE KEY"
    ),
}


def scan_for_secrets(text: str, patterns: dict = None) -> List[dict]:
    """Scan text for exposed secrets/credentials."""
    patterns = patterns or SENSITIVE_PATTERNS
    findings = []

    for secret_type, pattern in patterns.items():
        matches = pattern.finditer(text)
        for match in matches:
            findings.append({
                "type": secret_type,
                "position": match.start(),
                "pattern": secret_type,
                "severity": "CRITICAL",
            })

    return findings


def sanitize_for_logging(text: str) -> str:
    """Remove sensitive data before logging."""
    for secret_type, pattern in SENSITIVE_PATTERNS.items():
        text = pattern.sub(f"<{secret_type}>", text)
    return text


def validate_no_hardcoded_secrets(
    code: str, raise_on_finding: bool = False
) -> bool:
    """Validate code contains no hardcoded secrets."""
    findings = scan_for_secrets(code)
    if findings and raise_on_finding:
        raise ValueError(f"Found {len(findings)} potential secrets in code")
    return len(findings) == 0


# ──────────────────────────────────────────────────────────────────────────────
# Input Validation & Sanitization
# ──────────────────────────────────────────────────────────────────────────────


class InputValidator:
    """Validate and sanitize user inputs."""

    @staticmethod
    def sanitize_file_path(
        path: str, base_dir: str = None
    ) -> Optional[str]:
        """Prevent path traversal attacks."""
        import os
        from pathlib import Path

        normalized = os.path.normpath(path)

        if ".." in normalized:
            return None

        if base_dir:
            resolved = Path(base_dir).resolve() / normalized
            try:
                resolved.relative_to(Path(base_dir).resolve())
            except ValueError:
                return None  # Outside base_dir

        return normalized

    @staticmethod
    def sanitize_shell_input(text: str) -> str:
        """Escape shell metacharacters."""
        import shlex
        return shlex.quote(text)

    @staticmethod
    def validate_json_input(
        data: str, max_size_bytes: int = 1_000_000
    ) -> tuple[bool, Optional[dict]]:
        """Safely validate and parse JSON."""
        if len(data) > max_size_bytes:
            return False, None

        try:
            import json
            return True, json.loads(data)
        except json.JSONDecodeError:
            return False, None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and prevent SSRF."""
        import re as _re
        from urllib.parse import urlparse

        if not _re.match(r"^https?://", url):
            return False

        parsed = urlparse(url)

        blocked_hosts = {
            "localhost", "127.0.0.1", "0.0.0.0",
            "169.254.169.254",  # AWS metadata
        }
        if parsed.hostname in blocked_hosts:
            return False

        return True


# ──────────────────────────────────────────────────────────────────────────────
# Async Safety
# ──────────────────────────────────────────────────────────────────────────────


class AsyncSafety:
    """Detect and prevent common async antipatterns."""

    @staticmethod
    def validate_no_blocking_in_async(fn_code: str) -> List[str]:
        """Warn about blocking calls in async functions."""
        warnings = []
        blocking_calls = {
            "open(": "Use aiofiles.open() instead",
            "requests.": "Use httpx.AsyncClient instead",
            "time.sleep(": "Use asyncio.sleep() instead",
            "json.dumps(": "OK if result is not awaited",
            "socket.": "Use asyncio sockets",
        }

        for call, suggestion in blocking_calls.items():
            if call in fn_code:
                warnings.append(
                    f"Possible blocking call '{call}': {suggestion}"
                )

        return warnings

    @staticmethod
    def validate_proper_task_cleanup(code: str) -> List[str]:
        """Warn about uncancelled asyncio tasks."""
        warnings = []

        if "asyncio.create_task(" in code and "cancel()" not in code:
            warnings.append(
                "create_task used without visible cancel() — may leak tasks"
            )

        if "gather(" in code and "return_exceptions" not in code:
            warnings.append(
                "gather() without return_exceptions may fail if one task raises"
            )

        return warnings


# ──────────────────────────────────────────────────────────────────────────────
# Code Quality Checks
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class CodeHealth:
    """Code quality assessment."""

    has_type_hints: bool
    has_docstrings: bool
    lacks_secrets: bool
    no_blocking_calls: bool
    async_safe: bool
    score: float  # 0-1
    issues: List[str]


def assess_code_health(code: str, is_async: bool = False) -> CodeHealth:
    """Holistic code health assessment."""
    issues = []

    has_type_hints = "->" in code or ": " in code
    has_docstrings = '"""' in code or "'''" in code

    secrets = scan_for_secrets(code)
    lacks_secrets = len(secrets) == 0
    if secrets:
        issues.append(f"Found {len(secrets)} potential secrets")

    no_blocking = True
    async_safe = True
    if is_async:
        blocking_warns = AsyncSafety.validate_no_blocking_in_async(code)
        async_warns = AsyncSafety.validate_proper_task_cleanup(code)
        no_blocking = len(blocking_warns) == 0
        async_safe = len(async_warns) == 0
        issues.extend(blocking_warns)
        issues.extend(async_warns)

    score = sum([
        has_type_hints * 0.25,
        has_docstrings * 0.25,
        lacks_secrets * 0.25,
        no_blocking * 0.125,
        async_safe * 0.125,
    ])

    return CodeHealth(
        has_type_hints=has_type_hints,
        has_docstrings=has_docstrings,
        lacks_secrets=lacks_secrets,
        no_blocking_calls=no_blocking,
        async_safe=async_safe,
        score=score,
        issues=issues,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Enforcement
# ──────────────────────────────────────────────────────────────────────────────


class SecurityPolicy:
    """Enforce security policies."""

    STRICT = {
        "allow_secrets": False,
        "require_type_hints": True,
        "require_docstrings": True,
        "block_dangerous_modules": ["pickle", "eval", "exec"],
    }

    RELAXED = {
        "allow_secrets": False,
        "require_type_hints": False,
        "require_docstrings": False,
        "block_dangerous_modules": ["pickle"],
    }

    @staticmethod
    def enforce(code: str, policy: dict) -> tuple[bool, List[str]]:
        """Check code against policy."""
        violations = []

        if not policy.get("allow_secrets"):
            secrets = scan_for_secrets(code)
            if secrets:
                violations.append(
                    f"Policy violation: hardcoded secrets found ({len(secrets)})"
                )

        if policy.get("require_type_hints") and "->" not in code:
            violations.append("Policy violation: missing type hints")

        if policy.get("require_docstrings") and '"""' not in code:
            violations.append("Policy violation: missing docstrings")

        for module in policy.get("block_dangerous_modules", []):
            if f"import {module}" in code or f"from {module}" in code:
                violations.append(
                    f"Policy violation: blocked module '{module}'"
                )

        return len(violations) == 0, violations
