"""Search utilities for MCP tool pattern matching."""

import re


class SearchError(Exception):
    """Raised when a search pattern is invalid."""

    pass


def compile_pattern(pattern: str, case_sensitive: bool = True) -> re.Pattern:
    """Compile a regex pattern with error handling.

    Args:
        pattern: The regex pattern string to compile
        case_sensitive: If False, compile with case-insensitive flag

    Returns:
        A compiled regex pattern object

    Raises:
        SearchError: If the pattern is not valid regex
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        return re.compile(pattern, flags)
    except re.error as e:
        raise SearchError(f"Invalid regex pattern: {e}") from e


def validate_pattern(pattern: str) -> str:
    """Validate that a string is a valid regex pattern.

    This is useful as a Pydantic field validator for pattern fields.

    Args:
        pattern: The pattern string to validate

    Returns:
        The pattern unchanged if valid

    Raises:
        ValueError: If the pattern is not valid regex
    """
    try:
        re.compile(pattern)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}") from e
    return pattern
