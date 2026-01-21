"""Tool for analyzing state variables in a project."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    ContractKey,
    ProjectFacts,
    StateVariableModel,
)


class StateVariableInfo(BaseModel):
    """Information about a state variable with contract context."""

    contract_key: Annotated[ContractKey, Field(description="Contract containing this variable")]
    variable: Annotated[StateVariableModel, Field(description="Variable details")]


class AnalyzeStateVariablesRequest(PaginatedRequest):
    """Request to analyze state variables in a project."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Optional, limit to specific contract"),
    ] = None
    visibility_filter: Annotated[
        str | None,
        Field(description="Optional, filter by visibility (public, internal, private)"),
    ] = None
    include_constants: Annotated[
        bool, Field(description="Include constant variables (default: true)")
    ] = True
    include_immutables: Annotated[
        bool, Field(description="Include immutable variables (default: true)")
    ] = True


class AnalyzeStateVariablesResponse(BaseModel):
    """Response containing state variable analysis."""

    success: bool
    variables: Annotated[
        list[StateVariableInfo],
        Field(description="List of state variables with their context"),
    ] = []
    total_count: Annotated[int, Field(description="Total number of state variables found")] = 0
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    summary: Annotated[
        dict[str, int],
        Field(description="Summary counts by visibility"),
    ] = {}
    error_message: str | None = None


def analyze_state_variables(
    request: AnalyzeStateVariablesRequest, project_facts: ProjectFacts
) -> AnalyzeStateVariablesResponse:
    """
    Analyze state variables across the project.

    Args:
        request: The analyze state variables request
        project_facts: The project facts containing contract data

    Returns:
        AnalyzeStateVariablesResponse with state variable information
    """
    state_vars: list[StateVariableInfo] = []
    visibility_counts: dict[str, int] = {}

    for contract_key, contract in project_facts.contracts.items():
        # Skip if filtering by contract and this isn't the target
        if request.contract_key and contract_key != request.contract_key:
            continue

        for var in contract.state_variables:
            # Apply visibility filter if specified
            if request.visibility_filter:
                if var.visibility.lower() != request.visibility_filter.lower():
                    continue

            # Apply constant/immutable filters
            if not request.include_constants and var.is_constant:
                continue
            if not request.include_immutables and var.is_immutable:
                continue

            info = StateVariableInfo(
                contract_key=contract_key,
                variable=var,
            )
            state_vars.append(info)

            # Track visibility counts
            vis = var.visibility.lower()
            visibility_counts[vis] = visibility_counts.get(vis, 0) + 1

    # Sort by contract name, then by variable name
    state_vars.sort(key=lambda x: (x.contract_key.contract_name, x.variable.name))

    # Apply pagination
    variables, total_count, has_more = apply_pagination(state_vars, request.offset, request.limit)

    return AnalyzeStateVariablesResponse(
        success=True,
        variables=variables,
        total_count=total_count,
        has_more=has_more,
        summary=visibility_counts,
    )
