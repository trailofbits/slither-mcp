"""Tool for listing function callers."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.types import (
    FunctionKey,
    JSONStringTolerantModel,
    ProjectFacts,
    QueryContext,
    normalize_signature,
)


class FunctionCallers(BaseModel):
    """Grouped function callers by call type."""

    internal_callers: Annotated[
        list[FunctionKey], Field(description="Functions that call the target as an internal call")
    ]
    external_callers: Annotated[
        list[FunctionKey], Field(description="Functions that call the target as an external call")
    ]
    library_callers: Annotated[
        list[FunctionKey], Field(description="Functions that call the target as a library call")
    ]


class FunctionCallersRequest(JSONStringTolerantModel):
    """Request to list callers for a function."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    function_key: Annotated[
        FunctionKey,
        Field(description="The function key identifying the function and its context."),
    ]
    include_query_context: Annotated[
        bool, Field(description="Include query_context in response (default false to reduce size)")
    ] = False


class FunctionCallersResponse(BaseModel):
    """Response containing function callers grouped by call type."""

    success: bool
    query_context: QueryContext | None = None
    callers: FunctionCallers | None = None
    error_message: str | None = None


def list_function_callers(
    request: FunctionCallersRequest, project_facts: ProjectFacts
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

    # Only include query_context if requested
    response_qc = qc if request.include_query_context else None

    if err is not None:
        return FunctionCallersResponse(success=False, query_context=response_qc, error_message=err)

    # Construct the target function's external signature format
    # This is the format used in FunctionCallees lists (e.g., "ContractName.signature()")
    target_ext_sig = f"{request.function_key.contract_name}.{request.function_key.signature}"
    # Create normalized version for flexible matching
    normalized_target = normalize_signature(target_ext_sig)

    # Use sets to avoid duplicates
    internal_callers_set: set[FunctionKey] = set()
    external_callers_set: set[FunctionKey] = set()
    library_callers_set: set[FunctionKey] = set()

    def _matches_target(callee: str) -> bool:
        """Check if a callee matches the target using normalized comparison."""
        if callee == target_ext_sig:
            return True
        return normalize_signature(callee) == normalized_target

    # Loop through all contracts and their functions
    for contract_key, contract_model in project_facts.contracts.items():
        # Check both declared and inherited functions
        all_functions = {**contract_model.functions_declared, **contract_model.functions_inherited}

        for func_sig, func_model in all_functions.items():
            # Create the FunctionKey for this potential caller
            caller_key = FunctionKey(
                signature=func_sig, contract_name=contract_key.contract_name, path=contract_key.path
            )

            # Check if target appears in this function's callees (with normalized matching)
            if any(_matches_target(c) for c in func_model.callees.internal_callees):
                internal_callers_set.add(caller_key)

            if any(_matches_target(c) for c in func_model.callees.external_callees):
                external_callers_set.add(caller_key)

            if any(_matches_target(c) for c in func_model.callees.library_callees):
                library_callers_set.add(caller_key)

    # Convert sets to lists for response
    callers = FunctionCallers(
        internal_callers=list(internal_callers_set),
        external_callers=list(external_callers_set),
        library_callers=list(library_callers_set),
    )

    return FunctionCallersResponse(success=True, query_context=response_qc, callers=callers)
