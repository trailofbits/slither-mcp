"""Tool for listing contracts with optional filters."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    ContractKey,
    ProjectFacts,
    path_matches_exclusion,
)


class ContractInfo(BaseModel):
    """Basic contract information."""

    key: ContractKey
    is_abstract: bool
    is_interface: bool
    is_library: bool
    is_fully_implemented: bool
    function_count: Annotated[
        int, Field(description="Total number of functions (declared + inherited)")
    ] = 0


class ListContractsRequest(PaginatedRequest):
    """Request to list contracts with optional filters."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    filter_type: Literal["all", "concrete", "interface", "library", "abstract"] | None = "all"
    sort_by: Annotated[
        Literal["name", "path", "function_count"] | None,
        Field(description="Sort results by: name, path, or function_count"),
    ] = None
    sort_order: Annotated[
        Literal["asc", "desc"],
        Field(description="Sort order: asc (ascending) or desc (descending)"),
    ] = "asc"
    exclude_paths: Annotated[
        list[str] | None,
        Field(description="Path prefixes to exclude (e.g., ['lib/', 'test/', 'node_modules/'])"),
    ] = None


class ListContractsResponse(BaseModel):
    """Response containing list of contracts."""

    success: bool
    contracts: list[ContractInfo]
    total_count: int
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def list_contracts(
    request: ListContractsRequest, project_facts: ProjectFacts
) -> ListContractsResponse:
    """
    List all contracts with optional filters.

    Args:
        request: The list contracts request with filters
        project_facts: The project facts containing contract data

    Returns:
        ListContractsResponse with filtered contract list
    """
    contracts = []

    for key, model in project_facts.contracts.items():
        # Apply exclude_paths filter
        if request.exclude_paths:
            if path_matches_exclusion(key.path, request.exclude_paths):
                continue

        # Apply filter_type
        if request.filter_type == "concrete":
            if model.is_interface or model.is_library or model.is_abstract:
                continue
        elif request.filter_type == "interface":
            if not model.is_interface:
                continue
        elif request.filter_type == "library":
            if not model.is_library:
                continue
        elif request.filter_type == "abstract":
            if not model.is_abstract:
                continue
        # "all" includes everything

        # Calculate function count
        func_count = len(model.functions_declared) + len(model.functions_inherited)

        contracts.append(
            ContractInfo(
                key=key,
                is_abstract=model.is_abstract,
                is_interface=model.is_interface,
                is_library=model.is_library,
                is_fully_implemented=model.is_fully_implemented,
                function_count=func_count,
            )
        )

    # Apply sorting if specified
    if request.sort_by:
        reverse = request.sort_order == "desc"
        if request.sort_by == "name":
            contracts.sort(key=lambda c: c.key.contract_name.lower(), reverse=reverse)
        elif request.sort_by == "path":
            contracts.sort(key=lambda c: c.key.path.lower(), reverse=reverse)
        elif request.sort_by == "function_count":
            contracts.sort(key=lambda c: c.function_count, reverse=reverse)

    # Apply pagination
    contracts, total_count, has_more = apply_pagination(contracts, request.offset, request.limit)

    return ListContractsResponse(
        success=True, contracts=contracts, total_count=total_count, has_more=has_more
    )
