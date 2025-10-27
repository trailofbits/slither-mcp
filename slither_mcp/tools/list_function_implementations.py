"""Tool for listing contracts that implement a specific function."""

from typing import Annotated
from pydantic import BaseModel, Field

from slither_mcp.types import ContractKey, ContractModel, FuncSig, ProjectFacts


class ListFunctionImplementationsRequest(BaseModel):
    """Request to find contracts implementing a function."""
    
    contract_key: Annotated[
        ContractKey,
        Field(description="The contract key (typically an abstract contract or interface)")
    ]
    function_signature: Annotated[
        FuncSig,
        Field(description="The function signature to find implementations for (e.g., 'transfer(address,uint256)')")
    ]


class ListFunctionImplementationsResponse(BaseModel):
    """Response containing contracts that implement the function."""
    
    success: bool
    implementing_contracts: list[ContractModel] | None = None
    error_message: str | None = None


def list_function_implementations(
    request: ListFunctionImplementationsRequest,
    project_facts: ProjectFacts
) -> ListFunctionImplementationsResponse:
    """
    Find all contracts that implement a given function signature.
    
    This is useful for finding implementations of abstract functions or interface methods.
    The function searches through the inheritance tree to find all contracts that provide
    an implementation of the specified function.
    
    Args:
        request: Request containing contract key and function signature
        project_facts: The project facts containing all contract data
        
    Returns:
        Response with list of implementing contracts or error message
    """
    # Get the contract model
    contract_model = project_facts.contracts.get(request.contract_key)
    
    if not contract_model:
        return ListFunctionImplementationsResponse(
            success=False,
            error_message=f"Contract not found: {request.contract_key.contract_name} at {request.contract_key.path}"
        )
    
    # Check if the function exists in the contract
    if not contract_model.does_contract_contain_function(request.function_signature):
        return ListFunctionImplementationsResponse(
            success=False,
            error_message=f"Function '{request.function_signature}' not found in contract '{request.contract_key.contract_name}'"
        )
    
    # Find all implementing contracts
    implementing_contracts = project_facts.resolve_function_implementations(
        contract_model,
        request.function_signature
    )
    
    return ListFunctionImplementationsResponse(
        success=True,
        implementing_contracts=implementing_contracts
    )

