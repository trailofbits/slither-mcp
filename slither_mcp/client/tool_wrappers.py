"""MCP-based tool wrappers for pydantic-ai agents.

This module provides simple wrappers around SlitherMCPClient methods to make them
compatible with pydantic-ai agents. All types are directly from slither-mcp.
"""

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
    
    Returns a wrapper function that calls mcp_client.list_contracts() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def list_contracts(request: ListContractsRequest) -> ListContractsResponse:
        """List all contracts with optional filters."""
        return await mcp_client.list_contracts(request)
    
    return list_contracts


def create_get_contract_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_contract tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.get_contract() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def get_contract(request: GetContractRequest) -> GetContractResponse:
        """Get detailed information about a specific contract."""
        return await mcp_client.get_contract(request)
    
    return get_contract


def create_get_contract_source_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_contract_source tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.get_contract_source() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def get_contract_source(request: GetContractSourceRequest) -> GetContractSourceResponse:
        """Get the full source code of the file where a contract is implemented."""
        return await mcp_client.get_contract_source(request)
    
    return get_contract_source


def create_get_function_source_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_function_source tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.get_function_source() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def get_function_source(request: GetFunctionSourceRequest) -> GetFunctionSourceResponse:
        """Get the source code of a specific function."""
        return await mcp_client.get_function_source(request)
    
    return get_function_source


def create_list_functions_tool(mcp_client: SlitherMCPClient):
    """
    Create a list_functions tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.list_functions() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def list_functions(request: ListFunctionsRequest) -> ListFunctionsResponse:
        """List functions with optional filters."""
        return await mcp_client.list_functions(request)
    
    return list_functions


# Analysis Tools

def create_function_callees_tool(mcp_client: SlitherMCPClient):
    """
    Create a function callees tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.function_callees() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def function_callees(request: FunctionCalleesRequest) -> FunctionCalleesResponse:
        """Get the internal, external, and library callees for a function."""
        return await mcp_client.function_callees(request)
    
    return function_callees


def create_function_callers_tool(mcp_client: SlitherMCPClient):
    """
    Create a function callers tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.function_callers() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def function_callers(request: FunctionCallersRequest) -> FunctionCallersResponse:
        """Get all functions that call the target function, grouped by call type."""
        return await mcp_client.function_callers(request)
    
    return function_callers


def create_get_inherited_contracts_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_inherited_contracts tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.get_inherited_contracts() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def get_inherited_contracts(
        request: GetInheritedContractsRequest
    ) -> GetInheritedContractsResponse:
        """Get the inherited contracts for a contract."""
        return await mcp_client.get_inherited_contracts(request)
    
    return get_inherited_contracts


def create_get_derived_contracts_tool(mcp_client: SlitherMCPClient):
    """
    Create a get_derived_contracts tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.get_derived_contracts() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def get_derived_contracts(
        request: GetDerivedContractsRequest
    ) -> GetDerivedContractsResponse:
        """Get the derived contracts for a contract (contracts that inherit from it)."""
        return await mcp_client.get_derived_contracts(request)
    
    return get_derived_contracts


def create_function_implementations_tool(mcp_client: SlitherMCPClient):
    """
    Create a function implementations tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.list_function_implementations()
    with proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def list_function_implementations(
        request: ListFunctionImplementationsRequest
    ) -> ListFunctionImplementationsResponse:
        """List all contracts that implement a specific function signature."""
        return await mcp_client.list_function_implementations(request)
    
    return list_function_implementations

