import pytest

from elite_safety import validate_no_hardcoded_secrets


def test_validate_no_hardcoded_secrets_clean_code():
    """Test that clean code passes the validation."""
    clean_code = "def my_func():\n    return 'Hello World'"
    assert validate_no_hardcoded_secrets(clean_code) is True


def test_validate_no_hardcoded_secrets_with_secrets_no_raise():
    """Test that code with secrets returns False when raise_on_finding is False."""
    code_with_secret = "API_KEY = 'AKIA1234567890ABCDEF'"  # AWS Key mock
    assert validate_no_hardcoded_secrets(code_with_secret) is False


def test_validate_no_hardcoded_secrets_with_secrets_raise():
    """Test that code with secrets raises ValueError when raise_on_finding is True."""
    code_with_secret = "ghp_1234567890abcdef1234567890abcdef1234"  # Github token mock
    with pytest.raises(ValueError, match="Found 1 potential secrets in code"):
        validate_no_hardcoded_secrets(code_with_secret, raise_on_finding=True)


def test_validate_no_hardcoded_secrets_multiple_secrets():
    """Test code with multiple secrets raises correct ValueError."""
    # the regex for token also catches 'API_KEY' so 'AKIA...' and 'API_KEY' and 'ghp...' gives multiple results.
    code_with_secrets = "var1 = 'AKIA1234567890ABCDEF'\n var2 = 'ghp_1234567890abcdef1234567890abcdef1234'"
    with pytest.raises(ValueError, match="Found 2 potential secrets in code"):
        validate_no_hardcoded_secrets(code_with_secrets, raise_on_finding=True)
