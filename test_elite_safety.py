"""Unit tests for elite_safety.py."""

import pytest
from elite_safety import InputValidator

def test_validate_json_input_valid():
    """Test with valid JSON string."""
    success, data = InputValidator.validate_json_input('{"key": "value"}')
    assert success is True
    assert data == {"key": "value"}

def test_validate_json_input_invalid():
    """Test with invalid JSON string."""
    success, data = InputValidator.validate_json_input('{"key": "value"')
    assert success is False
    assert data is None

def test_validate_json_input_empty():
    """Test with empty JSON string."""
    success, data = InputValidator.validate_json_input('')
    assert success is False
    assert data is None

def test_validate_json_input_exceeds_max_size():
    """Test with JSON string exceeding max_size_bytes."""
    large_json = '{"key": "value"}'
    success, data = InputValidator.validate_json_input(large_json, max_size_bytes=10)
    assert success is False
    assert data is None

def test_validate_json_input_exact_max_size():
    """Test with JSON string exactly matching max_size_bytes."""
    exact_json = '{"k": "v"}' # length is 10
    assert len(exact_json) == 10
    success, data = InputValidator.validate_json_input(exact_json, max_size_bytes=10)
    assert success is True
    assert data == {"k": "v"}
