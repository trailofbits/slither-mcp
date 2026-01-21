"""Tool for getting the full source code of a contract's file."""

import os
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from slither_mcp.types import (
    ContractKey,
    JSONStringTolerantModel,
    PathTraversalError,
    ProjectFacts,
    validate_path_within_project,
)


class GetContractSourceRequest(JSONStringTolerantModel):
    """Request to get the full source code of a contract's file."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: ContractKey
    max_lines: Annotated[
        int | None,
        Field(description="Maximum number of lines to return (default 500, None for unlimited)"),
    ] = 500
    start_line: Annotated[
        int | None,
        Field(description="Starting line number (1-indexed, default 1)"),
    ] = None

    @field_validator("max_lines")
    @classmethod
    def validate_max_lines(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("max_lines must be >= 1")
        return v

    @field_validator("start_line")
    @classmethod
    def validate_start_line(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("start_line must be >= 1")
        return v


class GetContractSourceResponse(BaseModel):
    """Response containing the contract's source file content."""

    success: bool
    source_code: str | None = None
    file_path: Annotated[
        str | None, Field(description="File path relative to project directory")
    ] = None
    total_lines: Annotated[
        int | None, Field(description="Total number of lines in the source file")
    ] = None
    returned_lines: Annotated[
        tuple[int, int] | None,
        Field(description="Line range returned (start, end) - 1-indexed, inclusive"),
    ] = None
    truncated: Annotated[
        bool, Field(description="True if the source was truncated due to max_lines limit")
    ] = False
    error_message: str | None = None


def get_contract_source(
    request: GetContractSourceRequest, project_facts: ProjectFacts
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
            error_message=(
                f"Contract not found: '{request.contract_key.contract_name}' "
                f"at '{request.contract_key.path}'. "
                f"Use search_contracts or list_contracts to find available contracts."
            ),
        )

    project_path = request.path
    if not os.path.exists(project_path):
        return GetContractSourceResponse(
            success=False, error_message=f"Project does not exist on path: {project_path}"
        )

    # Get the file path and validate it's within project directory
    file_path_rel = contract_model.path
    try:
        file_path = validate_path_within_project(project_path, file_path_rel)
    except PathTraversalError as e:
        return GetContractSourceResponse(success=False, error_message=str(e))

    # Check if file exists
    if not os.path.exists(file_path):
        return GetContractSourceResponse(
            success=False, error_message=f"Source file not found: {file_path}"
        )

    # Read the source code
    try:
        with open(file_path, encoding="utf-8") as f:
            all_lines = f.readlines()

        total_lines = len(all_lines)

        # Handle empty file case
        if total_lines == 0:
            return GetContractSourceResponse(
                success=True,
                source_code="",
                file_path=file_path_rel,
                total_lines=0,
                returned_lines=(1, 0),
                truncated=False,
            )

        # Calculate line range (convert to 0-indexed for slicing)
        start_idx = (request.start_line or 1) - 1
        if start_idx < 0:
            start_idx = 0
        if start_idx >= total_lines:
            return GetContractSourceResponse(
                success=False,
                error_message=f"start_line {request.start_line} exceeds file length ({total_lines} lines)",
            )

        # Determine end index based on max_lines
        if request.max_lines is not None:
            end_idx = min(start_idx + request.max_lines, total_lines)
        else:
            end_idx = total_lines

        # Check if truncation occurred
        truncated = end_idx < total_lines

        # Extract the lines
        selected_lines = all_lines[start_idx:end_idx]
        source_code = "".join(selected_lines)

        # Convert back to 1-indexed for response
        returned_lines = (start_idx + 1, end_idx)

        return GetContractSourceResponse(
            success=True,
            source_code=source_code,
            file_path=file_path_rel,
            total_lines=total_lines,
            returned_lines=returned_lines,
            truncated=truncated,
        )
    except Exception as e:
        return GetContractSourceResponse(
            success=False, error_message=f"Error reading source file: {str(e)}"
        )
