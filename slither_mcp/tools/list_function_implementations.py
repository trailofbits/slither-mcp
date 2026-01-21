"""Tool for listing contracts that implement a specific function."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    ContractKey,
    FuncSig,
    ProjectFacts,
)


class ImplementationInfo(BaseModel):
    """Lightweight summary of an implementing contract."""

    contract_key: Annotated[ContractKey, Field(description="The contract key")]
    is_abstract: Annotated[bool, Field(description="Whether the contract is abstract")]
    is_interface: Annotated[bool, Field(description="Whether the contract is an interface")]
    function_visibility: Annotated[
        str, Field(description="Visibility of the function implementation")
    ]
    function_modifiers: Annotated[
        list[str], Field(description="Custom modifiers decorating the function")
    ]


class ListFunctionImplementationsRequest(PaginatedRequest):
    """Request to find contracts implementing a function."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey,
        Field(description="The contract key (typically an abstract contract or interface)"),
    ]
    function_signature: Annotated[
        FuncSig,
        Field(
            description="The function signature to find implementations for (e.g., 'transfer(address,uint256)')"
        ),
    ]


class ListFunctionImplementationsResponse(BaseModel):
    """Response containing contracts that implement the function."""

    success: bool
    implementations: list[ImplementationInfo] | None = None
    total_count: int = 0
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def list_function_implementations(
    request: ListFunctionImplementationsRequest, project_facts: ProjectFacts
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
            error_message=(
                f"Contract not found: '{request.contract_key.contract_name}' "
                f"at '{request.contract_key.path}'. "
                f"Use search_contracts or list_contracts to find available contracts."
            ),
        )

    # Check if the function exists in the contract
    if not contract_model.does_contract_contain_function(request.function_signature):
        return ListFunctionImplementationsResponse(
            success=False,
            error_message=(
                f"Function '{request.function_signature}' not found in contract "
                f"'{request.contract_key.contract_name}'. "
                f"Use list_functions with this contract_key to see available functions, "
                f"or search_functions to find functions by pattern."
            ),
        )

    # Find all implementing contracts
    implementing_contracts = project_facts.resolve_function_implementations(
        contract_model, request.function_signature
    )

    # Convert to lightweight ImplementationInfo
    implementations = []
    for impl_contract in implementing_contracts:
        # Get the function model to extract visibility and modifiers
        func_model = impl_contract.functions_declared.get(request.function_signature)
        if func_model:
            implementations.append(
                ImplementationInfo(
                    contract_key=impl_contract.key,
                    is_abstract=impl_contract.is_abstract,
                    is_interface=impl_contract.is_interface,
                    function_visibility=func_model.visibility,
                    function_modifiers=func_model.function_modifiers,
                )
            )

    # Apply pagination
    implementations, total_count, has_more = apply_pagination(
        implementations, request.offset, request.limit
    )

    return ListFunctionImplementationsResponse(
        success=True, implementations=implementations, total_count=total_count, has_more=has_more
    )
