"""Tests for list_function_callers tool."""

import pytest
from slither_mcp.tools.list_function_callers import (
    FunctionCallersRequest,
    list_function_callers,
)
from slither_mcp.types import (
    ContractKey,
    FunctionKey,
    FunctionModel,
    FunctionCallees,
    ContractModel,
    ProjectFacts,
)


@pytest.fixture
def callees_calling_base_function():
    """FunctionCallees that calls BaseContract.baseFunction()."""
    return FunctionCallees(
        internal_callees=["BaseContract.baseFunction()"],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )


@pytest.fixture
def callees_calling_child_function():
    """FunctionCallees that calls ChildContract.childFunction(address)."""
    return FunctionCallees(
        internal_callees=[],
        external_callees=["ChildContract.childFunction(address)"],
        library_callees=[],
        has_low_level_calls=False,
    )


@pytest.fixture
def callees_calling_standalone_function():
    """FunctionCallees that calls StandaloneContract.standaloneFunction(uint256,address)."""
    return FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=["StandaloneContract.standaloneFunction(uint256,address)"],
        has_low_level_calls=False,
    )


@pytest.fixture
def callees_calling_multiple_functions():
    """FunctionCallees that calls multiple functions."""
    return FunctionCallees(
        internal_callees=["BaseContract.baseFunction()", "BaseContract.initialize()"],
        external_callees=["ChildContract.childFunction(address)"],
        library_callees=["StandaloneContract.standaloneFunction(uint256,address)"],
        has_low_level_calls=False,
    )


@pytest.fixture
def project_facts_with_callers(
    base_contract_key,
    child_contract_key,
    grandchild_contract_key,
    standalone_contract_key,
    callees_calling_base_function,
    callees_calling_child_function,
    callees_calling_standalone_function,
    callees_calling_multiple_functions,
    empty_callees,
):
    """ProjectFacts with contracts that have various caller relationships."""
    
    # BaseContract with initialize() and baseFunction()
    base_contract = ContractModel(
        name="BaseContract",
        key=base_contract_key,
        path="contracts/Base.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[base_contract_key],
        functions_declared={
            "initialize()": FunctionModel(
                signature="initialize()",
                implementation_contract=base_contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Base.sol",
                line_start=10,
                line_end=15,
                callees=empty_callees,  # No one calls anything
            ),
            "baseFunction()": FunctionModel(
                signature="baseFunction()",
                implementation_contract=base_contract_key,
                solidity_modifiers=["internal", "view"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=["uint256"],
                path="contracts/Base.sol",
                line_start=17,
                line_end=20,
                callees=empty_callees,  # No one calls anything
            ),
        },
        functions_inherited={},
    )
    
    # ChildContract that calls baseFunction() internally
    child_contract = ContractModel(
        name="ChildContract",
        key=child_contract_key,
        path="contracts/Child.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[base_contract_key],
        scopes=[child_contract_key, base_contract_key],
        functions_declared={
            "childFunction(address)": FunctionModel(
                signature="childFunction(address)",
                implementation_contract=child_contract_key,
                solidity_modifiers=["public", "payable"],
                visibility="public",
                function_modifiers=["onlyOwner"],
                arguments=["address"],
                returns=[],
                path="contracts/Child.sol",
                line_start=12,
                line_end=18,
                callees=callees_calling_base_function,  # Calls baseFunction()
            ),
        },
        functions_inherited={
            "initialize()": FunctionModel(
                signature="initialize()",
                implementation_contract=base_contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Base.sol",
                line_start=10,
                line_end=15,
                callees=empty_callees,
            ),
            "baseFunction()": FunctionModel(
                signature="baseFunction()",
                implementation_contract=base_contract_key,
                solidity_modifiers=["internal", "view"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=["uint256"],
                path="contracts/Base.sol",
                line_start=17,
                line_end=20,
                callees=empty_callees,
            ),
        },
    )
    
    # GrandchildContract that calls childFunction() externally and multiple others
    grandchild_contract = ContractModel(
        name="GrandchildContract",
        key=grandchild_contract_key,
        path="contracts/Grandchild.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[child_contract_key],
        scopes=[grandchild_contract_key, child_contract_key, base_contract_key],
        functions_declared={
            "grandchildFunction()": FunctionModel(
                signature="grandchildFunction()",
                implementation_contract=grandchild_contract_key,
                solidity_modifiers=["external", "view"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=["bool"],
                path="contracts/Grandchild.sol",
                line_start=10,
                line_end=13,
                callees=callees_calling_multiple_functions,  # Calls multiple functions
            ),
            "anotherFunction()": FunctionModel(
                signature="anotherFunction()",
                implementation_contract=grandchild_contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Grandchild.sol",
                line_start=15,
                line_end=18,
                callees=callees_calling_child_function,  # Also calls childFunction()
            ),
        },
        functions_inherited={
            "childFunction(address)": FunctionModel(
                signature="childFunction(address)",
                implementation_contract=child_contract_key,
                solidity_modifiers=["public", "payable"],
                visibility="public",
                function_modifiers=["onlyOwner"],
                arguments=["address"],
                returns=[],
                path="contracts/Child.sol",
                line_start=12,
                line_end=18,
                callees=callees_calling_base_function,
            ),
            "initialize()": FunctionModel(
                signature="initialize()",
                implementation_contract=base_contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Base.sol",
                line_start=10,
                line_end=15,
                callees=empty_callees,
            ),
            "baseFunction()": FunctionModel(
                signature="baseFunction()",
                implementation_contract=base_contract_key,
                solidity_modifiers=["internal", "view"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=["uint256"],
                path="contracts/Base.sol",
                line_start=17,
                line_end=20,
                callees=empty_callees,
            ),
        },
    )
    
    # StandaloneContract with no callers
    standalone_contract = ContractModel(
        name="StandaloneContract",
        key=standalone_contract_key,
        path="contracts/Standalone.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[standalone_contract_key],
        functions_declared={
            "standaloneFunction(uint256,address)": FunctionModel(
                signature="standaloneFunction(uint256,address)",
                implementation_contract=standalone_contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=["nonReentrant"],
                arguments=["uint256", "address"],
                returns=["bool"],
                path="contracts/Standalone.sol",
                line_start=15,
                line_end=22,
                callees=empty_callees,  # Doesn't call anything
            ),
            "neverCalledFunction()": FunctionModel(
                signature="neverCalledFunction()",
                implementation_contract=standalone_contract_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Standalone.sol",
                line_start=24,
                line_end=26,
                callees=empty_callees,  # Doesn't call anything
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={
            base_contract_key: base_contract,
            child_contract_key: child_contract,
            grandchild_contract_key: grandchild_contract,
            standalone_contract_key: standalone_contract,
        },
        project_dir="/test/project",
    )


class TestListFunctionCallersHappyPath:
    """Test happy path scenarios for list_function_callers."""

    def test_function_with_no_callers(self, project_facts_with_callers):
        """Test getting callers for a function with no callers."""
        function_key = FunctionKey(
            signature="neverCalledFunction()",
            contract_name="StandaloneContract",
            path="contracts/Standalone.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.error_message is None
        assert response.callers is not None
        assert len(response.callers.internal_callers) == 0
        assert len(response.callers.external_callers) == 0
        assert len(response.callers.library_callers) == 0

    def test_function_with_single_internal_caller(self, project_facts_with_callers):
        """Test getting callers for a function with internal callers."""
        function_key = FunctionKey(
            signature="baseFunction()",
            contract_name="BaseContract",
            path="contracts/Base.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.error_message is None
        assert response.callers is not None
        
        # Should have 3 internal callers:
        # 1. ChildContract.childFunction(address) (declared)
        # 2. GrandchildContract.childFunction(address) (inherited, also calls it)
        # 3. GrandchildContract.grandchildFunction() (declared)
        assert len(response.callers.internal_callers) == 3
        
        # Verify the callers
        caller_sigs = {(c.contract_name, c.signature) for c in response.callers.internal_callers}
        assert ("ChildContract", "childFunction(address)") in caller_sigs
        assert ("GrandchildContract", "childFunction(address)") in caller_sigs
        assert ("GrandchildContract", "grandchildFunction()") in caller_sigs
        
        assert len(response.callers.external_callers) == 0
        assert len(response.callers.library_callers) == 0

    def test_function_with_external_callers(self, project_facts_with_callers):
        """Test getting callers for a function with external callers."""
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",
            path="contracts/Child.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.error_message is None
        assert response.callers is not None
        
        # Should have 2 external callers from GrandchildContract
        assert len(response.callers.external_callers) == 2
        
        # Verify the callers
        caller_sigs = {(c.contract_name, c.signature) for c in response.callers.external_callers}
        assert ("GrandchildContract", "grandchildFunction()") in caller_sigs
        assert ("GrandchildContract", "anotherFunction()") in caller_sigs
        
        assert len(response.callers.internal_callers) == 0
        assert len(response.callers.library_callers) == 0

    def test_function_with_library_callers(self, project_facts_with_callers):
        """Test getting callers for a function with library callers."""
        function_key = FunctionKey(
            signature="standaloneFunction(uint256,address)",
            contract_name="StandaloneContract",
            path="contracts/Standalone.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.error_message is None
        assert response.callers is not None
        
        # Should have 1 library caller from GrandchildContract.grandchildFunction()
        assert len(response.callers.library_callers) == 1
        
        caller = response.callers.library_callers[0]
        assert caller.contract_name == "GrandchildContract"
        assert caller.signature == "grandchildFunction()"
        
        assert len(response.callers.internal_callers) == 0
        assert len(response.callers.external_callers) == 0

    def test_function_with_multiple_caller_types(self, project_facts_with_callers):
        """Test that callers are properly grouped by call type."""
        # Test baseFunction which is called internally by multiple functions
        function_key = FunctionKey(
            signature="baseFunction()",
            contract_name="BaseContract",
            path="contracts/Base.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.callers is not None
        
        # Should have internal callers but no external or library
        assert len(response.callers.internal_callers) >= 1
        assert len(response.callers.external_callers) == 0
        assert len(response.callers.library_callers) == 0

    def test_query_context_is_populated(self, project_facts_with_callers):
        """Test that query context is properly populated in response."""
        function_key = FunctionKey(
            signature="baseFunction()",
            contract_name="BaseContract",
            path="contracts/Base.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.query_context is not None
        assert response.query_context.searched_calling_context is not None
        assert response.query_context.searched_function is not None
        assert "BaseContract.baseFunction()" in response.query_context.searched_function


class TestListFunctionCallersErrorCases:
    """Test error cases for list_function_callers."""

    def test_nonexistent_contract(self, project_facts_with_callers):
        """Test getting callers for a function in a non-existent contract."""
        function_key = FunctionKey(
            signature="someFunction()",
            contract_name="NonExistentContract",
            path="contracts/NonExistent.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is False
        assert response.error_message is not None
        assert "NonExistentContract" in response.error_message
        assert response.callers is None

    def test_nonexistent_function(self, project_facts_with_callers):
        """Test getting callers for a non-existent function."""
        function_key = FunctionKey(
            signature="nonExistentFunction()",
            contract_name="ChildContract",
            path="contracts/Child.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is False
        assert response.error_message is not None
        assert "nonExistentFunction()" in response.error_message
        assert response.callers is None

    def test_function_in_wrong_contract(self, project_facts_with_callers):
        """Test getting callers with function signature not matching the contract."""
        # Try to find childFunction in BaseContract (it doesn't exist there)
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="BaseContract",
            path="contracts/Base.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is False
        assert response.error_message is not None
        assert response.callers is None

    def test_empty_project(self, empty_project_facts):
        """Test getting callers in an empty project."""
        function_key = FunctionKey(
            signature="someFunction()",
            contract_name="SomeContract",
            path="contracts/Some.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, empty_project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert response.callers is None

    def test_wrong_path_for_contract(self, project_facts_with_callers):
        """Test getting callers with correct contract name but wrong path."""
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",
            path="contracts/WrongPath.sol",  # Wrong path
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is False
        assert response.error_message is not None
        assert response.callers is None


class TestListFunctionCallersEdgeCases:
    """Test edge cases for list_function_callers."""

    def test_function_with_complex_signature(self, project_facts):
        """Test function with complex type signature."""
        complex_contract_key = ContractKey(
            contract_name="ComplexContract",
            path="contracts/Complex.sol"
        )

        caller_contract_key = ContractKey(
            contract_name="CallerContract",
            path="contracts/Caller.sol"
        )

        # Create a complex function
        complex_contract = ContractModel(
            name="ComplexContract",
            key=complex_contract_key,
            path="contracts/Complex.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[complex_contract_key],
            functions_declared={
                "complexFunction(uint256[],address,(uint256,bool))": FunctionModel(
                    signature="complexFunction(uint256[],address,(uint256,bool))",
                    implementation_contract=complex_contract_key,
                    solidity_modifiers=["external"],
                    visibility="external",
                    function_modifiers=[],
                    arguments=["uint256[]", "address", "(uint256,bool)"],
                    returns=[],
                    path="contracts/Complex.sol",
                    line_start=10,
                    line_end=15,
                    callees=FunctionCallees(
                        internal_callees=[],
                        external_callees=[],
                        library_callees=[],
                        has_low_level_calls=False,
                    ),
                ),
            },
            functions_inherited={},
        )

        # Create a caller that calls the complex function
        caller_contract = ContractModel(
            name="CallerContract",
            key=caller_contract_key,
            path="contracts/Caller.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[caller_contract_key, complex_contract_key],
            functions_declared={
                "callerFunction()": FunctionModel(
                    signature="callerFunction()",
                    implementation_contract=caller_contract_key,
                    solidity_modifiers=["public"],
                    visibility="public",
                    function_modifiers=[],
                    arguments=[],
                    returns=[],
                    path="contracts/Caller.sol",
                    line_start=10,
                    line_end=15,
                    callees=FunctionCallees(
                        internal_callees=[],
                        external_callees=["ComplexContract.complexFunction(uint256[],address,(uint256,bool))"],
                        library_callees=[],
                        has_low_level_calls=False,
                    ),
                ),
            },
            functions_inherited={},
        )

        complex_facts = ProjectFacts(
            contracts={
                complex_contract_key: complex_contract,
                caller_contract_key: caller_contract,
            },
            project_dir="/test/project",
        )

        function_key = FunctionKey(
            signature="complexFunction(uint256[],address,(uint256,bool))",
            contract_name="ComplexContract",
            path="contracts/Complex.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, complex_facts)

        assert response.success is True
        assert response.callers is not None
        assert len(response.callers.external_callers) == 1
        assert response.callers.external_callers[0].signature == "callerFunction()"

    def test_no_duplicate_callers(self, project_facts_with_callers):
        """Test that duplicate callers are not included multiple times."""
        # Even if a function inherits and declares the same function,
        # it should only appear once in the callers list
        function_key = FunctionKey(
            signature="baseFunction()",
            contract_name="BaseContract",
            path="contracts/Base.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.callers is not None
        
        # Count occurrences of each caller
        internal_caller_keys = [
            (c.contract_name, c.signature) 
            for c in response.callers.internal_callers
        ]
        
        # Each unique caller should appear only once
        assert len(internal_caller_keys) == len(set(internal_caller_keys))

    def test_inherited_function_callers(self, project_facts_with_callers):
        """Test that callers work correctly with inherited functions."""
        # ChildContract's childFunction is inherited by GrandchildContract
        # and is called by GrandchildContract functions
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",
            path="contracts/Child.sol",
        )
        request = FunctionCallersRequest(function_key=function_key)
        response = list_function_callers(request, project_facts_with_callers)

        assert response.success is True
        assert response.callers is not None
        assert len(response.callers.external_callers) >= 1

