"""Client utilities for connecting to Slither MCP servers.

This module provides a typed client wrapper for interacting with
Slither MCP servers programmatically.
"""

from slither_mcp.client.mcp_client import SlitherMCPClient
from slither_mcp.tools import (
    # Analysis types
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    FunctionCallersRequest,
    FunctionCallersResponse,
    GetContractRequest,
    GetContractResponse,
    GetContractSourceRequest,
    GetContractSourceResponse,
    GetDerivedContractsRequest,
    GetDerivedContractsResponse,
    GetFunctionSourceRequest,
    GetFunctionSourceResponse,
    GetInheritedContractsRequest,
    GetInheritedContractsResponse,
    # Query types
    ListContractsRequest,
    ListContractsResponse,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    ListFunctionsRequest,
    ListFunctionsResponse,
)

# Re-export common types for convenience
from slither_mcp.tools.list_contracts import ContractInfo
from slither_mcp.tools.list_functions import FunctionInfo

__all__ = [
    "SlitherMCPClient",
    # Info types (for auto-paginated helpers)
    "ContractInfo",
    "FunctionInfo",
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
