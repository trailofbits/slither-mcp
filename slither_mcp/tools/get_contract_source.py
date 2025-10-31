"""Tool for getting the full source code of a contract's file."""

import os
from pydantic import BaseModel

from slither_mcp.types import (
    ContractKey,
    ProjectFacts,
    JSONStringTolerantModel,
)


class GetContractSourceRequest(JSONStringTolerantModel):
    """Request to get the full source code of a contract's file."""
    path: str
    contract_key: ContractKey


class GetContractSourceResponse(BaseModel):
    """Response containing the contract's source file content."""
    success: bool
    source_code: str | None = None
    file_path: str | None = None
    error_message: str | None = None


def get_contract_source(
    request: GetContractSourceRequest,
    project_facts: ProjectFacts
) -> GetContractSourceResponse:
    """
    Get the full source code of the file where a contract is implemented.
    
    Args:
        request: The get contract source request with contract key
        project_facts: The project facts containing contract data
        
    Returns:
        GetContractSourceResponse with source code or error
    """
    # Look up the contract
    contract_model = project_facts.contracts.get(request.contract_key)
    
    if contract_model is None:
        return GetContractSourceResponse(
            success=False,
            error_message=f"Contract not found: {request.contract_key.contract_name}"
        )
    
    # Get the file path from the contract model
    file_path = contract_model.path
    
    # Check if file exists
    if not os.path.exists(file_path):
        return GetContractSourceResponse(
            success=False,
            error_message=f"Source file not found: {file_path}"
        )
    
    # Read the source code
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        return GetContractSourceResponse(
            success=True,
            source_code=source_code,
            file_path=file_path
        )
    except Exception as e:
        return GetContractSourceResponse(
            success=False,
            error_message=f"Error reading source file: {str(e)}"
        )

