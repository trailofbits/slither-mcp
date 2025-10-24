"""Tool for listing functions with optional filters."""

from typing import Optional
from pydantic import BaseModel

from slither_mcp.types import (
    ContractKey,
    FuncSig,
    FunctionKey,
    ProjectFacts,
)


class FunctionInfo(BaseModel):
    """Basic function information."""
    function_key: FunctionKey
    visibility: str
    solidity_modifiers: list[str]
    is_declared: bool  # True if declared, False if inherited


class ListFunctionsRequest(BaseModel):
    """Request to list functions with optional filters."""
    contract_key: ContractKey
    visibility: Optional[list[str]] = None
    has_modifiers: Optional[list[str]] = None


class ListFunctionsResponse(BaseModel):
    """Response containing list of functions."""
    success: bool
    functions: list[FunctionInfo]
    total_count: int
    error_message: str | None = None


def list_functions(
    request: ListFunctionsRequest,
    project_facts: ProjectFacts
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
            error_message=f"Contract not found: {request.contract_key.contract_name}"
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
                if not any(mod in func_model.solidity_modifiers for mod in request.has_modifiers):
                    continue
            
            functions.append(FunctionInfo(
                function_key=FunctionKey(
                    signature=sig,
                    contract_name=contract_key.contract_name,
                    path=contract_key.path
                ),
                visibility=func_model.visibility,
                solidity_modifiers=func_model.solidity_modifiers,
                is_declared=True
            ))
        
        # Check inherited functions
        for sig, func_model in contract_model.functions_inherited.items():
            # Apply visibility filter
            if request.visibility and func_model.visibility not in request.visibility:
                continue
            
            # Apply modifiers filter
            if request.has_modifiers:
                if not any(mod in func_model.solidity_modifiers for mod in request.has_modifiers):
                    continue
            
            functions.append(FunctionInfo(
                function_key=FunctionKey(
                    signature=sig,
                    contract_name=contract_key.contract_name,
                    path=contract_key.path
                ),
                visibility=func_model.visibility,
                solidity_modifiers=func_model.solidity_modifiers,
                is_declared=False
            ))
    
    return ListFunctionsResponse(
        success=True,
        functions=functions,
        total_count=len(functions)
    )

