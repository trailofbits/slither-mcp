"""Tests for types.py functions."""

import pytest

from slither_mcp.types import (
    find_matching_signature,
    normalize_signature,
)


class TestNormalizeSignature:
    """Tests for normalize_signature function."""

    def test_simple_signature_unchanged(self):
        """Test that simple signatures without prefixes are unchanged."""
        sig = "transfer(address,uint256)"
        assert normalize_signature(sig) == "transfer(address,uint256)"

    def test_removes_single_prefix(self):
        """Test removing a single type prefix."""
        sig = "swap(PoolKey,IPoolManager.SwapParams,bytes)"
        normalized = normalize_signature(sig)
        assert normalized == "swap(PoolKey,SwapParams,bytes)"

    def test_removes_multiple_prefixes(self):
        """Test removing multiple type prefixes."""
        sig = "execute(IManager.Command,IRouter.Params)"
        normalized = normalize_signature(sig)
        assert normalized == "execute(Command,Params)"

    def test_handles_no_parameters(self):
        """Test signatures with no parameters."""
        sig = "initialize()"
        assert normalize_signature(sig) == "initialize()"

    def test_handles_array_types(self):
        """Test handling array types with prefixes."""
        sig = "batchSwap(IVault.SwapKind,IVault.BatchSwapStep[],IAsset[])"
        normalized = normalize_signature(sig)
        assert normalized == "batchSwap(SwapKind,BatchSwapStep[],IAsset[])"

    def test_function_name_unchanged(self):
        """Test that function name with dots is preserved."""
        # Edge case: if the function name had a dot (shouldn't happen in Solidity)
        sig = "myFunction(Type.Nested)"
        normalized = normalize_signature(sig)
        assert normalized == "myFunction(Nested)"

    def test_no_parenthesis(self):
        """Test input without parenthesis returns unchanged."""
        sig = "noParens"
        assert normalize_signature(sig) == "noParens"

    def test_preserves_basic_types(self):
        """Test that basic Solidity types are preserved."""
        sig = "transfer(address,uint256,bytes32)"
        assert normalize_signature(sig) == "transfer(address,uint256,bytes32)"

    def test_handles_deeply_nested_type(self):
        """Test deeply nested type prefixes (only last part kept)."""
        sig = "foo(A.B.C.Type)"
        normalized = normalize_signature(sig)
        assert normalized == "foo(Type)"


class TestFindMatchingSignature:
    """Tests for find_matching_signature function."""

    def test_exact_match(self):
        """Test exact signature match."""
        available = {
            "transfer(address,uint256)": "func1",
            "approve(address,uint256)": "func2",
        }
        result = find_matching_signature("transfer(address,uint256)", available)
        assert result == "transfer(address,uint256)"

    def test_normalized_match(self):
        """Test finding signature via normalized matching."""
        available = {
            "swap(PoolKey,SwapParams,bytes)": "func1",
            "approve(address,uint256)": "func2",
        }
        # User specifies with qualified type
        result = find_matching_signature("swap(PoolKey,IPoolManager.SwapParams,bytes)", available)
        assert result == "swap(PoolKey,SwapParams,bytes)"

    def test_no_match(self):
        """Test that non-matching signature returns None."""
        available = {
            "transfer(address,uint256)": "func1",
            "approve(address,uint256)": "func2",
        }
        result = find_matching_signature("nonexistent()", available)
        assert result is None

    def test_exact_match_preferred(self):
        """Test that exact match is returned even when normalized would also match."""
        available = {
            "swap(PoolKey,IPoolManager.SwapParams,bytes)": "exact",
            "swap(PoolKey,SwapParams,bytes)": "normalized",
        }
        # Exact match should be preferred
        result = find_matching_signature(
            "swap(PoolKey,IPoolManager.SwapParams,bytes)", available
        )
        assert result == "swap(PoolKey,IPoolManager.SwapParams,bytes)"

    def test_empty_dict(self):
        """Test with empty available signatures."""
        result = find_matching_signature("transfer()", {})
        assert result is None
