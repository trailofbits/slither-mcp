"""Tool for searching contracts by name pattern."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from slither_mcp.pagination import apply_pagination
from slither_mcp.search import SearchError, compile_pattern, validate_pattern
from slither_mcp.types import (
    ContractKey,
    JSONStringTolerantModel,
    ProjectFacts,
    path_matches_exclusion,
)


class SearchContractsRequest(JSONStringTolerantModel):
    """Request to search contracts by pattern."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    pattern: Annotated[str, Field(description="Regex pattern to match contract names")]
    case_sensitive: Annotated[bool, Field(description="Whether the search is case-sensitive")] = (
        False
    )
    limit: Annotated[int | None, Field(description="Maximum number of results to return")] = None
    offset: Annotated[int, Field(description="Number of results to skip for pagination")] = 0
    exclude_paths: Annotated[
        list[str] | None,
        Field(description="Path prefixes to exclude (e.g., ['lib/', 'test/', 'node_modules/'])"),
    ] = None

    @field_validator("pattern")
    @classmethod
    def validate_pattern_field(cls, v: str) -> str:
        return validate_pattern(v)

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("limit must be >= 1")
        return v

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError("offset must be >= 0")
        return v


class SearchContractsResponse(BaseModel):
    """Response with matching contracts."""

    success: bool
    matches: list[ContractKey]
    total_count: int
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def search_contracts(
    request: SearchContractsRequest, project_facts: ProjectFacts
) -> SearchContractsResponse:
    """
    Search for contracts matching a regex pattern.

    Args:
        request: The search request with pattern and options
        project_facts: The project facts containing contract data

    Returns:
        SearchContractsResponse with matching contract keys
    """
    try:
        pattern = compile_pattern(request.pattern, request.case_sensitive)
    except SearchError as e:
        return SearchContractsResponse(
            success=False,
            matches=[],
            total_count=0,
            error_message=str(e),
        )

    matches = [key for key in project_facts.contracts.keys() if pattern.search(key.contract_name)]

    # Apply exclude_paths filter
    if request.exclude_paths:
        matches = [
            key for key in matches if not path_matches_exclusion(key.path, request.exclude_paths)
        ]

    matches, total_count, has_more = apply_pagination(matches, request.offset, request.limit)

    return SearchContractsResponse(
        success=True, matches=matches, total_count=total_count, has_more=has_more
    )
