"""Tool for getting derived contracts (children in the inheritance hierarchy)."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from slither_mcp.constants import DEFAULT_MAX_DEPTH
from slither_mcp.types import (
    ContractKey,
    JSONStringTolerantModel,
    ProjectFacts,
)


class DerivedNode(BaseModel):
    """A node in the derived contracts tree."""

    contract_key: Annotated[
        ContractKey, Field(description="The contract key for this node in the derived tree")
    ]
    derived_by: Annotated[
        list["DerivedNode"],
        Field(description="The contracts that directly inherit from this contract"),
    ] = []


# Rebuild the model to resolve forward references
DerivedNode.model_rebuild()


class GetDerivedContractsRequest(JSONStringTolerantModel):
    """Request to get derived contracts (contracts that inherit from this one)."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey, Field(description="The contract key to get derived contracts for")
    ]
    max_depth: Annotated[
        int | None,
        Field(
            description=f"Maximum derivation depth to traverse (None for unlimited, default {DEFAULT_MAX_DEPTH})"
        ),
    ] = DEFAULT_MAX_DEPTH

    @field_validator("max_depth")
    @classmethod
    def validate_max_depth(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("max_depth must be >= 1")
        return v


class GetDerivedContractsResponse(BaseModel):
    """Response containing derived contracts."""

    success: bool
    contract_key: ContractKey
    full_derived: DerivedNode | None = None
    truncated: Annotated[
        bool, Field(description="True if the tree was truncated due to max_depth limit")
    ] = False
    error_message: str | None = None


def build_derived_tree(
    contract_key: ContractKey,
    project_facts: ProjectFacts,
    visited: set[ContractKey] | None = None,
    current_depth: int = 0,
    max_depth: int | None = None,
    truncated_flag: list[bool] | None = None,
) -> DerivedNode:
    """
    Build a recursive derived contracts tree for a contract.

    Args:
        contract_key: The contract to build the tree for
        project_facts: The project facts containing contract data
        visited: Set of already visited contracts to prevent infinite recursion
        current_depth: Current depth in the tree (0-indexed)
        max_depth: Maximum depth to traverse (None for unlimited)
        truncated_flag: Mutable list to track if truncation occurred

    Returns:
        DerivedNode representing the contract and its derived contracts hierarchy
    """
    if visited is None:
        visited = set()
    if truncated_flag is None:
        truncated_flag = [False]

    # Prevent infinite recursion in case of circular dependencies
    if contract_key in visited:
        return DerivedNode(contract_key=contract_key, derived_by=[])

    visited.add(contract_key)

    # Find all contracts that directly inherit from this contract
    direct_children = []
    for potential_child_key, potential_child_model in project_facts.contracts.items():
        if contract_key in potential_child_model.directly_inherits:
            direct_children.append(potential_child_key)

    # Check depth limit - if at max depth, don't recurse further
    if max_depth is not None and current_depth >= max_depth:
        # If there are children we're not showing, mark as truncated
        if direct_children:
            truncated_flag[0] = True
        return DerivedNode(contract_key=contract_key, derived_by=[])

    # Recursively build trees for all children
    derived_contracts = []
    for child_key in direct_children:
        derived_contracts.append(
            build_derived_tree(
                child_key,
                project_facts,
                visited.copy(),
                current_depth + 1,
                max_depth,
                truncated_flag,
            )
        )

    return DerivedNode(contract_key=contract_key, derived_by=derived_contracts)


def get_derived_contracts(
    request: GetDerivedContractsRequest, project_facts: ProjectFacts
) -> GetDerivedContractsResponse:
    """
    Get the derived contracts for a contract (contracts that inherit from it).

    Args:
        request: The get derived contracts request
        project_facts: The project facts containing contract data

    Returns:
        GetDerivedContractsResponse with recursive hierarchy or error message
    """
    # Check if contract exists
    contract_model = project_facts.contracts.get(request.contract_key)

    if contract_model is None:
        return GetDerivedContractsResponse(
            success=False,
            contract_key=request.contract_key,
            error_message=(
                f"Contract not found: '{request.contract_key.contract_name}' "
                f"at '{request.contract_key.path}'. "
                f"Use search_contracts or list_contracts to find available contracts."
            ),
        )

    # Build the recursive derived contracts tree with depth tracking
    truncated_flag = [False]
    derived_tree = build_derived_tree(
        request.contract_key,
        project_facts,
        max_depth=request.max_depth,
        truncated_flag=truncated_flag,
    )

    return GetDerivedContractsResponse(
        success=True,
        contract_key=request.contract_key,
        full_derived=derived_tree,
        truncated=truncated_flag[0],
    )
