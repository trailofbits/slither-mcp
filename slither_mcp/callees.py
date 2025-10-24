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

    return FunctionCallees(
        internal_callees=list(set(internal)),
        library_callees=list(set(library)),
        external_callees=list(set(external)),
        has_low_level_calls=True if len(function_contract.low_level_calls) else False,
    )

