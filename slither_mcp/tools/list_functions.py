"""Tool for listing functions with optional filters."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    ContractKey,
    FunctionKey,
    ProjectFacts,
)


class FunctionInfo(BaseModel):
    """Basic function information."""

    function_key: FunctionKey
    visibility: str
    solidity_modifiers: list[str]
    is_declared: bool  # True if declared, False if inherited
    line_count: Annotated[
        int, Field(description="Number of lines in the function")
    ] = 0


class ListFunctionsRequest(PaginatedRequest):
    """Request to list functions with optional filters."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: ContractKey
    visibility: list[str] | None = None
    has_modifiers: list[str] | None = None
    sort_by: Annotated[
        Literal["name", "visibility", "line_count"] | None,
        Field(description="Sort results by: name, visibility, or line_count"),
    ] = None
    sort_order: Annotated[
        Literal["asc", "desc"],
        Field(description="Sort order: asc (ascending) or desc (descending)"),
    ] = "asc"


class ListFunctionsResponse(BaseModel):
    """Response containing list of functions."""

    success: bool
    functions: list[FunctionInfo]
    total_count: int
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def list_functions(
    request: ListFunctionsRequest, project_facts: ProjectFacts
) -> ListFunctionsResponse:
    """
    List functions with optional filters.

    Args:
        request: The list functions request with filters
        project_facts: The project facts containing contract data

    Returns:
        ListFunctionsResponse with filtered function list
    """
    functions = []

    # Get the specified contract
    contract_model = project_facts.contracts.get(request.contract_key)
    if not contract_model:
        return ListFunctionsResponse(
            success=False,
            functions=[],
            total_count=0,
            error_message=f"Contract not found: {request.contract_key.contract_name}",
        )

    contracts_to_search = [(request.contract_key, contract_model)]

    # Iterate through contracts and functions
    for contract_key, contract_model in contracts_to_search:
        # Check declared functions
        for sig, func_model in contract_model.functions_declared.items():
            # Apply visibility filter
            if request.visibility and func_model.visibility not in request.visibility:
                continue

            # Apply modifiers filter
            if request.has_modifiers:
                if not any(
                    mod in func_model.solidity_modifiers for mod in request.has_modifiers
                ):
                    continue

            # Calculate line count
            line_count = func_model.line_end - func_model.line_start + 1

            functions.append(
                FunctionInfo(
                    function_key=FunctionKey(
                        signature=sig,
                        contract_name=contract_key.contract_name,
                        path=contract_key.path,
                    ),
                    visibility=func_model.visibility,
                    solidity_modifiers=func_model.solidity_modifiers,
                    is_declared=True,
                    line_count=line_count,
                )
            )

        # Check inherited functions
        for sig, func_model in contract_model.functions_inherited.items():
            # Apply visibility filter
            if request.visibility and func_model.visibility not in request.visibility:
                continue

            # Apply modifiers filter
            if request.has_modifiers:
                if not any(
                    mod in func_model.solidity_modifiers for mod in request.has_modifiers
                ):
                    continue

            # Calculate line count
            line_count = func_model.line_end - func_model.line_start + 1

            functions.append(
                FunctionInfo(
                    function_key=FunctionKey(
                        signature=sig,
                        contract_name=contract_key.contract_name,
                        path=contract_key.path,
                    ),
                    visibility=func_model.visibility,
                    solidity_modifiers=func_model.solidity_modifiers,
                    is_declared=False,
                    line_count=line_count,
                )
            )

    # Apply sorting if specified
    if request.sort_by:
        reverse = request.sort_order == "desc"
        # Define visibility order for sorting
        visibility_order = {"external": 0, "public": 1, "internal": 2, "private": 3}
        if request.sort_by == "name":
            functions.sort(
                key=lambda f: f.function_key.signature.lower(), reverse=reverse
            )
        elif request.sort_by == "visibility":
            functions.sort(
                key=lambda f: visibility_order.get(f.visibility.lower(), 4),
                reverse=reverse,
            )
        elif request.sort_by == "line_count":
            functions.sort(key=lambda f: f.line_count, reverse=reverse)

    # Apply pagination
    functions, total_count, has_more = apply_pagination(
        functions, request.offset, request.limit
    )

    return ListFunctionsResponse(
        success=True, functions=functions, total_count=total_count, has_more=has_more
    )
