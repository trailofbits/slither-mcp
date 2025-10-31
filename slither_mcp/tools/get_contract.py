"""Tool for getting detailed contract information."""

from pydantic import BaseModel

from slither_mcp.types import (
    ContractKey,
    ContractModel,
    ProjectFacts,
    JSONStringTolerantModel,
)


class GetContractRequest(JSONStringTolerantModel):
    """Request to get detailed contract information."""
    path: str
    contract_key: ContractKey
    include_functions: bool = True


class GetContractResponse(BaseModel):
    """Response containing contract details."""
    success: bool
    contract: ContractModel | None = None
    error_message: str | None = None


def get_contract(
    request: GetContractRequest,
    project_facts: ProjectFacts
) -> GetContractResponse:
    """
    Get detailed contract information.
    
    Args:
        request: The get contract request
        project_facts: The project facts containing contract data
        
    Returns:
        GetContractResponse with contract details or error
    """
    contract_model = project_facts.contracts.get(request.contract_key)
    
    if contract_model is None:
        return GetContractResponse(
            success=False,
            error_message=f"Contract not found: {request.contract_key.contract_name}"
        )
    
    # If not including functions, create a copy without them
    if not request.include_functions:
        # Create a minimal contract model without functions
        contract_model = ContractModel(
            name=contract_model.name,
            key=contract_model.key,
            path=contract_model.path,
            is_abstract=contract_model.is_abstract,
            is_fully_implemented=contract_model.is_fully_implemented,
            is_interface=contract_model.is_interface,
            is_library=contract_model.is_library,
            directly_inherits=contract_model.directly_inherits,
            scopes=contract_model.scopes,
            functions_declared={},
            functions_inherited={}
        )
    
    return GetContractResponse(
        success=True,
        contract=contract_model
    )

