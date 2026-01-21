"""Tests for pagination utilities."""

import pytest
from pydantic import ValidationError

from slither_mcp.pagination import PaginatedRequest, apply_pagination


class TestPaginatedRequest:
    """Tests for PaginatedRequest base class."""

    def test_default_values(self):
        """Test that default pagination values are set correctly."""

        class TestRequest(PaginatedRequest):
            path: str

        request = TestRequest(path="/test")
        assert request.limit is None
        assert request.offset == 0

    def test_explicit_values(self):
        """Test setting explicit pagination values."""

        class TestRequest(PaginatedRequest):
            path: str

        request = TestRequest(path="/test", limit=10, offset=20)
        assert request.limit == 10
        assert request.offset == 20

    def test_limit_validation_positive(self):
        """Test that limit must be positive if provided."""

        class TestRequest(PaginatedRequest):
            path: str

        with pytest.raises(ValidationError) as exc_info:
            TestRequest(path="/test", limit=0)
        assert "limit must be >= 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            TestRequest(path="/test", limit=-5)
        assert "limit must be >= 1" in str(exc_info.value)

    def test_limit_none_is_valid(self):
        """Test that None limit is accepted (no limit)."""

        class TestRequest(PaginatedRequest):
            path: str

        request = TestRequest(path="/test", limit=None)
        assert request.limit is None

    def test_offset_validation_non_negative(self):
        """Test that offset must be non-negative."""

        class TestRequest(PaginatedRequest):
            path: str

        with pytest.raises(ValidationError) as exc_info:
            TestRequest(path="/test", offset=-1)
        assert "offset must be >= 0" in str(exc_info.value)

    def test_offset_zero_is_valid(self):
        """Test that zero offset is accepted."""

        class TestRequest(PaginatedRequest):
            path: str

        request = TestRequest(path="/test", offset=0)
        assert request.offset == 0


class TestApplyPagination:
    """Tests for apply_pagination helper function."""

    def test_no_pagination(self):
        """Test with no pagination applied (offset=0, limit=None)."""
        items = ["a", "b", "c", "d", "e"]
        result, total, has_more = apply_pagination(items, offset=0, limit=None)

        assert result == ["a", "b", "c", "d", "e"]
        assert total == 5
        assert has_more is False

    def test_limit_only(self):
        """Test with limit but no offset."""
        items = ["a", "b", "c", "d", "e"]
        result, total, has_more = apply_pagination(items, offset=0, limit=3)

        assert result == ["a", "b", "c"]
        assert total == 5
        assert has_more is True

    def test_offset_only(self):
        """Test with offset but no limit."""
        items = ["a", "b", "c", "d", "e"]
        result, total, has_more = apply_pagination(items, offset=2, limit=None)

        assert result == ["c", "d", "e"]
        assert total == 5
        assert has_more is False

    def test_offset_and_limit(self):
        """Test with both offset and limit."""
        items = ["a", "b", "c", "d", "e"]
        result, total, has_more = apply_pagination(items, offset=1, limit=2)

        assert result == ["b", "c"]
        assert total == 5
        assert has_more is True

    def test_offset_beyond_items(self):
        """Test offset larger than item count."""
        items = ["a", "b", "c"]
        result, total, has_more = apply_pagination(items, offset=5, limit=None)

        assert result == []
        assert total == 3
        assert has_more is False

    def test_limit_larger_than_remaining(self):
        """Test limit larger than remaining items after offset."""
        items = ["a", "b", "c", "d", "e"]
        result, total, has_more = apply_pagination(items, offset=3, limit=10)

        assert result == ["d", "e"]
        assert total == 5
        assert has_more is False

    def test_empty_list(self):
        """Test pagination on empty list."""
        items: list[str] = []
        result, total, has_more = apply_pagination(items, offset=0, limit=10)

        assert result == []
        assert total == 0
        assert has_more is False

    def test_exact_page_size(self):
        """Test when limit equals remaining items (no has_more)."""
        items = ["a", "b", "c"]
        result, total, has_more = apply_pagination(items, offset=0, limit=3)

        assert result == ["a", "b", "c"]
        assert total == 3
        assert has_more is False

    def test_preserves_original_list(self):
        """Test that original list is not modified."""
        items = ["a", "b", "c", "d", "e"]
        original_items = items.copy()
        apply_pagination(items, offset=1, limit=2)

        assert items == original_items

    def test_with_complex_objects(self):
        """Test pagination with complex objects (not just strings)."""

        class Item:
            def __init__(self, value: int):
                self.value = value

        items = [Item(i) for i in range(10)]
        result, total, has_more = apply_pagination(items, offset=3, limit=4)

        assert len(result) == 4
        assert [r.value for r in result] == [3, 4, 5, 6]
        assert total == 10
        assert has_more is True
