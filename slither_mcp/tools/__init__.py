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
from slither_mcp.tools.get_inheritance_hierarchy import (
    InheritanceNode,
    InheritanceHierarchyRequest,
    InheritanceHierarchyResponse,
    get_inheritance_hierarchy,
)
from slither_mcp.tools.list_function_implementations import (
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    list_function_implementations,
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
    "FunctionInfo",
    "ListFunctionsRequest",
    "ListFunctionsResponse",
    "list_functions",
    # Analysis tools
    "FunctionCalleesRequest",
    "FunctionCalleesResponse",
    "list_function_callees",
    "InheritanceNode",
    "InheritanceHierarchyRequest",
    "InheritanceHierarchyResponse",
    "get_inheritance_hierarchy",
    "ListFunctionImplementationsRequest",
    "ListFunctionImplementationsResponse",
    "list_function_implementations",
]

