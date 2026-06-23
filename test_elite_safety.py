import pytest
from elite_safety import scan_for_secrets, SENSITIVE_PATTERNS

def test_scan_for_secrets_no_secrets():
    text = "This is a safe string with no credentials."
    findings = scan_for_secrets(text)
    assert len(findings) == 0

def test_scan_for_secrets_api_key():
    text = "Here is my api_key='abcdef1234567890'"
    findings = scan_for_secrets(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "api_key"
    assert findings[0]["severity"] == "CRITICAL"

def test_scan_for_secrets_aws_key():
    text = "AWS config: AKIAIOSFODNN7EXAMPLE"
    findings = scan_for_secrets(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "aws_key"

def test_scan_for_secrets_github_token():
    text = "My access is ghp_123456789012345678901234567890123456"
    findings = scan_for_secrets(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "github_token"

def test_scan_for_secrets_password():
    text = "DB_PASSWORD='supersecure123'"
    findings = scan_for_secrets(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "password"

def test_scan_for_secrets_database_url():
    text = "Connect to postgres://user:pass@localhost:5432/db"
    findings = scan_for_secrets(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "database_url"

def test_scan_for_secrets_private_key():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA"
    findings = scan_for_secrets(text)
    assert len(findings) == 1
    assert findings[0]["type"] == "private_key"

def test_scan_for_secrets_multiple_secrets():
    text = "AWS_KEY=AKIAIOSFODNN7EXAMPLE and DB_PWD='foo'"
    findings = scan_for_secrets(text)
    assert len(findings) == 2
    types = {f["type"] for f in findings}
    assert "aws_key" in types
    assert "password" in types

def test_sanitize_for_logging():
    from elite_safety import sanitize_for_logging
    # The api_key pattern includes "token", "secret", "api_key". It catches things like "secret='foo'".
    # password catches "password", "passwd", "pwd".
    # Wait, the api_key pattern doesn't specify word boundaries, and password doesn't either?
    # Let's just use something simple
    text = "Here is my api_key='abcdef1234567890' and my passwd='supersecure123'"
    sanitized = sanitize_for_logging(text)
    assert "<api_key>" in sanitized
    assert "<password>" in sanitized
    assert "abcdef1234567890" not in sanitized
    assert "supersecure123" not in sanitized

def test_validate_no_hardcoded_secrets():
    from elite_safety import validate_no_hardcoded_secrets
    assert validate_no_hardcoded_secrets("safe code here") is True
    assert validate_no_hardcoded_secrets("api_key='secret'") is False
    with pytest.raises(ValueError, match="Found 1 potential secrets in code"):
        validate_no_hardcoded_secrets("api_key='secret'", raise_on_finding=True)


def test_scan_for_secrets_custom_patterns():
    import re
    custom_patterns = {
        "custom_token": re.compile(r"MY_TOKEN_[0-9]+"),
    }
    text = "Here is my MY_TOKEN_12345"
    findings = scan_for_secrets(text, patterns=custom_patterns)
    assert len(findings) == 1
    assert findings[0]["type"] == "custom_token"
