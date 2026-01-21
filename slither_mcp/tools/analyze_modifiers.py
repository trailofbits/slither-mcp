"""Tool for analyzing custom modifiers and their usage."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    ContractKey,
    FunctionKey,
    ProjectFacts,
)


class ModifierUsage(BaseModel):
    """Information about a modifier and its usage."""

    name: Annotated[str, Field(description="Name of the modifier")]
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Contract where modifier is defined (if determinable)"),
    ]
    used_by: Annotated[list[FunctionKey], Field(description="Functions that use this modifier")]
    usage_count: Annotated[int, Field(description="Number of functions using this modifier")]


class AnalyzeModifiersRequest(PaginatedRequest):
    """Request to analyze modifiers in a project."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Optional, limit to specific contract"),
    ] = None
    modifier_filter: Annotated[
        str | None,
        Field(description="Optional, filter by modifier name (case-insensitive substring)"),
    ] = None


class AnalyzeModifiersResponse(BaseModel):
    """Response containing modifier analysis."""

    success: bool
    modifiers: Annotated[
        list[ModifierUsage], Field(description="List of modifiers with their usage")
    ] = []
    total_count: Annotated[int, Field(description="Total number of modifiers found")] = 0
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def analyze_modifiers(
    request: AnalyzeModifiersRequest, project_facts: ProjectFacts
) -> AnalyzeModifiersResponse:
    """
    Analyze custom modifiers and their usage across the project.

    Args:
        request: The analyze modifiers request
        project_facts: The project facts containing contract data

    Returns:
        AnalyzeModifiersResponse with modifier usage information
    """
    # Collect modifier usage across all functions
    modifier_usage: dict[str, list[FunctionKey]] = {}

    for contract_key, contract in project_facts.contracts.items():
        # Skip if filtering by contract and this isn't the target
        if request.contract_key and contract_key != request.contract_key:
            continue

        # Check declared functions
        for sig, func in contract.functions_declared.items():
            for modifier_name in func.function_modifiers:
                # Apply modifier filter if specified
                if request.modifier_filter:
                    if request.modifier_filter.lower() not in modifier_name.lower():
                        continue

                if modifier_name not in modifier_usage:
                    modifier_usage[modifier_name] = []

                func_key = FunctionKey(
                    signature=sig,
                    contract_name=contract_key.contract_name,
                    path=contract_key.path,
                )
                modifier_usage[modifier_name].append(func_key)

        # Also check inherited functions if not filtering by contract
        if not request.contract_key:
            for sig, func in contract.functions_inherited.items():
                for modifier_name in func.function_modifiers:
                    if request.modifier_filter:
                        if request.modifier_filter.lower() not in modifier_name.lower():
                            continue

                    if modifier_name not in modifier_usage:
                        modifier_usage[modifier_name] = []

                    func_key = FunctionKey(
                        signature=sig,
                        contract_name=func.implementation_contract.contract_name,
                        path=func.implementation_contract.path,
                    )
                    # Avoid duplicates
                    if func_key not in modifier_usage[modifier_name]:
                        modifier_usage[modifier_name].append(func_key)

    # Build result list sorted by usage count (most used first)
    modifiers = []
    for name, functions in sorted(modifier_usage.items(), key=lambda x: len(x[1]), reverse=True):
        # Try to determine which contract defines this modifier
        # The modifier name may be in format "ContractName.modifierName"
        defining_contract = None
        if "." in name:
            contract_name = name.split(".")[0]
            # Find contract with this name
            for key in project_facts.contracts:
                if key.contract_name == contract_name:
                    defining_contract = key
                    break

        modifiers.append(
            ModifierUsage(
                name=name,
                contract_key=defining_contract,
                used_by=functions,
                usage_count=len(functions),
            )
        )

    # Apply pagination
    modifiers, total_count, has_more = apply_pagination(modifiers, request.offset, request.limit)

    return AnalyzeModifiersResponse(
        success=True,
        modifiers=modifiers,
        total_count=total_count,
        has_more=has_more,
    )
