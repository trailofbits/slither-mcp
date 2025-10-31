"""Tool for listing function callees."""

from typing import Annotated
from pydantic import BaseModel, Field

from slither_mcp.types import (
    FunctionCallees,
    FunctionKey,
    ProjectFacts,
    QueryContext,
    JSONStringTolerantModel,
)


class FunctionCalleesRequest(JSONStringTolerantModel):
    """Request to list callees for a function."""
    path: str
    function_key: Annotated[
        FunctionKey,
        Field(
            description="The function key identifying the function and its context."
        ),
    ]


class FunctionCalleesResponse(BaseModel):
    """Response containing function callees."""
    success: bool
    query_context: QueryContext
    callees: FunctionCallees | None = None
    error_message: str | None = None


def list_function_callees(
    request: FunctionCalleesRequest,
    project_facts: ProjectFacts
) -> FunctionCalleesResponse:
    """
    List the internal, external, and library callees for a function.
    
    Args:
        request: The function callees request containing the function key
        project_facts: The project facts containing contract data
        
    Returns:
        FunctionCalleesResponse with callees or error message
    """
    qc, _, function_model, err = project_facts.resolve_function_by_key(
        request.function_key
    )

    if err is not None:
        return FunctionCalleesResponse(
            success=False, query_context=qc, error_message=err
        )

    return FunctionCalleesResponse(
        success=True, query_context=qc, callees=function_model.callees
    )

