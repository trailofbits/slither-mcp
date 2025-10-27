"""Tool for listing function callers."""

from typing import Annotated
from pydantic import BaseModel, Field

from slither_mcp.types import (
    FunctionKey,
    ProjectFacts,
    QueryContext,
)


class FunctionCallers(BaseModel):
    """Grouped function callers by call type."""
    internal_callers: Annotated[
        list[FunctionKey],
        Field(description="Functions that call the target as an internal call")
    ]
    external_callers: Annotated[
        list[FunctionKey],
        Field(description="Functions that call the target as an external call")
    ]
    library_callers: Annotated[
        list[FunctionKey],
        Field(description="Functions that call the target as a library call")
    ]


class FunctionCallersRequest(BaseModel):
    """Request to list callers for a function."""
    function_key: Annotated[
        FunctionKey,
        Field(
            description="The function key identifying the function and its context."
        ),
    ]


class FunctionCallersResponse(BaseModel):
    """Response containing function callers grouped by call type."""
    success: bool
    query_context: QueryContext
    callers: FunctionCallers | None = None
    error_message: str | None = None


def list_function_callers(
    request: FunctionCallersRequest,
    project_facts: ProjectFacts
) -> FunctionCallersResponse:
    """
    List all functions that call the target function, grouped by call type.
    
    This tool finds all functions in the project that may call the target function
    by checking each function's callees lists (internal, external, library).
    
    Args:
        request: The function callers request containing the function key
        project_facts: The project facts containing contract data
        
    Returns:
        FunctionCallersResponse with callers grouped by type or error message
    """
    qc, contract_model, function_model, err = project_facts.resolve_function_by_key(
        request.function_key
    )

    if err is not None:
        return FunctionCallersResponse(
            success=False, query_context=qc, error_message=err
        )

    # Construct the target function's external signature format
    # This is the format used in FunctionCallees lists (e.g., "ContractName.signature()")
    target_ext_sig = f"{request.function_key.contract_name}.{request.function_key.signature}"

    # Use sets to avoid duplicates
    internal_callers_set: set[FunctionKey] = set()
    external_callers_set: set[FunctionKey] = set()
    library_callers_set: set[FunctionKey] = set()

    # Loop through all contracts and their functions
    for contract_key, contract_model in project_facts.contracts.items():
        # Check both declared and inherited functions
        all_functions = {
            **contract_model.functions_declared,
            **contract_model.functions_inherited
        }
        
        for func_sig, func_model in all_functions.items():
            # Create the FunctionKey for this potential caller
            caller_key = FunctionKey(
                signature=func_sig,
                contract_name=contract_key.contract_name,
                path=contract_key.path
            )
            
            # Check if target appears in this function's callees
            if target_ext_sig in func_model.callees.internal_callees:
                internal_callers_set.add(caller_key)
            
            if target_ext_sig in func_model.callees.external_callees:
                external_callers_set.add(caller_key)
            
            if target_ext_sig in func_model.callees.library_callees:
                library_callers_set.add(caller_key)

    # Convert sets to lists for response
    callers = FunctionCallers(
        internal_callers=list(internal_callers_set),
        external_callers=list(external_callers_set),
        library_callers=list(library_callers_set)
    )

    return FunctionCallersResponse(
        success=True,
        query_context=qc,
        callers=callers
    )

