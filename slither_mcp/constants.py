"""Shared constants for Slither MCP server."""

# Tree traversal defaults
DEFAULT_MAX_DEPTH = 3  # Inheritance/derived tree depth limit
DEFAULT_MAX_NODES = 100  # Call graph node limit

# Special Solidity function names (entry points/lifecycle)
SPECIAL_FUNCTION_NAMES = frozenset(
    {
        "constructor",
        "receive",
        "fallback",
        "setUp",  # Foundry test setup
        "run",  # Foundry script entry
    }
)

# Test function prefix (Foundry convention)
TEST_FUNCTION_PREFIX = "test"

# Slither internal function prefix (generated functions)
SLITHER_INTERNAL_PREFIX = "slither"
