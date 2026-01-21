"""Tests for search utilities."""

import pytest

from slither_mcp.search import SearchError, compile_pattern, validate_pattern


class TestCompilePattern:
    """Tests for compile_pattern function."""

    def test_valid_pattern(self):
        """Test compiling a valid regex pattern."""
        pattern = compile_pattern(r"transfer\(.*\)")
        assert pattern.search("transfer(address,uint256)") is not None

    def test_case_sensitive_default(self):
        """Test that patterns are case-sensitive by default."""
        pattern = compile_pattern("Transfer")
        assert pattern.search("Transfer") is not None
        assert pattern.search("transfer") is None

    def test_case_insensitive(self):
        """Test case-insensitive pattern matching."""
        pattern = compile_pattern("transfer", case_sensitive=False)
        assert pattern.search("Transfer") is not None
        assert pattern.search("TRANSFER") is not None
        assert pattern.search("transfer") is not None

    def test_invalid_pattern_raises_search_error(self):
        """Test that invalid regex raises SearchError."""
        with pytest.raises(SearchError) as exc_info:
            compile_pattern("[invalid(")
        assert "Invalid regex pattern" in str(exc_info.value)

    def test_complex_regex_pattern(self):
        """Test compiling complex regex patterns."""
        # Pattern to match function signatures with specific argument types
        pattern = compile_pattern(r"\w+\(address,uint256\)")
        assert pattern.search("transfer(address,uint256)") is not None
        assert pattern.search("approve(address,uint256)") is not None
        assert pattern.search("transfer(uint256)") is None

    def test_empty_pattern(self):
        """Test that empty pattern matches everything."""
        pattern = compile_pattern("")
        assert pattern.search("anything") is not None
        assert pattern.search("") is not None

    def test_special_regex_characters(self):
        """Test patterns with special regex characters."""
        # Literal parentheses need escaping
        pattern = compile_pattern(r"func\(\)")
        assert pattern.search("func()") is not None
        assert pattern.search("func(x)") is None


class TestValidatePattern:
    """Tests for validate_pattern function (Pydantic validator helper)."""

    def test_valid_pattern_returns_unchanged(self):
        """Test that valid pattern is returned unchanged."""
        pattern = r"transfer\(.*\)"
        result = validate_pattern(pattern)
        assert result == pattern

    def test_invalid_pattern_raises_value_error(self):
        """Test that invalid regex raises ValueError (for Pydantic)."""
        with pytest.raises(ValueError) as exc_info:
            validate_pattern("[unclosed")
        assert "Invalid regex pattern" in str(exc_info.value)

    def test_simple_patterns(self):
        """Test validation of simple patterns."""
        assert validate_pattern("simple") == "simple"
        assert validate_pattern("^start") == "^start"
        assert validate_pattern("end$") == "end$"
        assert validate_pattern(".*") == ".*"

    def test_complex_valid_patterns(self):
        """Test validation of complex but valid patterns."""
        patterns = [
            r"[a-zA-Z]+",
            r"\d{1,3}",
            r"(foo|bar)",
            r"(?:non-capturing)",
            r"\w+\(\)",
        ]
        for pattern in patterns:
            result = validate_pattern(pattern)
            assert result == pattern

    def test_invalid_patterns(self):
        """Test various invalid patterns raise ValueError."""
        invalid_patterns = [
            "[",  # Unclosed bracket
            "(",  # Unclosed paren
            "*",  # Nothing to repeat
            "?",  # Nothing to make optional
            "+",  # Nothing to repeat
            "\\",  # Trailing backslash
        ]
        for pattern in invalid_patterns:
            with pytest.raises(ValueError):
                validate_pattern(pattern)


class TestSearchErrorException:
    """Tests for SearchError exception class."""

    def test_search_error_is_exception(self):
        """Test that SearchError is a proper exception."""
        error = SearchError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_search_error_can_chain_cause(self):
        """Test that SearchError preserves exception chaining."""
        original_error = ValueError("original")
        error = SearchError("wrapped")
        error.__cause__ = original_error
        assert error.__cause__ is not None
        assert isinstance(error.__cause__, ValueError)
