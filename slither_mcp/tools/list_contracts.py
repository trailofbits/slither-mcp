"""Tool for listing contracts with optional filters."""

from typing import Literal, Optional
from pydantic import BaseModel

from slither_mcp.types import (
    ContractKey,
    ProjectFacts,
    JSONStringTolerantModel,
)


class ContractInfo(BaseModel):
    """Basic contract information."""
    key: ContractKey
    is_abstract: bool
    is_interface: bool
    is_library: bool
    is_fully_implemented: bool


class ListContractsRequest(JSONStringTolerantModel):
    """Request to list contracts with optional filters."""
    path: str
    filter_type: Optional[Literal["all", "concrete", "interface", "library", "abstract"]] = "all"


class ListContractsResponse(BaseModel):
    """Response containing list of contracts."""
    success: bool
    contracts: list[ContractInfo]
    total_count: int
    error_message: str | None = None


def list_contracts(
    request: ListContractsRequest,
    project_facts: ProjectFacts
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
        
        contracts.append(ContractInfo(
            key=key,
            is_abstract=model.is_abstract,
            is_interface=model.is_interface,
            is_library=model.is_library,
            is_fully_implemented=model.is_fully_implemented
        ))
    
    return ListContractsResponse(
        success=True,
        contracts=contracts,
        total_count=len(contracts)
    )

