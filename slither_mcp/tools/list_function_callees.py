"""Tool for listing function callees."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.types import (
    FunctionCallees,
    FunctionKey,
    JSONStringTolerantModel,
    ProjectFacts,
    QueryContext,
)


class FunctionCalleesRequest(JSONStringTolerantModel):
    """Request to list callees for a function."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    function_key: Annotated[
        FunctionKey,
        Field(description="The function key identifying the function and its context."),
    ]
    include_query_context: Annotated[
        bool, Field(description="Include query_context in response (default false to reduce size)")
    ] = False


class FunctionCalleesResponse(BaseModel):
    """Response containing function callees."""

    success: bool
    query_context: QueryContext | None = None
    callees: FunctionCallees | None = None
    error_message: str | None = None


def list_function_callees(
    request: FunctionCalleesRequest, project_facts: ProjectFacts
) -> FunctionCalleesResponse:
    """
    List the internal, external, and library callees for a function.

    Args:
        request: The function callees request containing the function key
        project_facts: The project facts containing contract data

    Returns:
        FunctionCalleesResponse with callees or error message
    """
    qc, _, function_model, err = project_facts.resolve_function_by_key(request.function_key)

    # Only include query_context if requested
    response_qc = qc if request.include_query_context else None

    if err is not None or function_model is None:
        return FunctionCalleesResponse(
            success=False, query_context=response_qc, error_message=err or "Function not found"
        )

    return FunctionCalleesResponse(
        success=True, query_context=response_qc, callees=function_model.callees
    )
