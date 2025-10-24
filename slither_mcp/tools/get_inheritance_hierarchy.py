"""Tool for getting inheritance hierarchy."""

from typing import Annotated
from pydantic import BaseModel, Field

from slither_mcp.types import (
    ContractKey,
    ProjectFacts,
)


class InheritanceNode(BaseModel):
    """A node in the inheritance hierarchy tree."""
    contract_key: Annotated[
        ContractKey,
        Field(description="The contract key for this node in the hierarchy")
    ]
    inherits: Annotated[
        list['InheritanceNode'],
        Field(description="The contracts that this contract directly inherits from")
    ] = []


# Rebuild the model to resolve forward references
InheritanceNode.model_rebuild()


class InheritanceHierarchyRequest(BaseModel):
    """Request to get inheritance hierarchy for a contract."""
    contract_key: Annotated[
        ContractKey,
        Field(description="The contract key to get inheritance hierarchy for")
    ]


class InheritanceHierarchyResponse(BaseModel):
    """Response containing inheritance hierarchy."""
    success: bool
    contract_key: ContractKey
    full_inheritance: InheritanceNode | None = None
    error_message: str | None = None


def build_inheritance_tree(
    contract_key: ContractKey,
    project_facts: ProjectFacts,
    visited: set[ContractKey] | None = None
) -> InheritanceNode:
    """
    Build a recursive inheritance tree for a contract.
    
    Args:
        contract_key: The contract to build the tree for
        project_facts: The project facts containing contract data
        visited: Set of already visited contracts to prevent infinite recursion
        
    Returns:
        InheritanceNode representing the contract and its inheritance hierarchy
    """
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion in case of circular dependencies
    if contract_key in visited:
        return InheritanceNode(contract_key=contract_key, inherits=[])
    
    visited.add(contract_key)
    
    contract_model = project_facts.contracts.get(contract_key)
    if contract_model is None:
        return InheritanceNode(contract_key=contract_key, inherits=[])
    
    # Recursively build trees for all directly inherited contracts
    inherited_nodes = []
    for parent_key in contract_model.directly_inherits:
        inherited_nodes.append(
            build_inheritance_tree(parent_key, project_facts, visited.copy())
        )
    
    return InheritanceNode(
        contract_key=contract_key,
        inherits=inherited_nodes
    )


def get_inheritance_hierarchy(
    request: InheritanceHierarchyRequest,
    project_facts: ProjectFacts
) -> InheritanceHierarchyResponse:
    """
    Get the inheritance hierarchy for a contract.
    
    Args:
        request: The inheritance hierarchy request
        project_facts: The project facts containing contract data
        
    Returns:
        InheritanceHierarchyResponse with recursive hierarchy or error message
    """
    # Check if contract exists
    contract_model = project_facts.contracts.get(request.contract_key)
    
    if contract_model is None:
        return InheritanceHierarchyResponse(
            success=False,
            contract_key=request.contract_key,
            error_message=f"Contract not found: {request.contract_key.contract_name}"
        )
    
    # Build the recursive inheritance tree
    inheritance_tree = build_inheritance_tree(request.contract_key, project_facts)
    
    return InheritanceHierarchyResponse(
        success=True,
        contract_key=request.contract_key,
        full_inheritance=inheritance_tree
    )

