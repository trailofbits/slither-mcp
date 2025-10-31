"""Tests for tool wrappers."""

from unittest.mock import AsyncMock
import pytest

from slither_mcp.client.mcp_client import SlitherMCPClient
from slither_mcp.client.tool_wrappers import (
    create_function_callees_tool,
    create_function_implementations_tool,
)
from slither_mcp.tools import (
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
)
from slither_mcp.types import ContractKey


class TestFunctionCalleesTool:
    """Test the function_callees tool wrapper."""

    @pytest.mark.asyncio
    async def test_wrapper_calls_client_method(self, child_contract_key):
        """Test that the wrapper correctly calls the client method."""
        # Create mock client
        mock_client = AsyncMock(spec=SlitherMCPClient)
        
        # Mock the response
        from slither_mcp.tools.list_function_callees import QueryContext
        from slither_mcp.types import FunctionCallees
        
        expected_response = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                ext_function_signature="ChildContract.childFunction(address)",
                calling_context=child_contract_key
            ),
            callees=FunctionCallees(
                internal_callees=["internalFunc()"],
                external_callees=["ExternalContract.externalFunc()"],
                library_callees=["LibraryContract.libraryFunc()"],
                has_low_level_calls=False
            )
        )
        mock_client.function_callees = AsyncMock(return_value=expected_response)
        
        # Create the wrapper
        function_callees_tool = create_function_callees_tool(mock_client)
        
        # Call the wrapper
        from slither_mcp.types import FunctionKey
        
        request = FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                signature="childFunction(address)",
                contract_name="ChildContract",
                path="contracts/Child.sol"
            )
        )
        response = await function_callees_tool(request)
        
        # Verify the client method was called
        mock_client.function_callees.assert_called_once_with(request)
        
        # Verify the response
        assert response.success is True
        assert response.callees is not None
        assert len(response.callees.internal_callees) == 1
        assert response.callees.internal_callees[0] == "internalFunc()"
        assert len(response.callees.external_callees) == 1
        assert len(response.callees.library_callees) == 1

    @pytest.mark.asyncio
    async def test_wrapper_has_correct_name(self):
        """Test that the wrapper function has the correct name for introspection."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        function_callees_tool = create_function_callees_tool(mock_client)
        
        # The function should be named 'function_callees' for pydantic-ai
        assert function_callees_tool.__name__ == "function_callees"

    @pytest.mark.asyncio
    async def test_wrapper_has_docstring(self):
        """Test that the wrapper has a docstring for introspection."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        function_callees_tool = create_function_callees_tool(mock_client)
        
        # Should have a docstring
        assert function_callees_tool.__doc__ is not None
        assert "callees" in function_callees_tool.__doc__.lower()

    @pytest.mark.asyncio
    async def test_wrapper_preserves_error_response(self, child_contract_key):
        """Test that error responses are preserved through the wrapper."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        
        # Mock error response
        from slither_mcp.tools.list_function_callees import QueryContext
        
        error_response = FunctionCalleesResponse(
            success=False,
            query_context=QueryContext(
                ext_function_signature="NonExistent.function()",
                calling_context=child_contract_key
            ),
            callees=None,
            error_message="Function not found"
        )
        mock_client.function_callees = AsyncMock(return_value=error_response)
        
        # Create and call wrapper
        from slither_mcp.types import FunctionKey
        
        function_callees_tool = create_function_callees_tool(mock_client)
        request = FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                signature="function()",
                contract_name="NonExistent",
                path="contracts/Child.sol"
            )
        )
        response = await function_callees_tool(request)
        
        # Verify error is preserved
        assert response.success is False
        assert response.error_message == "Function not found"


class TestFunctionImplementationsTool:
    """Test the list_function_implementations tool wrapper."""

    @pytest.mark.asyncio
    async def test_wrapper_calls_client_method(self, child_contract_key, child_contract):
        """Test that the wrapper correctly calls the client method."""
        # Create mock client
        mock_client = AsyncMock(spec=SlitherMCPClient)
        
        # Mock the response
        expected_response = ListFunctionImplementationsResponse(
            success=True,
            implementing_contracts=[child_contract]
        )
        mock_client.list_function_implementations = AsyncMock(return_value=expected_response)
        
        # Create the wrapper
        implementations_tool = create_function_implementations_tool(mock_client)
        
        # Call the wrapper
        request = ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
            function_signature="childFunction(address)"
        )
        response = await implementations_tool(request)
        
        # Verify the client method was called
        mock_client.list_function_implementations.assert_called_once_with(request)
        
        # Verify the response
        assert response.success is True
        assert response.implementing_contracts is not None
        assert len(response.implementing_contracts) == 1
        assert response.implementing_contracts[0].name == "ChildContract"

    @pytest.mark.asyncio
    async def test_wrapper_has_correct_name(self):
        """Test that the wrapper function has the correct name for introspection."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        implementations_tool = create_function_implementations_tool(mock_client)
        
        # The function should be named 'list_function_implementations' for pydantic-ai
        assert implementations_tool.__name__ == "list_function_implementations"

    @pytest.mark.asyncio
    async def test_wrapper_has_docstring(self):
        """Test that the wrapper has a docstring for introspection."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        implementations_tool = create_function_implementations_tool(mock_client)
        
        # Should have a docstring
        assert implementations_tool.__doc__ is not None
        assert "implement" in implementations_tool.__doc__.lower()

    @pytest.mark.asyncio
    async def test_wrapper_preserves_error_response(self, child_contract_key):
        """Test that error responses are preserved through the wrapper."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        
        # Mock error response
        error_response = ListFunctionImplementationsResponse(
            success=False,
            implementing_contracts=None,
            error_message="Contract not found"
        )
        mock_client.list_function_implementations = AsyncMock(return_value=error_response)
        
        # Create and call wrapper
        implementations_tool = create_function_implementations_tool(mock_client)
        request = ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
            function_signature="nonExistent()"
        )
        response = await implementations_tool(request)
        
        # Verify error is preserved
        assert response.success is False
        assert response.error_message == "Contract not found"

    @pytest.mark.asyncio
    async def test_multiple_implementations(self, child_contract_key, child_contract, base_contract, standalone_contract):
        """Test handling multiple implementations."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        
        expected_response = ListFunctionImplementationsResponse(
            success=True,
            implementing_contracts=[child_contract, base_contract, standalone_contract]
        )
        mock_client.list_function_implementations = AsyncMock(return_value=expected_response)
        
        implementations_tool = create_function_implementations_tool(mock_client)
        request = ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
            function_signature="commonFunction()"
        )
        response = await implementations_tool(request)
        
        assert response.success is True
        assert response.implementing_contracts is not None
        assert len(response.implementing_contracts) == 3
        assert response.implementing_contracts[0].name == "ChildContract"
        assert response.implementing_contracts[1].name == "BaseContract"
        assert response.implementing_contracts[2].name == "StandaloneContract"


class TestToolWrapperIntegration:
    """Test tool wrappers with multiple tools together."""

    @pytest.mark.asyncio
    async def test_multiple_wrappers_from_same_client(self, child_contract_key, child_contract):
        """Test creating multiple wrappers from the same client."""
        mock_client = AsyncMock(spec=SlitherMCPClient)
        
        # Set up mock responses
        from slither_mcp.tools.list_function_callees import QueryContext
        from slither_mcp.types import FunctionCallees
        
        callees_response = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                ext_function_signature="Test.func()",
                calling_context=child_contract_key
            ),
            callees=FunctionCallees(
                internal_callees=["helper()"],
                external_callees=[],
                library_callees=[],
                has_low_level_calls=False
            )
        )
        mock_client.function_callees = AsyncMock(return_value=callees_response)
        
        impls_response = ListFunctionImplementationsResponse(
            success=True,
            implementing_contracts=[child_contract]
        )
        mock_client.list_function_implementations = AsyncMock(return_value=impls_response)
        
        # Create both wrappers
        callees_tool = create_function_callees_tool(mock_client)
        impls_tool = create_function_implementations_tool(mock_client)
        
        # Use both tools
        from slither_mcp.types import FunctionKey
        
        callees_result = await callees_tool(
            FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                    signature="func()",
                    contract_name="Test",
                    path="contracts/Child.sol"
                )
            )
        )
        impls_result = await impls_tool(
            ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
                function_signature="func()"
            )
        )
        
        # Verify both worked
        assert callees_result.success is True
        assert impls_result.success is True
        
        # Verify both client methods were called
        mock_client.function_callees.assert_called_once()
        mock_client.list_function_implementations.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrappers_are_independent(self):
        """Test that wrappers from different clients are independent."""
        mock_client1 = AsyncMock(spec=SlitherMCPClient)
        mock_client2 = AsyncMock(spec=SlitherMCPClient)
        
        from slither_mcp.tools.list_function_callees import QueryContext
        from slither_mcp.types import FunctionCallees
        
        test_key = ContractKey(contract_name="Test", path="test.sol")
        
        response1 = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                ext_function_signature="Test.func()",
                calling_context=test_key
            ),
            callees=FunctionCallees(
                internal_callees=["client1_func()"],
                external_callees=[],
                library_callees=[],
                has_low_level_calls=False
            )
        )
        response2 = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                ext_function_signature="Test.func()",
                calling_context=test_key
            ),
            callees=FunctionCallees(
                internal_callees=["client2_func()"],
                external_callees=[],
                library_callees=[],
                has_low_level_calls=False
            )
        )
        
        mock_client1.function_callees = AsyncMock(return_value=response1)
        mock_client2.function_callees = AsyncMock(return_value=response2)
        
        # Create wrappers from different clients
        tool1 = create_function_callees_tool(mock_client1)
        tool2 = create_function_callees_tool(mock_client2)
        
        # Call both
        from slither_mcp.types import FunctionKey
        
        result1 = await tool1(
            FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                    signature="func()",
                    contract_name="Test",
                    path="test.sol"
                )
            )
        )
        result2 = await tool2(
            FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                    signature="func()",
                    contract_name="Test",
                    path="test.sol"
                )
            )
        )
        
        # Verify they used different clients
        assert result1.callees.internal_callees[0] == "client1_func()"
        assert result2.callees.internal_callees[0] == "client2_func()"
        mock_client1.function_callees.assert_called_once()
        mock_client2.function_callees.assert_called_once()

