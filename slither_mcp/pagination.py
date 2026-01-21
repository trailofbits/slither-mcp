"""Pagination utilities for MCP tool responses."""

from typing import TypeVar

from pydantic import Field, field_validator

from slither_mcp.types import JSONStringTolerantModel

T = TypeVar("T")


class PaginatedRequest(JSONStringTolerantModel):
    """Base class for requests with pagination support.

    Inherit from this class to add consistent pagination parameters and
    validation to any MCP tool request.

    Example:
        class ListContractsRequest(PaginatedRequest):
            path: str
            filter_type: str | None = None
    """

    limit: int | None = Field(
        default=None,
        description="Maximum number of results to return",
    )
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
    )

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int | None) -> int | None:
        """Validate limit is positive if provided."""
        if v is not None and v < 1:
            raise ValueError("limit must be >= 1")
        return v

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: int) -> int:
        """Validate offset is non-negative."""
        if v < 0:
            raise ValueError("offset must be >= 0")
        return v


def apply_pagination(
    items: list[T],
    offset: int,
    limit: int | None,
) -> tuple[list[T], int, bool]:
    """Apply pagination to a list of items.

    Args:
        items: The full list of items to paginate
        offset: Number of items to skip from the beginning
        limit: Maximum number of items to return (None for no limit)

    Returns:
        A tuple of (paginated_items, total_count, has_more) where:
        - paginated_items: The subset of items after applying offset and limit
        - total_count: The total number of items before pagination
        - has_more: True if there are more items beyond the returned page
    """
    total_count = len(items)

    if offset:
        items = items[offset:]
    if limit is not None:
        items = items[:limit]

    has_more = (offset + len(items)) < total_count
    return items, total_count, has_more
