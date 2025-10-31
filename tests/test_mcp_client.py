"""Tests for the MCP client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from slither_mcp.client.mcp_client import SlitherMCPClient
from slither_mcp.tools import (
    ListContractsRequest,
    ListContractsResponse,
    GetContractRequest,
    GetContractResponse,
    ListFunctionsRequest,
    ListFunctionsResponse,
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    GetInheritedContractsRequest,
    GetInheritedContractsResponse,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
)
from slither_mcp.types import ContractKey, ContractModel, ProjectFacts


class TestSlitherMCPClientConnection:
    """Test client connection and lifecycle management."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test that client initializes with correct default state."""
        client = SlitherMCPClient()
        
        assert client._session is None
        assert client._read is None
        assert client._write is None
        assert client._project_path is None
        assert client._stdio_context is None

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to MCP server."""
        client = SlitherMCPClient()
        
        # Mock the stdio_client and session
        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_stdio_context = AsyncMock()
        mock_stdio_context.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_stdio_context.__aexit__ = AsyncMock()
        
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()
        
        with patch('slither_mcp.client.mcp_client.stdio_client', return_value=mock_stdio_context):
            with patch('slither_mcp.client.mcp_client.ClientSession', return_value=mock_session):
                await client.connect(project_path="/test/project")
                
                assert client._session is not None
                assert client._project_path == "/test/project"
                mock_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_without_default_path(self):
        """Test connection without setting default path."""
        client = SlitherMCPClient()

        mock_read = MagicMock()
        mock_write = MagicMock()
        mock_stdio_context = AsyncMock()
        mock_stdio_context.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_stdio_context.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()

        with patch('slither_mcp.client.mcp_client.stdio_client', return_value=mock_stdio_context) as mock_stdio:
            with patch('slither_mcp.client.mcp_client.ClientSession', return_value=mock_session):
                await client.connect()

                # Verify the command args don't include --path or --use-cache (both removed)
                call_args = mock_stdio.call_args[0][0]
                assert "--use-cache" not in call_args.args
                assert "--path" not in call_args.args
                assert client._project_path is None

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client connection."""
        client = SlitherMCPClient()
        
        # Set up mock session
        mock_session = AsyncMock()
        mock_session.__aexit__ = AsyncMock()
        client._session = mock_session
        
        mock_stdio_context = AsyncMock()
        mock_stdio_context.__aexit__ = AsyncMock()
        client._stdio_context = mock_stdio_context
        
        await client.close()
        
        assert client._session is None
        mock_session.__aexit__.assert_called_once()
        mock_stdio_context.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_handles_errors(self):
        """Test that close handles errors gracefully."""
        client = SlitherMCPClient()
        
        # Set up mock session that raises on exit
        mock_session = AsyncMock()
        mock_session.__aexit__ = AsyncMock(side_effect=Exception("Close error"))
        client._session = mock_session
        
        mock_stdio_context = AsyncMock()
        mock_stdio_context.__aexit__ = AsyncMock()
        client._stdio_context = mock_stdio_context
        
        # Should not raise
        await client.close()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using client as async context manager."""
        client = SlitherMCPClient()
        
        # Test __aenter__ and __aexit__
        async with client:
            assert client is not None
        
        # __aexit__ should call close (which we've tested separately)

    @pytest.mark.asyncio
    async def test_ensure_connected_raises_when_not_connected(self):
        """Test that operations fail when not connected."""
        client = SlitherMCPClient()
        
        with pytest.raises(RuntimeError, match="not connected"):
            await client.list_contracts(ListContractsRequest(path="/test/project"))


class TestSlitherMCPClientTools:
    """Test client tool method calls."""

    @pytest.fixture
    def mock_connected_client(self):
        """Create a mock connected client."""
        client = SlitherMCPClient()
        
        # Mock the session
        mock_session = AsyncMock()
        client._session = mock_session
        client._project_path = "/test/project"
        
        return client, mock_session

    @pytest.mark.asyncio
    async def test_list_contracts(self, mock_connected_client):
        """Test list_contracts method."""
        client, mock_session = mock_connected_client
        
        # Mock the response
        expected_response = ListContractsResponse(
            success=True,
            contracts=[],
            total_count=0
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = expected_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Call the method
        request = ListContractsRequest(path="/test/project", filter_type="all")
        response = await client.list_contracts(request)
        
        # Verify
        assert response.success is True
        assert response.total_count == 0
        mock_session.call_tool.assert_called_once()
        call_args = mock_session.call_tool.call_args
        assert call_args[0][0] == "list_contracts"

    @pytest.mark.asyncio
    async def test_get_contract(self, mock_connected_client, child_contract_key, child_contract):
        """Test get_contract method."""
        client, mock_session = mock_connected_client
        
        # Mock the response
        expected_response = GetContractResponse(
            success=True,
            contract=child_contract
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = expected_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Call the method
        request = GetContractRequest(
            path="/test/project",
            contract_key=child_contract_key,
            include_functions=True
        )
        response = await client.get_contract(request)
        
        # Verify
        assert response.success is True
        assert response.contract is not None
        assert response.contract.name == "ChildContract"
        mock_session.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_functions(self, mock_connected_client, child_contract_key):
        """Test list_functions method."""
        client, mock_session = mock_connected_client
        
        # Mock the response
        expected_response = ListFunctionsResponse(
            success=True,
            functions=[],
            total_count=0
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = expected_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Call the method
        request = ListFunctionsRequest(path="/test/project", contract_key=child_contract_key)
        response = await client.list_functions(request)
        
        # Verify
        assert response.success is True
        assert response.total_count == 0
        mock_session.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_function_callees(self, mock_connected_client, child_contract_key, empty_callees):
        """Test function_callees method."""
        client, mock_session = mock_connected_client
        
        # Mock the response
        from slither_mcp.tools.list_function_callees import QueryContext
        
        expected_response = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                ext_function_signature="ChildContract.childFunction(address)",
                calling_context=child_contract_key
            ),
            callees=empty_callees
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = expected_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Call the method
        from slither_mcp.types import FunctionKey
        
        request = FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                signature="childFunction(address)",
                contract_name="ChildContract",
                path="contracts/Child.sol"
            )
        )
        response = await client.function_callees(request)
        
        # Verify
        assert response.success is True
        assert response.callees is not None
        assert len(response.callees.internal_callees) == 0
        mock_session.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_inherited_contracts(self, mock_connected_client, child_contract_key):
        """Test get_inherited_contracts method."""
        client, mock_session = mock_connected_client
        
        # Mock the response
        expected_response = GetInheritedContractsResponse(
            success=True,
            contract_key=child_contract_key,
            full_inheritance=None
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = expected_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Call the method
        request = GetInheritedContractsRequest(path="/test/project", contract_key=child_contract_key)
        response = await client.get_inherited_contracts(request)
        
        # Verify
        assert response.success is True
        assert response.contract_key == child_contract_key
        mock_session.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_function_implementations(self, mock_connected_client, child_contract_key):
        """Test list_function_implementations method."""
        client, mock_session = mock_connected_client
        
        # Mock the response
        expected_response = ListFunctionImplementationsResponse(
            success=True,
            implementing_contracts=[]
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = expected_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Call the method
        request = ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
            function_signature="childFunction(address)"
        )
        response = await client.list_function_implementations(request)
        
        # Verify
        assert response.success is True
        assert response.implementing_contracts is not None
        assert len(response.implementing_contracts) == 0
        mock_session.call_tool.assert_called_once()


class TestSlitherMCPClientHelpers:
    """Test client helper methods."""

    @pytest.fixture
    def mock_connected_client(self):
        """Create a mock connected client."""
        client = SlitherMCPClient()
        
        # Mock the session
        mock_session = AsyncMock()
        client._session = mock_session
        client._project_path = "/test/project"
        
        return client, mock_session

    @pytest.mark.asyncio
    async def test_get_all_contracts(self, mock_connected_client, child_contract_key, child_contract):
        """Test get_all_contracts helper method."""
        client, mock_session = mock_connected_client
        
        # Mock list_contracts response
        from slither_mcp.tools.list_contracts import ContractInfo
        
        list_response = ListContractsResponse(
            success=True,
            contracts=[
                ContractInfo(
                    key=child_contract_key,
                    is_abstract=False,
                    is_interface=False,
                    is_library=False,
                    is_fully_implemented=True
                )
            ],
            total_count=1
        )
        
        # Mock get_contract response
        get_response = GetContractResponse(
            success=True,
            contract=child_contract
        )
        
        # Set up mock responses
        call_count = [0]
        
        async def mock_call_tool(tool_name, arguments):
            mock_result = MagicMock()
            mock_content = MagicMock()
            
            if tool_name == "list_contracts":
                mock_content.text = list_response.model_dump_json()
            else:  # get_contract
                mock_content.text = get_response.model_dump_json()
            
            mock_result.content = [mock_content]
            call_count[0] += 1
            return mock_result
        
        mock_session.call_tool = mock_call_tool
        
        # Call the helper
        contracts = await client.get_all_contracts()
        
        # Verify
        assert len(contracts) == 1
        assert contracts[0].name == "ChildContract"
        assert call_count[0] == 2  # list_contracts + get_contract

    @pytest.mark.asyncio
    async def test_get_all_contracts_empty(self, mock_connected_client):
        """Test get_all_contracts with no contracts."""
        client, mock_session = mock_connected_client
        
        # Mock empty response
        list_response = ListContractsResponse(
            success=True,
            contracts=[],
            total_count=0
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = list_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Call the helper
        contracts = await client.get_all_contracts()
        
        # Verify
        assert len(contracts) == 0

    @pytest.mark.asyncio
    async def test_get_project_facts(self, mock_connected_client, child_contract_key, child_contract):
        """Test get_project_facts helper method."""
        client, mock_session = mock_connected_client
        
        # Mock responses
        from slither_mcp.tools.list_contracts import ContractInfo
        
        list_response = ListContractsResponse(
            success=True,
            contracts=[
                ContractInfo(
                    key=child_contract_key,
                    is_abstract=False,
                    is_interface=False,
                    is_library=False,
                    is_fully_implemented=True
                )
            ],
            total_count=1
        )
        
        get_response = GetContractResponse(
            success=True,
            contract=child_contract
        )
        
        # Set up mock responses
        async def mock_call_tool(tool_name, arguments):
            mock_result = MagicMock()
            mock_content = MagicMock()
            
            if tool_name == "list_contracts":
                mock_content.text = list_response.model_dump_json()
            else:  # get_contract
                mock_content.text = get_response.model_dump_json()
            
            mock_result.content = [mock_content]
            return mock_result
        
        mock_session.call_tool = mock_call_tool
        
        # Call the helper
        facts = await client.get_project_facts()
        
        # Verify
        assert isinstance(facts, ProjectFacts)
        assert len(facts.contracts) == 1
        assert child_contract_key in facts.contracts
        assert facts.project_dir == "/test/project"


class TestSlitherMCPClientErrorHandling:
    """Test client error handling."""

    @pytest.fixture
    def mock_connected_client(self):
        """Create a mock connected client."""
        client = SlitherMCPClient()
        
        # Mock the session
        mock_session = AsyncMock()
        client._session = mock_session
        client._project_path = "/test/project"
        
        return client, mock_session

    @pytest.mark.asyncio
    async def test_tool_returns_no_content(self, mock_connected_client):
        """Test error handling when tool returns no content."""
        client, mock_session = mock_connected_client
        
        # Mock result with no content
        mock_result = MagicMock()
        mock_result.content = []
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="returned no content"):
            await client.list_contracts(ListContractsRequest(path="/test/project"))

    @pytest.mark.asyncio
    async def test_tool_returns_invalid_format(self, mock_connected_client):
        """Test error handling when tool returns unexpected format."""
        client, mock_session = mock_connected_client
        
        # Mock result with content that has no text attribute
        mock_result = MagicMock()
        mock_content = MagicMock(spec=[])  # No text attribute
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="unexpected content format"):
            await client.list_contracts(ListContractsRequest(path="/test/project"))

    @pytest.mark.asyncio
    async def test_tool_returns_error_response(self, mock_connected_client):
        """Test handling of error responses from tools."""
        client, mock_session = mock_connected_client
        
        # Mock error response
        error_response = ListContractsResponse(
            success=False,
            contracts=[],
            total_count=0,
            error_message="Contract not found"
        )
        
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = error_response.model_dump_json()
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Should return error response
        response = await client.list_contracts(ListContractsRequest(path="/test/project"))
        
        assert response.success is False
        assert response.error_message == "Contract not found"

    @pytest.mark.asyncio
    async def test_serialization_error(self, mock_connected_client):
        """Test handling of serialization errors."""
        client, mock_session = mock_connected_client
        
        # Mock response with invalid JSON
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "invalid json {"
        mock_result.content = [mock_content]
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        # Should raise JSON decode error
        with pytest.raises(json.JSONDecodeError):
            await client.list_contracts(ListContractsRequest(path="/test/project"))

