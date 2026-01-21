"""Tool for getting inherited contracts."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from slither_mcp.constants import DEFAULT_MAX_DEPTH
from slither_mcp.types import (
    ContractKey,
    JSONStringTolerantModel,
    ProjectFacts,
)


class InheritanceNode(BaseModel):
    """A node in the inheritance hierarchy tree."""

    contract_key: Annotated[
        ContractKey, Field(description="The contract key for this node in the hierarchy")
    ]
    inherits: Annotated[
        list["InheritanceNode"],
        Field(description="The contracts that this contract directly inherits from"),
    ] = []


# Rebuild the model to resolve forward references
InheritanceNode.model_rebuild()


class GetInheritedContractsRequest(JSONStringTolerantModel):
    """Request to get inherited contracts for a contract."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey, Field(description="The contract key to get inherited contracts for")
    ]
    max_depth: Annotated[
        int | None,
        Field(
            description=f"Maximum inheritance depth to traverse (None for unlimited, default {DEFAULT_MAX_DEPTH})"
        ),
    ] = DEFAULT_MAX_DEPTH

    @field_validator("max_depth")
    @classmethod
    def validate_max_depth(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("max_depth must be >= 1")
        return v


class GetInheritedContractsResponse(BaseModel):
    """Response containing inherited contracts."""

    success: bool
    contract_key: ContractKey
    full_inheritance: InheritanceNode | None = None
    truncated: Annotated[
        bool, Field(description="True if the tree was truncated due to max_depth limit")
    ] = False
    error_message: str | None = None


def build_inheritance_tree(
    contract_key: ContractKey,
    project_facts: ProjectFacts,
    visited: set[ContractKey] | None = None,
    current_depth: int = 0,
    max_depth: int | None = None,
    truncated_flag: list[bool] | None = None,
) -> InheritanceNode:
    """
    Build a recursive inheritance tree for a contract.

    Args:
        contract_key: The contract to build the tree for
        project_facts: The project facts containing contract data
        visited: Set of already visited contracts to prevent infinite recursion
        current_depth: Current depth in the tree (0-indexed)
        max_depth: Maximum depth to traverse (None for unlimited)
        truncated_flag: Mutable list to track if truncation occurred

    Returns:
        InheritanceNode representing the contract and its inheritance hierarchy
    """
    if visited is None:
        visited = set()
    if truncated_flag is None:
        truncated_flag = [False]

    # Prevent infinite recursion in case of circular dependencies
    if contract_key in visited:
        return InheritanceNode(contract_key=contract_key, inherits=[])

    visited.add(contract_key)

    contract_model = project_facts.contracts.get(contract_key)
    if contract_model is None:
        return InheritanceNode(contract_key=contract_key, inherits=[])

    # Check depth limit - if at max depth, don't recurse further
    if max_depth is not None and current_depth >= max_depth:
        # If there are parents we're not showing, mark as truncated
        if contract_model.directly_inherits:
            truncated_flag[0] = True
        return InheritanceNode(contract_key=contract_key, inherits=[])

    # Recursively build trees for all directly inherited contracts
    inherited_nodes = []
    for parent_key in contract_model.directly_inherits:
        inherited_nodes.append(
            build_inheritance_tree(
                parent_key,
                project_facts,
                visited.copy(),
                current_depth + 1,
                max_depth,
                truncated_flag,
            )
        )

    return InheritanceNode(contract_key=contract_key, inherits=inherited_nodes)


def get_inherited_contracts(
    request: GetInheritedContractsRequest, project_facts: ProjectFacts
) -> GetInheritedContractsResponse:
    """
    Get the inherited contracts for a contract.

    Args:
        request: The get inherited contracts request
        project_facts: The project facts containing contract data

    Returns:
        GetInheritedContractsResponse with recursive hierarchy or error message
    """
    # Check if contract exists
    contract_model = project_facts.contracts.get(request.contract_key)

    if contract_model is None:
        return GetInheritedContractsResponse(
            success=False,
            contract_key=request.contract_key,
            error_message=(
                f"Contract not found: '{request.contract_key.contract_name}' "
                f"at '{request.contract_key.path}'. "
                f"Use search_contracts or list_contracts to find available contracts."
            ),
        )

    # Build the recursive inheritance tree with depth tracking
    truncated_flag = [False]
    inheritance_tree = build_inheritance_tree(
        request.contract_key,
        project_facts,
        max_depth=request.max_depth,
        truncated_flag=truncated_flag,
    )

    return GetInheritedContractsResponse(
        success=True,
        contract_key=request.contract_key,
        full_inheritance=inheritance_tree,
        truncated=truncated_flag[0],
    )
