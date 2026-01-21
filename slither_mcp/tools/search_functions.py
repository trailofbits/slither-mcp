"""Tool for searching functions by name or signature pattern."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from slither_mcp.pagination import apply_pagination
from slither_mcp.search import SearchError, compile_pattern, validate_pattern
from slither_mcp.types import FunctionKey, JSONStringTolerantModel, ProjectFacts


class SearchFunctionsRequest(JSONStringTolerantModel):
    """Request to search functions by pattern."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    pattern: Annotated[
        str, Field(description="Regex pattern to match function names or signatures")
    ]
    case_sensitive: Annotated[bool, Field(description="Whether the search is case-sensitive")] = (
        False
    )
    search_signatures: Annotated[
        bool,
        Field(description="If true, search full signatures; if false, search only function names"),
    ] = False
    limit: Annotated[int | None, Field(description="Maximum number of results to return")] = None
    offset: Annotated[int, Field(description="Number of results to skip for pagination")] = 0

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


class SearchFunctionsResponse(BaseModel):
    """Response with matching functions."""

    success: bool
    matches: list[FunctionKey]
    total_count: int
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def search_functions(
    request: SearchFunctionsRequest, project_facts: ProjectFacts
) -> SearchFunctionsResponse:
    """
    Search for functions matching a regex pattern.

    Args:
        request: The search request with pattern and options
        project_facts: The project facts containing contract data

    Returns:
        SearchFunctionsResponse with matching function keys
    """
    try:
        pattern = compile_pattern(request.pattern, request.case_sensitive)
    except SearchError as e:
        return SearchFunctionsResponse(
            success=False,
            matches=[],
            total_count=0,
            error_message=str(e),
        )

    matches: list[FunctionKey] = []

    for contract_key, contract_model in project_facts.contracts.items():
        # Search declared functions
        for sig in contract_model.functions_declared.keys():
            search_target = sig if request.search_signatures else _extract_function_name(sig)
            if pattern.search(search_target):
                matches.append(
                    FunctionKey(
                        signature=sig,
                        contract_name=contract_key.contract_name,
                        path=contract_key.path,
                    )
                )

        # Search inherited functions
        for sig in contract_model.functions_inherited.keys():
            search_target = sig if request.search_signatures else _extract_function_name(sig)
            if pattern.search(search_target):
                matches.append(
                    FunctionKey(
                        signature=sig,
                        contract_name=contract_key.contract_name,
                        path=contract_key.path,
                    )
                )

    matches, total_count, has_more = apply_pagination(matches, request.offset, request.limit)

    return SearchFunctionsResponse(
        success=True, matches=matches, total_count=total_count, has_more=has_more
    )


def _extract_function_name(signature: str) -> str:
    """Extract the function name from a full Solidity function signature.

    Args:
        signature: A function signature like 'transfer(address,uint256)'

    Returns:
        The function name portion (e.g., 'transfer'). Returns the full
        signature unchanged if no parenthesis is found.
    """
    paren_idx = signature.find("(")
    if paren_idx == -1:
        return signature
    return signature[:paren_idx]
