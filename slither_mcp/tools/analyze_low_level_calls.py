"""Tool for analyzing low-level calls in a project."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    ContractKey,
    FunctionKey,
    ProjectFacts,
)


class LowLevelCallInfo(BaseModel):
    """Information about a function with low-level calls."""

    function_key: Annotated[FunctionKey, Field(description="Function containing low-level calls")]
    visibility: Annotated[str, Field(description="Function visibility")]
    is_payable: Annotated[bool, Field(description="Whether function is payable")]
    solidity_modifiers: Annotated[
        list[str], Field(description="Solidity modifiers on the function")
    ]
    custom_modifiers: Annotated[list[str], Field(description="Custom modifiers on the function")]


class AnalyzeLowLevelCallsRequest(PaginatedRequest):
    """Request to analyze low-level calls in a project."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Optional, limit to specific contract"),
    ] = None
    visibility_filter: Annotated[
        str | None,
        Field(description="Optional, filter by visibility (public, external, internal, private)"),
    ] = None


class AnalyzeLowLevelCallsResponse(BaseModel):
    """Response containing low-level call analysis."""

    success: bool
    calls: Annotated[
        list[LowLevelCallInfo],
        Field(description="Functions with low-level calls"),
    ] = []
    total_count: Annotated[
        int, Field(description="Total number of functions with low-level calls")
    ] = 0
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    summary: Annotated[
        dict[str, int],
        Field(description="Summary counts by visibility"),
    ] = {}
    error_message: str | None = None


def analyze_low_level_calls(
    request: AnalyzeLowLevelCallsRequest, project_facts: ProjectFacts
) -> AnalyzeLowLevelCallsResponse:
    """
    Find functions with low-level calls (call, delegatecall, staticcall, send, transfer).

    Args:
        request: The analyze low-level calls request
        project_facts: The project facts containing contract data

    Returns:
        AnalyzeLowLevelCallsResponse with functions containing low-level calls
    """
    functions_with_low_level_calls: list[LowLevelCallInfo] = []
    visibility_counts: dict[str, int] = {}

    for contract_key, contract in project_facts.contracts.items():
        # Skip if filtering by contract and this isn't the target
        if request.contract_key and contract_key != request.contract_key:
            continue

        # Check declared functions
        for sig, func in contract.functions_declared.items():
            if not func.callees.has_low_level_calls:
                continue

            # Apply visibility filter if specified
            if request.visibility_filter:
                if func.visibility.lower() != request.visibility_filter.lower():
                    continue

            func_key = FunctionKey(
                signature=sig,
                contract_name=contract_key.contract_name,
                path=contract_key.path,
            )

            info = LowLevelCallInfo(
                function_key=func_key,
                visibility=func.visibility,
                is_payable="payable" in func.solidity_modifiers,
                solidity_modifiers=func.solidity_modifiers,
                custom_modifiers=func.function_modifiers,
            )
            functions_with_low_level_calls.append(info)

            # Track visibility counts
            vis = func.visibility.lower()
            visibility_counts[vis] = visibility_counts.get(vis, 0) + 1

    # Sort by visibility (external/public first as more exposed)
    visibility_order = {"external": 0, "public": 1, "internal": 2, "private": 3}
    functions_with_low_level_calls.sort(key=lambda x: visibility_order.get(x.visibility.lower(), 4))

    # Apply pagination
    calls, total_count, has_more = apply_pagination(
        functions_with_low_level_calls, request.offset, request.limit
    )

    return AnalyzeLowLevelCallsResponse(
        success=True,
        calls=calls,
        total_count=total_count,
        has_more=has_more,
        summary=visibility_counts,
    )
