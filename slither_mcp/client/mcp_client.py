"""Typed MCP client wrapper for Slither MCP server."""

import asyncio
import json
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import all request/response types from slither-mcp
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

# Also import core types that might be needed
from slither_mcp.types import (
    ContractKey,
    ContractModel,
    FunctionModel,
    ProjectFacts,
)


class SlitherMCPClient:
    """
    Typed wrapper around the Slither MCP server.
    
    This client provides type-safe access to all Slither MCP tools,
    automatically handling serialization/deserialization of Pydantic models.
    """
    
    def __init__(self):
        """Initialize the MCP client (not yet connected)."""
        self._session: ClientSession | None = None
        self._read = None
        self._write = None
        self._process = None
        self._project_path: str | None = None
        self._stdio_context = None
    
    async def connect(self, project_path: str, use_cache: bool = True) -> None:
        """
        Connect to the Slither MCP server for the given project.
        
        Args:
            project_path: Path to the Solidity project to analyze
            use_cache: Whether to use cached artifacts if available
            
        Note:
            ClientSession MUST be used as an async context manager to start
            the _receive_loop task. Without this, messages won't be routed properly.
        """
        self._project_path = os.path.abspath(project_path)
        
        # Determine the command to run the MCP server
        # We'll use 'uv run' to execute the slither-mcp script
        command = "uv"
        args = ["run", "slither-mcp", self._project_path]
        if use_cache:
            args.append("--use-cache")
        
        # Create server parameters
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None,  # Inherit environment
        )
        
        # Connect via stdio - use async with to enter the context manager
        self._stdio_context = stdio_client(server_params)
        self._read, self._write = await self._stdio_context.__aenter__()
        
        # Create session - MUST use as async context manager!
        self._session = ClientSession(self._read, self._write)
        await self._session.__aenter__()  # Start the receive loop
        
        # Initialize the session
        await self._session.initialize()
    
    async def close(self) -> None:
        """Close the MCP client connection."""
        if self._session:
            # Properly exit the session context manager
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors
            self._session = None
        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors
            self._stdio_context = None
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    def _ensure_connected(self) -> None:
        """Ensure the client is connected."""
        if not self._session:
            raise RuntimeError("MCP client is not connected. Call connect() first.")
    
    async def _call_tool(
        self,
        tool_name: str,
        request: Any,
        response_type: type
    ) -> Any:
        """
        Call an MCP tool with automatic serialization/deserialization.
        
        Args:
            tool_name: Name of the MCP tool to call
            request: Request object (Pydantic model)
            response_type: Expected response type (Pydantic model class)
            
        Returns:
            Response object (Pydantic model instance)
        """
        self._ensure_connected()
        
        # Serialize request to dict - nest under 'request' key to match FastMCP tool signature
        # FastMCP expects parameters to match the function signature exactly
        request_dict = {"request": request.model_dump(mode='json')}
        
        # Call the tool
        result = await self._session.call_tool(tool_name, arguments=request_dict)
        
        # The result should have a 'content' field with the response
        if not result.content:
            raise RuntimeError(f"Tool {tool_name} returned no content")
        
        # Extract the JSON from the response
        # MCP returns content as a list of TextContent objects
        response_json = None
        for content_item in result.content:
            if hasattr(content_item, 'text'):
                response_json = json.loads(content_item.text)
                break
        
        if response_json is None:
            raise RuntimeError(f"Tool {tool_name} returned unexpected content format")
        
        # Deserialize to Pydantic model
        return response_type.model_validate(response_json)
    
    # Query Tools
    
    async def list_contracts(
        self,
        request: ListContractsRequest
    ) -> ListContractsResponse:
        """
        List all contracts with optional filters.
        
        Args:
            request: Request with filter criteria
            
        Returns:
            Response containing matching contracts
        """
        return await self._call_tool("list_contracts", request, ListContractsResponse)
    
    async def get_contract(
        self,
        request: GetContractRequest
    ) -> GetContractResponse:
        """
        Get detailed information about a specific contract.
        
        Args:
            request: Request with contract key
            
        Returns:
            Response with contract details
        """
        return await self._call_tool("get_contract", request, GetContractResponse)
    
    async def get_contract_source(
        self,
        request: GetContractSourceRequest
    ) -> GetContractSourceResponse:
        """
        Get the full source code of the file where a contract is implemented.
        
        Args:
            request: Request with contract key
            
        Returns:
            Response with source code and file path
        """
        return await self._call_tool("get_contract_source", request, GetContractSourceResponse)
    
    async def get_function_source(
        self,
        request: GetFunctionSourceRequest
    ) -> GetFunctionSourceResponse:
        """
        Get the source code of a specific function.
        
        Args:
            request: Request with function key
            
        Returns:
            Response with function source code, file path, and line numbers
        """
        return await self._call_tool("get_function_source", request, GetFunctionSourceResponse)
    
    async def list_functions(
        self,
        request: ListFunctionsRequest
    ) -> ListFunctionsResponse:
        """
        List functions with optional filters.
        
        Args:
            request: Request with filter criteria
            
        Returns:
            Response containing matching functions
        """
        return await self._call_tool("list_functions", request, ListFunctionsResponse)
    
    # Analysis Tools
    
    async def function_callees(
        self,
        request: FunctionCalleesRequest
    ) -> FunctionCalleesResponse:
        """
        Get the functions called by a specific function.
        
        Args:
            request: Request with function signature and context
            
        Returns:
            Response with internal, external, and library callees
        """
        return await self._call_tool("function_callees", request, FunctionCalleesResponse)
    
    async def function_callers(
        self,
        request: FunctionCallersRequest
    ) -> FunctionCallersResponse:
        """
        Get all functions that call the target function, grouped by call type.
        
        Args:
            request: Request with function key
            
        Returns:
            Response with internal, external, and library callers
        """
        return await self._call_tool("function_callers", request, FunctionCallersResponse)
    
    async def get_inherited_contracts(
        self,
        request: GetInheritedContractsRequest
    ) -> GetInheritedContractsResponse:
        """
        Get the inherited contracts for a contract.
        
        Args:
            request: Request with contract key
            
        Returns:
            Response with inheritance tree
        """
        return await self._call_tool("get_inherited_contracts", request, GetInheritedContractsResponse)
    
    async def get_derived_contracts(
        self,
        request: GetDerivedContractsRequest
    ) -> GetDerivedContractsResponse:
        """
        Get the derived contracts for a contract (contracts that inherit from it).
        
        Args:
            request: Request with contract key
            
        Returns:
            Response with derived contracts tree
        """
        return await self._call_tool("get_derived_contracts", request, GetDerivedContractsResponse)
    
    async def list_function_implementations(
        self,
        request: ListFunctionImplementationsRequest
    ) -> ListFunctionImplementationsResponse:
        """
        Find all contracts that implement a specific function.
        
        Args:
            request: Request with contract key and function signature
            
        Returns:
            Response with implementing contracts
        """
        return await self._call_tool("list_function_implementations", request, ListFunctionImplementationsResponse)
    
    # Helper methods for common patterns
    
    async def get_all_contracts(self) -> list[ContractModel]:
        """
        Get all contracts in the project.
        
        Returns:
            List of all contract models
        """
        request = ListContractsRequest(filter_type="all")
        response = await self.list_contracts(request)
        
        if not response.success or not response.contracts:
            return []
        
        # Get full contract details for each
        contracts = []
        for contract_info in response.contracts:
            contract_request = GetContractRequest(
                contract_key=contract_info.key,
                include_functions=True
            )
            contract_response = await self.get_contract(contract_request)
            if contract_response.success and contract_response.contract:
                contracts.append(contract_response.contract)
        
        return contracts
    
    async def get_project_facts(self) -> ProjectFacts:
        """
        Build a ProjectFacts object from the MCP server data.
        
        This mimics the old build_project_facts() function but uses MCP.
        
        Returns:
            ProjectFacts with all contract data
        """
        # Get all contracts
        request = ListContractsRequest(filter_type="all")
        response = await self.list_contracts(request)
        
        if not response.success or not response.contracts:
            return ProjectFacts(contracts={}, project_dir=self._project_path or "")
        
        # Build contracts dict
        contracts = {}
        for contract_info in response.contracts:
            # Get full contract details
            contract_request = GetContractRequest(
                contract_key=contract_info.key,
                include_functions=True
            )
            contract_response = await self.get_contract(contract_request)
            if contract_response.success and contract_response.contract:
                contracts[contract_info.key] = contract_response.contract
        
        return ProjectFacts(
            contracts=contracts,
            project_dir=self._project_path or ""
        )

