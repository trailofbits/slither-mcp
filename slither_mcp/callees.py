"""Function callees extraction from Slither."""

from slither.slithir.operations import InternalCall, LibraryCall
from slither.slithir.operations.high_level_call import HighLevelCall

from slither_mcp.types import FunctionCallees


def get_callees(function_contract) -> FunctionCallees:
    """
    Extract function callees from a Slither FunctionContract.

    Args:
        function_contract: Slither FunctionContract object

    Returns:
        FunctionCallees with internal, external, and library callees
    """
    internal = [
        ic.function.canonical_name
        for ic in function_contract.internal_calls
        if isinstance(ic, InternalCall)
    ]
    library = [
        lc.function.canonical_name
        for lc in function_contract.library_calls
        if isinstance(lc, LibraryCall)
    ]
    external = [
        ec.function.canonical_name
        for (contract, ec) in function_contract.high_level_calls
        if isinstance(ec, HighLevelCall)
    ]

    # Deduplicate: Slither may emit both HighLevelCall and LibraryCall for the same call.
    # Library calls should not also appear in external calls.
    internal_set = set(internal)
    library_set = set(library)
    external_set = set(external) - library_set  # Remove overlap with library calls

    return FunctionCallees(
        internal_callees=list(internal_set),
        library_callees=list(library_set),
        external_callees=list(external_set),
        has_low_level_calls=bool(function_contract.low_level_calls),
    )
