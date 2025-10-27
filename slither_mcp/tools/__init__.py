"""MCP tools for Slither analysis.

This module provides a unified import point for all MCP tools.
Each tool has its own module with request/response models and implementation.
"""

# Query tools - for browsing and filtering data
from slither_mcp.tools.list_contracts import (
    ContractInfo,
    ListContractsRequest,
    ListContractsResponse,
    list_contracts,
)
from slither_mcp.tools.get_contract import (
    GetContractRequest,
    GetContractResponse,
    get_contract,
)
from slither_mcp.tools.list_functions import (
    FunctionInfo,
    ListFunctionsRequest,
    ListFunctionsResponse,
    list_functions,
)

# Analysis tools - for deep analysis
from slither_mcp.tools.list_function_callees import (
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    list_function_callees,
)
from slither_mcp.tools.get_inherited_contracts import (
    InheritanceNode,
    GetInheritedContractsRequest,
    GetInheritedContractsResponse,
    get_inherited_contracts,
)
from slither_mcp.tools.get_derived_contracts import (
    DerivedNode,
    GetDerivedContractsRequest,
    GetDerivedContractsResponse,
    get_derived_contracts,
)
from slither_mcp.tools.list_function_implementations import (
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    list_function_implementations,
)
from slither_mcp.tools.list_function_callers import (
    FunctionCallers,
    FunctionCallersRequest,
    FunctionCallersResponse,
    list_function_callers,
)
from slither_mcp.tools.get_contract_source import (
    GetContractSourceRequest,
    GetContractSourceResponse,
    get_contract_source,
)
from slither_mcp.tools.get_function_source import (
    GetFunctionSourceRequest,
    GetFunctionSourceResponse,
    get_function_source,
)

__all__ = [
    # Query tools
    "ContractInfo",
    "ListContractsRequest",
    "ListContractsResponse",
    "list_contracts",
    "GetContractRequest",
    "GetContractResponse",
    "get_contract",
    "GetContractSourceRequest",
    "GetContractSourceResponse",
    "get_contract_source",
    "GetFunctionSourceRequest",
    "GetFunctionSourceResponse",
    "get_function_source",
    "FunctionInfo",
    "ListFunctionsRequest",
    "ListFunctionsResponse",
    "list_functions",
    # Analysis tools
    "FunctionCalleesRequest",
    "FunctionCalleesResponse",
    "list_function_callees",
    "InheritanceNode",
    "GetInheritedContractsRequest",
    "GetInheritedContractsResponse",
    "get_inherited_contracts",
    "DerivedNode",
    "GetDerivedContractsRequest",
    "GetDerivedContractsResponse",
    "get_derived_contracts",
    "ListFunctionImplementationsRequest",
    "ListFunctionImplementationsResponse",
    "list_function_implementations",
    "FunctionCallers",
    "FunctionCallersRequest",
    "FunctionCallersResponse",
    "list_function_callers",
]

