"""Tool for finding functions with no callers (dead code)."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.constants import SPECIAL_FUNCTION_NAMES, TEST_FUNCTION_PREFIX
from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import ContractKey, FunctionKey, ProjectFacts


class DeadCodeFunction(BaseModel):
    """A function identified as potentially dead code."""

    function_key: FunctionKey
    visibility: str
    is_entry_point: Annotated[
        bool, Field(description="True if function could be called externally (public/external)")
    ]
    reason: Annotated[str, Field(description="Why this function is considered dead code")]


class FindDeadCodeRequest(PaginatedRequest):
    """Request to find dead code in the project."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Optional: limit search to a specific contract"),
    ] = None
    exclude_entry_points: Annotated[
        bool,
        Field(
            description="If true, exclude public/external functions (which may be called externally)"
        ),
    ] = True
    include_inherited: Annotated[
        bool,
        Field(description="If true, also check inherited functions"),
    ] = False


class FindDeadCodeResponse(BaseModel):
    """Response containing dead code findings."""

    success: bool
    dead_functions: list[DeadCodeFunction]
    total_count: int
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def _is_entry_point(visibility: str, func_signature: str) -> bool:
    """Check if a function is a potential entry point.

    Entry points are functions that may be called from outside the contract
    or have special meaning in the Solidity ecosystem (constructor, fallback,
    test functions, etc.).

    Args:
        visibility: Function visibility ('public', 'external', 'internal', 'private')
        func_signature: Full function signature (e.g., 'transfer(address,uint256)')

    Returns:
        True if the function is likely an entry point that shouldn't be
        flagged as dead code even if not called internally.
    """
    # Public and external functions can be called from outside
    if visibility.lower() in ("public", "external"):
        return True

    # Check for special function names
    func_name = func_signature.split("(")[0]
    if func_name in SPECIAL_FUNCTION_NAMES:
        return True

    # Test functions (starting with "test")
    if func_name.startswith(TEST_FUNCTION_PREFIX):
        return True

    return False


def _is_special_function(func_signature: str) -> bool:
    """Check if a function is a special Solidity function that shouldn't be flagged.

    Identifies functions that have special meaning in Solidity or common testing
    frameworks, and should be excluded from dead code analysis regardless of
    whether they appear to have callers.

    Args:
        func_signature: Full function signature (e.g., 'constructor()')

    Returns:
        True if the function is a special function (constructor, fallback,
        receive, setUp, run, or test* functions).
    """
    func_name = func_signature.split("(")[0]
    return func_name in SPECIAL_FUNCTION_NAMES or func_name.startswith(TEST_FUNCTION_PREFIX)


def find_dead_code(
    request: FindDeadCodeRequest, project_facts: ProjectFacts
) -> FindDeadCodeResponse:
    """
    Find functions that have no callers (potential dead code).

    This tool identifies functions that are never called from within the codebase.
    Note that public/external functions may be called from outside the project,
    so they should typically be excluded from dead code analysis.

    Args:
        request: Request with filtering options
        project_facts: The project facts containing all contract data

    Returns:
        FindDeadCodeResponse with list of dead functions
    """
    try:
        # Build set of all called function signatures
        called_functions: set[str] = set()

        for contract in project_facts.contracts.values():
            for func in contract.functions_declared.values():
                # Add internal callees
                for callee in func.callees.internal_callees:
                    called_functions.add(callee)
                # Add external callees
                for callee in func.callees.external_callees:
                    called_functions.add(callee)
                # Add library callees
                for callee in func.callees.library_callees:
                    called_functions.add(callee)

        # Find functions that are never called
        dead_functions: list[DeadCodeFunction] = []

        # Determine which contracts to search
        if request.contract_key:
            contract_model = project_facts.contracts.get(request.contract_key)
            if not contract_model:
                return FindDeadCodeResponse(
                    success=False,
                    dead_functions=[],
                    total_count=0,
                    error_message=f"Contract not found: '{request.contract_key.contract_name}' "
                    f"at '{request.contract_key.path}'",
                )
            contracts_to_check = [(request.contract_key, contract_model)]
        else:
            contracts_to_check = list(project_facts.contracts.items())

        for contract_key, contract_model in contracts_to_check:
            # Skip interfaces and libraries for dead code analysis
            if contract_model.is_interface or contract_model.is_library:
                continue

            # Check declared functions
            for sig, func in contract_model.functions_declared.items():
                # Build the external signature for matching
                ext_sig = f"{contract_key.contract_name}.{sig}"

                # Skip if this function is called
                if ext_sig in called_functions:
                    continue

                is_entry = _is_entry_point(func.visibility, sig)

                # Skip entry points if requested
                if request.exclude_entry_points and is_entry:
                    continue

                # Skip special functions (constructor, receive, fallback, etc.)
                if _is_special_function(sig):
                    continue

                # Determine reason for dead code classification
                if func.visibility.lower() in ("internal", "private"):
                    reason = "Internal/private function with no internal callers"
                else:
                    reason = "Function is never called from within the codebase"

                dead_functions.append(
                    DeadCodeFunction(
                        function_key=FunctionKey(
                            signature=sig,
                            contract_name=contract_key.contract_name,
                            path=contract_key.path,
                        ),
                        visibility=func.visibility,
                        is_entry_point=is_entry,
                        reason=reason,
                    )
                )

            # Check inherited functions if requested
            if request.include_inherited:
                for sig, func in contract_model.functions_inherited.items():
                    ext_sig = f"{contract_key.contract_name}.{sig}"

                    if ext_sig in called_functions:
                        continue

                    is_entry = _is_entry_point(func.visibility, sig)

                    if request.exclude_entry_points and is_entry:
                        continue

                    if _is_special_function(sig):
                        continue

                    dead_functions.append(
                        DeadCodeFunction(
                            function_key=FunctionKey(
                                signature=sig,
                                contract_name=contract_key.contract_name,
                                path=contract_key.path,
                            ),
                            visibility=func.visibility,
                            is_entry_point=is_entry,
                            reason="Inherited function is never called from within the codebase",
                        )
                    )

        # Apply pagination
        dead_functions, total_count, has_more = apply_pagination(
            dead_functions, request.offset, request.limit
        )

        return FindDeadCodeResponse(
            success=True,
            dead_functions=dead_functions,
            total_count=total_count,
            has_more=has_more,
        )

    except Exception as e:
        return FindDeadCodeResponse(
            success=False,
            dead_functions=[],
            total_count=0,
            error_message=f"Failed to find dead code: {e}",
        )
