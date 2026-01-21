"""Tests for tool creation methods on SlitherMCPClient."""

from unittest.mock import AsyncMock

import pytest

from slither_mcp.client.mcp_client import SlitherMCPClient
from slither_mcp.tools import (
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    ImplementationInfo,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
)
from slither_mcp.types import ContractKey


class TestFunctionCalleesTool:
    """Test the function_callees tool wrapper."""

    @pytest.mark.asyncio
    async def test_wrapper_calls_client_method(self, child_contract_key):
        """Test that the wrapper correctly calls the client method."""
        # Create real client
        real_client = SlitherMCPClient("/test/project")

        # Mock the response
        from slither_mcp.tools.list_function_callees import QueryContext
        from slither_mcp.types import FunctionCallees

        expected_response = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                searched_function="ChildContract.childFunction(address)",
                searched_calling_context=str(child_contract_key),
            ),
            callees=FunctionCallees(
                internal_callees=["internalFunc()"],
                external_callees=["ExternalContract.externalFunc()"],
                library_callees=["LibraryContract.libraryFunc()"],
                has_low_level_calls=False,
            ),
        )
        real_client.function_callees = AsyncMock(return_value=expected_response)  # type: ignore[method-assign]

        # Create the wrapper
        function_callees_tool = real_client.create_function_callees_tool()

        # Call the wrapper
        from slither_mcp.types import FunctionKey

        request = FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                signature="childFunction(address)",
                contract_name="ChildContract",
                path="contracts/Child.sol",
            ),
        )
        response = await function_callees_tool(request)

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
        real_client = SlitherMCPClient("/test/project")
        function_callees_tool = real_client.create_function_callees_tool()

        # The function should be named 'function_callees' for pydantic-ai
        assert function_callees_tool.__name__ == "function_callees"

    @pytest.mark.asyncio
    async def test_wrapper_has_docstring(self):
        """Test that the wrapper has a docstring for introspection."""
        real_client = SlitherMCPClient("/test/project")
        function_callees_tool = real_client.create_function_callees_tool()

        # Should have a docstring
        assert function_callees_tool.__doc__ is not None
        assert "callees" in function_callees_tool.__doc__.lower()

    @pytest.mark.asyncio
    async def test_wrapper_preserves_error_response(self, child_contract_key):
        """Test that error responses are preserved through the wrapper."""
        # Create real client
        real_client = SlitherMCPClient("/test/project")

        # Mock error response
        from slither_mcp.tools.list_function_callees import QueryContext

        error_response = FunctionCalleesResponse(
            success=False,
            query_context=QueryContext(
                searched_function="NonExistent.function()",
                searched_calling_context=str(child_contract_key),
            ),
            callees=None,
            error_message="Function not found",
        )
        real_client.function_callees = AsyncMock(return_value=error_response)  # type: ignore[method-assign]

        # Create and call wrapper
        from slither_mcp.types import FunctionKey

        function_callees_tool = real_client.create_function_callees_tool()
        request = FunctionCalleesRequest(
            path="/test/project",
            function_key=FunctionKey(
                signature="function()", contract_name="NonExistent", path="contracts/Child.sol"
            ),
        )
        response = await function_callees_tool(request)

        # Verify error is preserved
        assert response.success is False
        assert response.error_message == "Function not found"


class TestFunctionImplementationsTool:
    """Test the list_function_implementations tool wrapper."""

    @pytest.mark.asyncio
    async def test_wrapper_calls_client_method(self, child_contract_key):
        """Test that the wrapper correctly calls the client method."""
        # Create real client
        real_client = SlitherMCPClient("/test/project")

        # Mock the response with ImplementationInfo
        impl_info = ImplementationInfo(
            contract_key=child_contract_key,
            is_abstract=False,
            is_interface=False,
            function_visibility="public",
            function_modifiers=[],
        )
        expected_response = ListFunctionImplementationsResponse(
            success=True, implementations=[impl_info]
        )
        real_client.list_function_implementations = AsyncMock(return_value=expected_response)  # type: ignore[method-assign]

        # Create the wrapper
        implementations_tool = real_client.create_function_implementations_tool()

        # Call the wrapper
        request = ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
            function_signature="childFunction(address)",
        )
        response = await implementations_tool(request)

        # Verify the response
        assert response.success is True
        assert response.implementations is not None
        assert len(response.implementations) == 1
        assert response.implementations[0].contract_key.contract_name == "ChildContract"

    @pytest.mark.asyncio
    async def test_wrapper_has_correct_name(self):
        """Test that the wrapper function has the correct name for introspection."""
        real_client = SlitherMCPClient("/test/project")
        implementations_tool = real_client.create_function_implementations_tool()

        # The function should be named 'list_function_implementations' for pydantic-ai
        assert implementations_tool.__name__ == "list_function_implementations"

    @pytest.mark.asyncio
    async def test_wrapper_has_docstring(self):
        """Test that the wrapper has a docstring for introspection."""
        real_client = SlitherMCPClient("/test/project")
        implementations_tool = real_client.create_function_implementations_tool()

        # Should have a docstring
        assert implementations_tool.__doc__ is not None
        assert "implement" in implementations_tool.__doc__.lower()

    @pytest.mark.asyncio
    async def test_wrapper_preserves_error_response(self, child_contract_key):
        """Test that error responses are preserved through the wrapper."""
        real_client = SlitherMCPClient("/test/project")

        # Mock error response
        error_response = ListFunctionImplementationsResponse(
            success=False, implementations=None, error_message="Contract not found"
        )
        real_client.list_function_implementations = AsyncMock(return_value=error_response)  # type: ignore[method-assign]

        # Create and call wrapper
        implementations_tool = real_client.create_function_implementations_tool()
        request = ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
            function_signature="nonExistent()",
        )
        response = await implementations_tool(request)

        # Verify error is preserved
        assert response.success is False
        assert response.error_message == "Contract not found"

    @pytest.mark.asyncio
    async def test_multiple_implementations(
        self, child_contract_key, base_contract_key, standalone_contract_key
    ):
        """Test handling multiple implementations."""
        real_client = SlitherMCPClient("/test/project")

        # Create ImplementationInfo objects for each contract
        impl_infos = [
            ImplementationInfo(
                contract_key=child_contract_key,
                is_abstract=False,
                is_interface=False,
                function_visibility="public",
                function_modifiers=[],
            ),
            ImplementationInfo(
                contract_key=base_contract_key,
                is_abstract=True,
                is_interface=False,
                function_visibility="public",
                function_modifiers=[],
            ),
            ImplementationInfo(
                contract_key=standalone_contract_key,
                is_abstract=False,
                is_interface=False,
                function_visibility="public",
                function_modifiers=[],
            ),
        ]

        expected_response = ListFunctionImplementationsResponse(
            success=True,
            implementations=impl_infos,
        )
        real_client.list_function_implementations = AsyncMock(return_value=expected_response)  # type: ignore[method-assign]

        implementations_tool = real_client.create_function_implementations_tool()
        request = ListFunctionImplementationsRequest(
            path="/test/project",
            contract_key=child_contract_key,
            function_signature="commonFunction()",
        )
        response = await implementations_tool(request)

        assert response.success is True
        assert response.implementations is not None
        assert len(response.implementations) == 3
        assert response.implementations[0].contract_key.contract_name == "ChildContract"
        assert response.implementations[1].contract_key.contract_name == "BaseContract"
        assert response.implementations[2].contract_key.contract_name == "StandaloneContract"


class TestToolWrapperIntegration:
    """Test tool wrappers with multiple tools together."""

    @pytest.mark.asyncio
    async def test_multiple_wrappers_from_same_client(self, child_contract_key):
        """Test creating multiple wrappers from the same client."""
        real_client = SlitherMCPClient("/test/project")

        # Set up mock responses
        from slither_mcp.tools.list_function_callees import QueryContext
        from slither_mcp.types import FunctionCallees

        callees_response = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                searched_function="Test.func()", searched_calling_context=str(child_contract_key)
            ),
            callees=FunctionCallees(
                internal_callees=["helper()"],
                external_callees=[],
                library_callees=[],
                has_low_level_calls=False,
            ),
        )
        real_client.function_callees = AsyncMock(return_value=callees_response)  # type: ignore[method-assign]

        impl_info = ImplementationInfo(
            contract_key=child_contract_key,
            is_abstract=False,
            is_interface=False,
            function_visibility="public",
            function_modifiers=[],
        )
        impls_response = ListFunctionImplementationsResponse(
            success=True, implementations=[impl_info]
        )
        real_client.list_function_implementations = AsyncMock(return_value=impls_response)  # type: ignore[method-assign]

        # Create both wrappers
        callees_tool = real_client.create_function_callees_tool()
        impls_tool = real_client.create_function_implementations_tool()

        # Use both tools
        from slither_mcp.types import FunctionKey

        callees_result = await callees_tool(
            FunctionCalleesRequest(
                path="/test/project",
                function_key=FunctionKey(
                    signature="func()", contract_name="Test", path="contracts/Child.sol"
                ),
            )
        )
        impls_result = await impls_tool(
            ListFunctionImplementationsRequest(
                path="/test/project", contract_key=child_contract_key, function_signature="func()"
            )
        )

        # Verify both worked
        assert callees_result.success is True
        assert impls_result.success is True

    @pytest.mark.asyncio
    async def test_wrappers_are_independent(self):
        """Test that wrappers from different clients are independent."""
        real_client1 = SlitherMCPClient("/test/project1")
        real_client2 = SlitherMCPClient("/test/project2")

        from slither_mcp.tools.list_function_callees import QueryContext
        from slither_mcp.types import FunctionCallees

        test_key = ContractKey(contract_name="Test", path="test.sol")

        response1 = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                searched_function="Test.func()", searched_calling_context=str(test_key)
            ),
            callees=FunctionCallees(
                internal_callees=["client1_func()"],
                external_callees=[],
                library_callees=[],
                has_low_level_calls=False,
            ),
        )
        response2 = FunctionCalleesResponse(
            success=True,
            query_context=QueryContext(
                searched_function="Test.func()", searched_calling_context=str(test_key)
            ),
            callees=FunctionCallees(
                internal_callees=["client2_func()"],
                external_callees=[],
                library_callees=[],
                has_low_level_calls=False,
            ),
        )

        real_client1.function_callees = AsyncMock(return_value=response1)  # type: ignore[method-assign]
        real_client2.function_callees = AsyncMock(return_value=response2)  # type: ignore[method-assign]

        # Create wrappers from different clients
        tool1 = real_client1.create_function_callees_tool()
        tool2 = real_client2.create_function_callees_tool()

        # Call both
        from slither_mcp.types import FunctionKey

        result1 = await tool1(
            FunctionCalleesRequest(
                path="/test/project",
                function_key=FunctionKey(signature="func()", contract_name="Test", path="test.sol"),
            )
        )
        result2 = await tool2(
            FunctionCalleesRequest(
                path="/test/project",
                function_key=FunctionKey(signature="func()", contract_name="Test", path="test.sol"),
            )
        )

        # Verify they used different clients
        assert result1.callees is not None
        assert result2.callees is not None
        assert result1.callees.internal_callees[0] == "client1_func()"
        assert result2.callees.internal_callees[0] == "client2_func()"
