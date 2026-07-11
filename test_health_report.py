from unittest.mock import patch

from hive_tools.health_report import check_dependencies


def test_check_dependencies_all_present():
    """Test when all dependencies are successfully imported."""
    with patch("builtins.__import__") as mock_import:
        result = check_dependencies()

    assert result == {"status": "HEALTHY", "missing": []}
    assert mock_import.call_count == 10


def test_check_dependencies_some_missing():
    """Test when some dependencies are missing."""

    def mock_import_side_effect(name, *args, **kwargs):
        if name in ["numpy", "elevenlabs"]:
            raise ImportError(f"No module named {name}")
        return None

    with patch("builtins.__import__", side_effect=mock_import_side_effect):
        result = check_dependencies()

    assert result == {"status": "DEGRADED", "missing": ["numpy", "elevenlabs"]}


def test_check_dependencies_all_missing():
    """Test when all dependencies are missing."""
    with patch("builtins.__import__", side_effect=ImportError("Module not found")):
        result = check_dependencies()

    assert result["status"] == "DEGRADED"
    assert len(result["missing"]) == 10
    assert "fastapi" in result["missing"]
