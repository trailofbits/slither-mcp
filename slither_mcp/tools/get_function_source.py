"""Tool for getting the source code of a specific function."""

import os
from typing import Annotated
from pydantic import BaseModel, Field

from slither_mcp.types import (
    FunctionKey,
    ProjectFacts,
    JSONStringTolerantModel,
)


class GetFunctionSourceRequest(JSONStringTolerantModel):
    """Request to get the source code of a specific function."""
    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    function_key: FunctionKey


class GetFunctionSourceResponse(BaseModel):
    """Response containing the function's source code."""
    success: bool
    source_code: str | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    error_message: str | None = None


def get_function_source(
    request: GetFunctionSourceRequest,
    project_facts: ProjectFacts
) -> GetFunctionSourceResponse:
    """
    Get the source code of a specific function.
    
    Args:
        request: The get function source request with function key
        project_facts: The project facts containing contract and function data
        
    Returns:
        GetFunctionSourceResponse with source code or error
    """
    # Resolve the function using the FunctionKey
    query_context, contract_model, function_model, error = project_facts.resolve_function_by_key(
        request.function_key
    )
    
    if error or function_model is None:
        return GetFunctionSourceResponse(
            success=False,
            error_message=error or "Function not found"
        )
    
    # Get the file path and line numbers from the function model
    file_path = function_model.path
    line_start = function_model.line_start
    line_end = function_model.line_end
    
    # Check if file exists
    if not os.path.exists(file_path):
        return GetFunctionSourceResponse(
            success=False,
            error_message=f"Source file not found: {file_path}"
        )
    
    # Validate line numbers
    if line_start <= 0 or line_end <= 0 or line_start > line_end:
        return GetFunctionSourceResponse(
            success=False,
            error_message=f"Invalid line range: {line_start}-{line_end}"
        )
    
    # Read the source code
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract the function source (line numbers are 1-indexed)
        if line_start > len(lines) or line_end > len(lines):
            return GetFunctionSourceResponse(
                success=False,
                error_message=f"Line range {line_start}-{line_end} exceeds file length ({len(lines)} lines)"
            )
        
        source_code = ''.join(lines[line_start - 1:line_end])
        
        return GetFunctionSourceResponse(
            success=True,
            source_code=source_code,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end
        )
    except Exception as e:
        return GetFunctionSourceResponse(
            success=False,
            error_message=f"Error reading source file: {str(e)}"
        )

