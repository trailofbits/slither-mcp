"""Typed MCP client wrapper for Slither MCP server."""

import json
import logging
import os
from typing import Any, TypeVar

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

from slither_mcp.tools import (
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
    ListContractsRequest,
    ListContractsResponse,
    ListDetectorsRequest,
    ListDetectorsResponse,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    ListFunctionsRequest,
    ListFunctionsResponse,
    RunDetectorsRequest,
    RunDetectorsResponse,
)
from slither_mcp.tools.list_contracts import ContractInfo
from slither_mcp.tools.list_functions import FunctionInfo
from slither_mcp.types import (
    ContractModel,
    ProjectFacts,
)

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class SlitherMCPClient:
    """
    Typed wrapper around the Slither MCP server.

    This client provides type-safe access to all Slither MCP tools,
    automatically handling serialization/deserialization of Pydantic models.
    """

    def __init__(self, project_path: str):
        """
        Initialize the MCP client (not yet connected).

        Args:
            project_path: Path to the Solidity project to analyze. This path will be
                used for all tool calls made through this client.
        """
        self._session: ClientSession | None = None
        self._read = None
        self._write = None
        self._process = None
        self._project_path: str = os.path.abspath(project_path)
        self._stdio_context = None

    async def connect(
        self, enhanced_error_reporting: bool = False, disable_metrics: bool = False
    ) -> None:
        """
        Connect to the Slither MCP server.

        Args:
            enhanced_error_reporting: Enable Sentry error reporting for comprehensive exception monitoring.
            disable_metrics: Permanently disable metrics and error reporting.

        Note:
            ClientSession MUST be used as an async context manager to start
            the _receive_loop task. Without this, messages won't be routed properly.
        """

        # Determine the command to run the MCP server
        command = "uv"
        args = ["run", "slither-mcp"]

        # Add flags if enabled
        if disable_metrics:
            args.append("--disable-metrics")
        if enhanced_error_reporting:
            args.append("--enhanced-error-reporting")

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
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                logger.debug("Session cleanup error (ignored): %s", e)
            self._session = None
        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.debug("Stdio context cleanup error (ignored): %s", e)
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

    async def _call_tool(self, tool_name: str, request: Any, response_type: type[T]) -> T:
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
        assert self._session is not None  # Type narrowing after _ensure_connected

        # Serialize request to dict - nest under 'request' key to match FastMCP tool signature
        # FastMCP expects parameters to match the function signature exactly
        request_dict = {"request": request.model_dump(mode="json")}

        # Call the tool
        result = await self._session.call_tool(tool_name, arguments=request_dict)

        # The result should have a 'content' field with the response
        if not result.content:
            raise RuntimeError(f"Tool {tool_name} returned no content")

        # Extract the JSON from the response
        # MCP returns content as a list of TextContent objects
        response_json: dict[str, Any] | None = None
        for content_item in result.content:
            if hasattr(content_item, "text"):
                text = content_item.text
                if isinstance(text, str):
                    response_json = json.loads(text)
                    break

        if response_json is None:
            raise RuntimeError(f"Tool {tool_name} returned unexpected content format")

        # Deserialize to Pydantic model
        return response_type.model_validate(response_json)

    # Query Tools

    async def list_contracts(self, request: ListContractsRequest) -> ListContractsResponse:
        """
        List all contracts with optional filters.

        Args:
            request: Request with filter criteria

        Returns:
            Response containing matching contracts
        """
        request.path = self._project_path
        return await self._call_tool("list_contracts", request, ListContractsResponse)

    async def get_contract(self, request: GetContractRequest) -> GetContractResponse:
        """
        Get detailed information about a specific contract.

        Args:
            request: Request with contract key

        Returns:
            Response with contract details
        """
        request.path = self._project_path
        return await self._call_tool("get_contract", request, GetContractResponse)

    async def get_contract_source(
        self, request: GetContractSourceRequest
    ) -> GetContractSourceResponse:
        """
        Get the full source code of the file where a contract is implemented.

        Args:
            request: Request with contract key

        Returns:
            Response with source code and file path
        """
        request.path = self._project_path
        return await self._call_tool("get_contract_source", request, GetContractSourceResponse)

    async def get_function_source(
        self, request: GetFunctionSourceRequest
    ) -> GetFunctionSourceResponse:
        """
        Get the source code of a specific function.

        Args:
            request: Request with function key

        Returns:
            Response with function source code, file path, and line numbers
        """
        request.path = self._project_path
        return await self._call_tool("get_function_source", request, GetFunctionSourceResponse)

    async def list_functions(self, request: ListFunctionsRequest) -> ListFunctionsResponse:
        """
        List functions with optional filters.

        Args:
            request: Request with filter criteria

        Returns:
            Response containing matching functions
        """
        request.path = self._project_path
        return await self._call_tool("list_functions", request, ListFunctionsResponse)

    # Analysis Tools

    async def function_callees(self, request: FunctionCalleesRequest) -> FunctionCalleesResponse:
        """
        Get the functions called by a specific function.

        Args:
            request: Request with function signature and context

        Returns:
            Response with internal, external, and library callees
        """
        request.path = self._project_path
        return await self._call_tool("get_function_callees", request, FunctionCalleesResponse)

    async def function_callers(self, request: FunctionCallersRequest) -> FunctionCallersResponse:
        """
        Get all functions that call the target function, grouped by call type.

        Args:
            request: Request with function key

        Returns:
            Response with internal, external, and library callers
        """
        request.path = self._project_path
        return await self._call_tool("get_function_callers", request, FunctionCallersResponse)

    async def get_inherited_contracts(
        self, request: GetInheritedContractsRequest
    ) -> GetInheritedContractsResponse:
        """
        Get the inherited contracts for a contract.

        Args:
            request: Request with contract key

        Returns:
            Response with inheritance tree
        """
        request.path = self._project_path
        return await self._call_tool(
            "get_inherited_contracts", request, GetInheritedContractsResponse
        )

    async def get_derived_contracts(
        self, request: GetDerivedContractsRequest
    ) -> GetDerivedContractsResponse:
        """
        Get the derived contracts for a contract (contracts that inherit from it).

        Args:
            request: Request with contract key

        Returns:
            Response with derived contracts tree
        """
        request.path = self._project_path
        return await self._call_tool("get_derived_contracts", request, GetDerivedContractsResponse)

    async def list_function_implementations(
        self, request: ListFunctionImplementationsRequest
    ) -> ListFunctionImplementationsResponse:
        """
        Find all contracts that implement a specific function.

        Args:
            request: Request with contract key and function signature

        Returns:
            Response with implementing contracts
        """
        request.path = self._project_path
        return await self._call_tool(
            "list_function_implementations", request, ListFunctionImplementationsResponse
        )

    # Detector Tools

    async def list_detectors(self, request: ListDetectorsRequest) -> ListDetectorsResponse:
        """
        List all available Slither detectors with their metadata.

        Args:
            request: Request with optional name filter

        Returns:
            Response with detector metadata
        """
        request.path = self._project_path
        return await self._call_tool("list_detectors", request, ListDetectorsResponse)

    async def run_detectors(self, request: RunDetectorsRequest) -> RunDetectorsResponse:
        """
        Retrieve cached Slither detector results with optional filtering.

        Args:
            request: Request with optional filters for detector names, impact, and confidence

        Returns:
            Response with detector findings
        """
        request.path = self._project_path
        return await self._call_tool("run_detectors", request, RunDetectorsResponse)

    # Helper methods for common patterns

    async def get_all_contracts(self) -> list[ContractModel]:
        """
        Get all contracts in the project.

        Returns:
            List of all contract models
        """
        request = ListContractsRequest(path=self._project_path, filter_type="all")
        response = await self.list_contracts(request)

        if not response.success or not response.contracts:
            return []

        # Get full contract details for each
        contracts = []
        for contract_info in response.contracts:
            contract_request = GetContractRequest(
                path=self._project_path, contract_key=contract_info.key, include_functions=True
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
        request = ListContractsRequest(path=self._project_path, filter_type="all")
        response = await self.list_contracts(request)

        if not response.success or not response.contracts:
            return ProjectFacts(contracts={}, project_dir=self._project_path)

        # Build contracts dict
        contracts = {}
        for contract_info in response.contracts:
            # Get full contract details
            contract_request = GetContractRequest(
                path=self._project_path, contract_key=contract_info.key, include_functions=True
            )
            contract_response = await self.get_contract(contract_request)
            if contract_response.success and contract_response.contract:
                contracts[contract_info.key] = contract_response.contract

        return ProjectFacts(contracts=contracts, project_dir=self._project_path)

    async def get_all_contract_infos(
        self,
        filter_type: str = "all",
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> list[ContractInfo]:
        """
        Fetch all contract infos, handling pagination automatically.

        Args:
            filter_type: Filter type ("all", "concrete", "interface", "library", "abstract")
            sort_by: Sort field ("name", "path", "function_count") or None
            sort_order: Sort order ("asc" or "desc")

        Returns:
            List of all ContractInfo objects matching the filter
        """
        all_contracts: list[ContractInfo] = []
        offset = 0
        page_size = 100

        while True:
            request = ListContractsRequest(
                path=self._project_path,
                filter_type=filter_type,  # type: ignore[arg-type]
                sort_by=sort_by,  # type: ignore[arg-type]
                sort_order=sort_order,  # type: ignore[arg-type]
                limit=page_size,
                offset=offset,
            )
            response = await self.list_contracts(request)

            if not response.success:
                break

            all_contracts.extend(response.contracts)

            if not response.has_more:
                break
            offset += page_size

        return all_contracts

    async def get_all_function_infos(
        self,
        contract_info: ContractInfo,
        visibility: list[str] | None = None,
        has_modifiers: list[str] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> list[FunctionInfo]:
        """
        Fetch all function infos for a contract, handling pagination automatically.

        Args:
            contract_info: The contract to get functions for
            visibility: Filter by visibility (e.g., ["public", "external"])
            has_modifiers: Filter by modifiers (e.g., ["onlyOwner"])
            sort_by: Sort field ("name", "visibility", "line_count") or None
            sort_order: Sort order ("asc" or "desc")

        Returns:
            List of all FunctionInfo objects matching the filters
        """
        all_functions: list[FunctionInfo] = []
        offset = 0
        page_size = 100

        while True:
            request = ListFunctionsRequest(
                path=self._project_path,
                contract_key=contract_info.key,
                visibility=visibility,
                has_modifiers=has_modifiers,
                sort_by=sort_by,  # type: ignore[arg-type]
                sort_order=sort_order,  # type: ignore[arg-type]
                limit=page_size,
                offset=offset,
            )
            response = await self.list_functions(request)

            if not response.success:
                break

            all_functions.extend(response.functions)

            if not response.has_more:
                break
            offset += page_size

        return all_functions

    # Tool wrappers for pydantic-ai agents

    def create_list_contracts_tool(self):
        """
        Create a list_contracts tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def list_contracts(request: ListContractsRequest) -> ListContractsResponse:
            """List all contracts with optional filters."""
            request.path = self._project_path
            return await self.list_contracts(request)

        return list_contracts

    def create_get_contract_tool(self):
        """
        Create a get_contract tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def get_contract(request: GetContractRequest) -> GetContractResponse:
            """Get detailed information about a specific contract."""
            request.path = self._project_path
            return await self.get_contract(request)

        return get_contract

    def create_get_contract_source_tool(self):
        """
        Create a get_contract_source tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def get_contract_source(
            request: GetContractSourceRequest,
        ) -> GetContractSourceResponse:
            """Get the full source code of the file where a contract is implemented."""
            request.path = self._project_path
            return await self.get_contract_source(request)

        return get_contract_source

    def create_get_function_source_tool(self):
        """
        Create a get_function_source tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def get_function_source(
            request: GetFunctionSourceRequest,
        ) -> GetFunctionSourceResponse:
            """Get the source code of a specific function."""
            request.path = self._project_path
            return await self.get_function_source(request)

        return get_function_source

    def create_list_functions_tool(self):
        """
        Create a list_functions tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def list_functions(request: ListFunctionsRequest) -> ListFunctionsResponse:
            """List functions with optional filters."""
            request.path = self._project_path
            return await self.list_functions(request)

        return list_functions

    def create_function_callees_tool(self):
        """
        Create a function_callees tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def function_callees(request: FunctionCalleesRequest) -> FunctionCalleesResponse:
            """Get the internal, external, and library callees for a function."""
            request.path = self._project_path
            return await self.function_callees(request)

        return function_callees

    def create_function_callers_tool(self):
        """
        Create a function_callers tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def function_callers(request: FunctionCallersRequest) -> FunctionCallersResponse:
            """Get all functions that call the target function, grouped by call type."""
            request.path = self._project_path
            return await self.function_callers(request)

        return function_callers

    def create_get_inherited_contracts_tool(self):
        """
        Create a get_inherited_contracts tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def get_inherited_contracts(
            request: GetInheritedContractsRequest,
        ) -> GetInheritedContractsResponse:
            """Get the inherited contracts for a contract."""
            request.path = self._project_path
            return await self.get_inherited_contracts(request)

        return get_inherited_contracts

    def create_get_derived_contracts_tool(self):
        """
        Create a get_derived_contracts tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def get_derived_contracts(
            request: GetDerivedContractsRequest,
        ) -> GetDerivedContractsResponse:
            """Get the derived contracts for a contract (contracts that inherit from it)."""
            request.path = self._project_path
            return await self.get_derived_contracts(request)

        return get_derived_contracts

    def create_function_implementations_tool(self):
        """
        Create a list_function_implementations tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def list_function_implementations(
            request: ListFunctionImplementationsRequest,
        ) -> ListFunctionImplementationsResponse:
            """List all contracts that implement a specific function signature."""
            request.path = self._project_path
            return await self.list_function_implementations(request)

        return list_function_implementations

    def create_list_detectors_tool(self):
        """
        Create a list_detectors tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def list_detectors(request: ListDetectorsRequest) -> ListDetectorsResponse:
            """List all available Slither detectors with their metadata."""
            request.path = self._project_path
            return await self.list_detectors(request)

        return list_detectors

    def create_run_detectors_tool(self):
        """
        Create a run_detectors tool for pydantic-ai agents.

        Returns a wrapper function that pre-populates the path parameter.
        """

        async def run_detectors(request: RunDetectorsRequest) -> RunDetectorsResponse:
            """Retrieve cached Slither detector results with optional filtering."""
            request.path = self._project_path
            return await self.run_detectors(request)

        return run_detectors
