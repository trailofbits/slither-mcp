"""Tests for list_functions tool."""

import pytest
from slither_mcp.tools.list_functions import (
    ListFunctionsRequest,
    list_functions,
)
from slither_mcp.types import ContractKey


class TestListFunctionsHappyPath:
    """Test happy path scenarios for list_functions."""

    def test_list_all_functions_standalone(self, project_facts, standalone_contract_key):
        """Test listing all functions in a standalone contract."""
        request = ListFunctionsRequest(contract_key=standalone_contract_key)
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "standaloneFunction(uint256,address)"
        assert func.visibility == "public"
        assert func.is_declared is True
        assert "public" in func.solidity_modifiers

    def test_list_all_functions_with_inheritance(self, project_facts, child_contract_key):
        """Test listing all functions including inherited ones."""
        request = ListFunctionsRequest(contract_key=child_contract_key)
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 3

        # Check we have both declared and inherited functions
        signatures = {f.function_key.signature for f in response.functions}
        assert "childFunction(address)" in signatures
        assert "initialize()" in signatures
        assert "baseFunction()" in signatures

        # Verify is_declared flag
        declared_funcs = [f for f in response.functions if f.is_declared]
        inherited_funcs = [f for f in response.functions if not f.is_declared]

        assert len(declared_funcs) == 1
        assert len(inherited_funcs) == 2
        assert declared_funcs[0].function_key.signature == "childFunction(address)"

    def test_list_functions_deep_inheritance(self, project_facts, grandchild_contract_key):
        """Test listing functions with deep inheritance hierarchy."""
        request = ListFunctionsRequest(contract_key=grandchild_contract_key)
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 4

        signatures = {f.function_key.signature for f in response.functions}
        assert "grandchildFunction()" in signatures
        assert "childFunction(address)" in signatures
        assert "initialize()" in signatures
        assert "baseFunction()" in signatures

        # Only grandchildFunction should be declared
        declared = [f for f in response.functions if f.is_declared]
        assert len(declared) == 1
        assert declared[0].function_key.signature == "grandchildFunction()"

    def test_filter_by_visibility_public(self, project_facts, child_contract_key):
        """Test filtering functions by public visibility."""
        request = ListFunctionsRequest(
            contract_key=child_contract_key,
            visibility=["public"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 2

        signatures = {f.function_key.signature for f in response.functions}
        assert "childFunction(address)" in signatures
        assert "initialize()" in signatures
        # baseFunction is internal, should not be included
        assert "baseFunction()" not in signatures

    def test_filter_by_visibility_internal(self, project_facts, child_contract_key):
        """Test filtering functions by internal visibility."""
        request = ListFunctionsRequest(
            contract_key=child_contract_key,
            visibility=["internal"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "baseFunction()"
        assert func.visibility == "internal"

    def test_filter_by_visibility_external(self, project_facts, grandchild_contract_key):
        """Test filtering functions by external visibility."""
        request = ListFunctionsRequest(
            contract_key=grandchild_contract_key,
            visibility=["external"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "grandchildFunction()"
        assert func.visibility == "external"

    def test_filter_by_multiple_visibilities(self, project_facts, child_contract_key):
        """Test filtering by multiple visibility types."""
        request = ListFunctionsRequest(
            contract_key=child_contract_key,
            visibility=["public", "internal"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 3  # All functions match

    def test_filter_by_modifier(self, project_facts, child_contract_key):
        """Test filtering functions by modifier."""
        request = ListFunctionsRequest(
            contract_key=child_contract_key,
            has_modifiers=["payable"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "childFunction(address)"
        assert "payable" in func.solidity_modifiers

    def test_filter_by_view_modifier(self, project_facts, grandchild_contract_key):
        """Test filtering functions by view modifier."""
        request = ListFunctionsRequest(
            contract_key=grandchild_contract_key,
            has_modifiers=["view"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 2

        signatures = {f.function_key.signature for f in response.functions}
        assert "grandchildFunction()" in signatures
        assert "baseFunction()" in signatures

    def test_filter_by_multiple_modifiers(self, project_facts, multi_inherit_contract_key):
        """Test filtering by multiple modifiers."""
        request = ListFunctionsRequest(
            contract_key=multi_inherit_contract_key,
            has_modifiers=["external", "override"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        # Should find functions that have ANY of the specified modifiers
        assert response.total_count >= 1

        # interfaceMethod has both external and override
        found_interface = any(
            f.function_key.signature == "interfaceMethod()" 
            for f in response.functions
        )
        assert found_interface is True

    def test_filter_visibility_and_modifiers(self, project_facts, child_contract_key):
        """Test filtering by both visibility and modifiers."""
        request = ListFunctionsRequest(
            contract_key=child_contract_key,
            visibility=["public"],
            has_modifiers=["payable"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "childFunction(address)"
        assert func.visibility == "public"
        assert "payable" in func.solidity_modifiers

    def test_function_info_completeness(self, project_facts, standalone_contract_key):
        """Test that FunctionInfo contains all required fields."""
        request = ListFunctionsRequest(contract_key=standalone_contract_key)
        response = list_functions(request, project_facts)

        func = response.functions[0]
        assert isinstance(func.function_key.signature, str)
        assert isinstance(func.function_key.contract_name, str)
        assert isinstance(func.function_key.path, str)
        assert isinstance(func.visibility, str)
        assert isinstance(func.solidity_modifiers, list)
        assert isinstance(func.is_declared, bool)


class TestListFunctionsErrorCases:
    """Test error cases for list_functions."""

    def test_contract_not_found(self, project_facts):
        """Test listing functions for a non-existent contract."""
        nonexistent_key = ContractKey(
            contract_name="NonExistent",
            path="contracts/NonExistent.sol"
        )
        request = ListFunctionsRequest(contract_key=nonexistent_key)
        response = list_functions(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "NonExistent" in response.error_message
        assert "not found" in response.error_message.lower()
        assert response.total_count == 0
        assert len(response.functions) == 0

    def test_contract_not_found_empty_project(self, empty_project_facts):
        """Test listing functions for a contract in an empty project."""
        some_key = ContractKey(
            contract_name="SomeContract",
            path="contracts/Some.sol"
        )
        request = ListFunctionsRequest(contract_key=some_key)
        response = list_functions(request, empty_project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert response.total_count == 0


class TestListFunctionsEdgeCases:
    """Test edge cases for list_functions."""

    def test_contract_with_no_functions(self, project_facts, empty_contract_key):
        """Test listing functions for a contract with no functions."""
        request = ListFunctionsRequest(contract_key=empty_contract_key)
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.functions) == 0

    def test_filter_no_matches_visibility(self, project_facts, multi_inherit_contract_key):
        """Test filtering that matches no functions."""
        # multiFunction is private, but we filter for internal
        request = ListFunctionsRequest(
            contract_key=multi_inherit_contract_key,
            visibility=["internal"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        # Should only get baseFunction which is internal
        assert response.total_count == 1
        assert response.functions[0].function_key.signature == "baseFunction()"

    def test_filter_no_matches_modifiers(self, project_facts, standalone_contract_key):
        """Test filtering by modifier that doesn't exist."""
        request = ListFunctionsRequest(
            contract_key=standalone_contract_key,
            has_modifiers=["view", "pure"]  # standaloneFunction has neither
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 0
        assert len(response.functions) == 0

    def test_interface_functions(self, project_facts, interface_a_key):
        """Test listing functions in an interface."""
        request = ListFunctionsRequest(contract_key=interface_a_key)
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "interfaceMethod()"
        assert func.is_declared is True

    def test_library_functions(self, project_facts, library_b_key):
        """Test listing functions in a library."""
        request = ListFunctionsRequest(contract_key=library_b_key)
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "add(uint256,uint256)"
        assert "pure" in func.solidity_modifiers

    def test_private_function_visibility(self, project_facts, multi_inherit_contract_key):
        """Test that private functions are included in listings."""
        request = ListFunctionsRequest(
            contract_key=multi_inherit_contract_key,
            visibility=["private"]
        )
        response = list_functions(request, project_facts)

        assert response.success is True
        assert response.total_count == 1

        func = response.functions[0]
        assert func.function_key.signature == "multiFunction()"
        assert func.visibility == "private"

    def test_multiple_inheritance(self, project_facts, multi_inherit_contract_key):
        """Test listing functions from contract with multiple inheritance."""
        request = ListFunctionsRequest(contract_key=multi_inherit_contract_key)
        response = list_functions(request, project_facts)

        assert response.success is True
        # Should have: interfaceMethod (declared), multiFunction (declared),
        # initialize (inherited from Base), baseFunction (inherited from Base)
        assert response.total_count == 4

        declared = [f for f in response.functions if f.is_declared]
        inherited = [f for f in response.functions if not f.is_declared]

        assert len(declared) == 2
        assert len(inherited) == 2

