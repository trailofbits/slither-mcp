"""Client utilities for connecting to Slither MCP servers.

This module provides a typed client wrapper and tool wrappers for
interacting with Slither MCP servers programmatically.
"""

from slither_mcp.client.mcp_client import SlitherMCPClient
from slither_mcp.client.tool_wrappers import (
    # Query tools
    create_list_contracts_tool,
    create_get_contract_tool,
    create_get_contract_source_tool,
    create_get_function_source_tool,
    create_list_functions_tool,
    # Analysis tools
    create_function_callees_tool,
    create_function_callers_tool,
    create_get_inherited_contracts_tool,
    create_get_derived_contracts_tool,
    create_function_implementations_tool,
    # Request/Response types
    ListContractsRequest,
    ListContractsResponse,
    GetContractRequest,
    GetContractResponse,
    GetContractSourceRequest,
    GetContractSourceResponse,
    GetFunctionSourceRequest,
    GetFunctionSourceResponse,
    ListFunctionsRequest,
    ListFunctionsResponse,
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    FunctionCallersRequest,
    FunctionCallersResponse,
    GetInheritedContractsRequest,
    GetInheritedContractsResponse,
    GetDerivedContractsRequest,
    GetDerivedContractsResponse,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
)

__all__ = [
    "SlitherMCPClient",
    # Query tool creators
    "create_list_contracts_tool",
    "create_get_contract_tool",
    "create_get_contract_source_tool",
    "create_get_function_source_tool",
    "create_list_functions_tool",
    # Analysis tool creators
    "create_function_callees_tool",
    "create_function_callers_tool",
    "create_get_inherited_contracts_tool",
    "create_get_derived_contracts_tool",
    "create_function_implementations_tool",
    # Query types
    "ListContractsRequest",
    "ListContractsResponse",
    "GetContractRequest",
    "GetContractResponse",
    "GetContractSourceRequest",
    "GetContractSourceResponse",
    "GetFunctionSourceRequest",
    "GetFunctionSourceResponse",
    "ListFunctionsRequest",
    "ListFunctionsResponse",
    # Analysis types
    "FunctionCalleesRequest",
    "FunctionCalleesResponse",
    "FunctionCallersRequest",
    "FunctionCallersResponse",
    "GetInheritedContractsRequest",
    "GetInheritedContractsResponse",
    "GetDerivedContractsRequest",
    "GetDerivedContractsResponse",
    "ListFunctionImplementationsRequest",
    "ListFunctionImplementationsResponse",
]

