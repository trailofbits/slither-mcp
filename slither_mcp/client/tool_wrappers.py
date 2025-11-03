"""MCP-based tool wrappers for pydantic-ai agents.

This module provides simple wrappers around SlitherMCPClient methods to make them
compatible with pydantic-ai agents. All types are directly from slither-mcp.

DEPRECATED: These functions are deprecated. Use the create_*_tool() methods on
SlitherMCPClient directly instead. For example:
    client = SlitherMCPClient("/path/to/project")
    await client.connect()
    tool = client.create_list_contracts_tool()
"""

import warnings
from slither_mcp.client.mcp_client import SlitherMCPClient

# Re-export MCP types for backward compatibility
from slither_mcp.tools import (
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
    # Query tools
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
    # Analysis tools
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
    # Tool creators
    "create_list_contracts_tool",
    "create_get_contract_tool",
    "create_get_contract_source_tool",
    "create_get_function_source_tool",
    "create_list_functions_tool",
    "create_function_callees_tool",
    "create_function_callers_tool",
    "create_get_inherited_contracts_tool",
    "create_get_derived_contracts_tool",
    "create_function_implementations_tool",
]


# Query Tools

def create_list_contracts_tool(mcp_client: SlitherMCPClient):
    """
    Create a list_contracts tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_list_contracts_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_list_contracts_tool() is deprecated. Use mcp_client.create_list_contracts_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_list_contracts_tool()


def create_get_contract_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_contract tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_get_contract_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_get_contract_tool() is deprecated. Use mcp_client.create_get_contract_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_get_contract_tool()


def create_get_contract_source_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_contract_source tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_get_contract_source_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_get_contract_source_tool() is deprecated. Use mcp_client.create_get_contract_source_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_get_contract_source_tool()


def create_get_function_source_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_function_source tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_get_function_source_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_get_function_source_tool() is deprecated. Use mcp_client.create_get_function_source_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_get_function_source_tool()


def create_list_functions_tool(mcp_client: SlitherMCPClient):
    """
    Create a list_functions tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_list_functions_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_list_functions_tool() is deprecated. Use mcp_client.create_list_functions_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_list_functions_tool()


# Analysis Tools

def create_function_callees_tool(mcp_client: SlitherMCPClient):
    """
    Create a function callees tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_function_callees_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_function_callees_tool() is deprecated. Use mcp_client.create_function_callees_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_function_callees_tool()


def create_function_callers_tool(mcp_client: SlitherMCPClient):
    """
    Create a function callers tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_function_callers_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_function_callers_tool() is deprecated. Use mcp_client.create_function_callers_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_function_callers_tool()


def create_get_inherited_contracts_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_inherited_contracts tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_get_inherited_contracts_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_get_inherited_contracts_tool() is deprecated. Use mcp_client.create_get_inherited_contracts_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_get_inherited_contracts_tool()


def create_get_derived_contracts_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_derived_contracts tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_get_derived_contracts_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_get_derived_contracts_tool() is deprecated. Use mcp_client.create_get_derived_contracts_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_get_derived_contracts_tool()


def create_function_implementations_tool(mcp_client: SlitherMCPClient):
    """
    Create a function implementations tool from the MCP client.
    
    DEPRECATED: Use mcp_client.create_function_implementations_tool() instead.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    warnings.warn(
        "create_function_implementations_tool() is deprecated. Use mcp_client.create_function_implementations_tool() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return mcp_client.create_function_implementations_tool()

