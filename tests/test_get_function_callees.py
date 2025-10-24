"""Tests for list_function_callees tool."""

import pytest
from slither_mcp.tools.list_function_callees import (
    FunctionCalleesRequest,
    list_function_callees,
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
def callees_with_internal():
    """FunctionCallees with internal calls."""
    return FunctionCallees(
        internal_callees=["BaseContract.baseFunction()"],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )


@pytest.fixture
def callees_with_external():
    """FunctionCallees with external calls."""
    return FunctionCallees(
        internal_callees=[],
        external_callees=["ChildContract.childFunction(address)"],
        library_callees=[],
        has_low_level_calls=False,
    )


@pytest.fixture
def callees_with_library():
    """FunctionCallees with library calls."""
    return FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=["LibraryB.add(uint256,uint256)"],
        has_low_level_calls=False,
    )


@pytest.fixture
def callees_with_all_types():
    """FunctionCallees with internal, external, and library calls."""
    return FunctionCallees(
        internal_callees=["BaseContract.baseFunction()", "BaseContract.initialize()"],
        external_callees=["ChildContract.childFunction(address)"],
        library_callees=["LibraryB.add(uint256,uint256)"],
        has_low_level_calls=True,
    )


@pytest.fixture
def callees_with_low_level():
    """FunctionCallees with low level calls."""
    return FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=True,
    )


@pytest.fixture
def child_with_callees(child_contract_key, base_contract_key, callees_with_internal, empty_callees):
    """ChildContract with functions that have callees."""
    return ContractModel(
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
                callees=callees_with_internal,  # Calls baseFunction
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


@pytest.fixture
def grandchild_with_complex_callees(
    grandchild_contract_key,
    child_contract_key,
    base_contract_key,
    callees_with_all_types,
    callees_with_internal,
    empty_callees,
):
    """GrandchildContract with complex callees including all types."""
    return ContractModel(
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
                callees=callees_with_all_types,  # Complex callees
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
                callees=callees_with_internal,
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


@pytest.fixture
def project_facts_with_callees(
    base_contract,
    child_with_callees,
    grandchild_with_complex_callees,
    standalone_contract,
    base_contract_key,
    child_contract_key,
    grandchild_contract_key,
    standalone_contract_key,
):
    """ProjectFacts with contracts that have callees."""
    return ProjectFacts(
        contracts={
            base_contract_key: base_contract,
            child_contract_key: child_with_callees,
            grandchild_contract_key: grandchild_with_complex_callees,
            standalone_contract_key: standalone_contract,
        },
        project_dir="/test/project",
    )


class TestListFunctionCalleesHappyPath:
    """Test happy path scenarios for list_function_callees."""

    def test_function_with_no_callees(self, project_facts_with_callees, base_contract_key):
        """Test getting callees for a function with no callees."""
        function_key = FunctionKey(
            signature="initialize()",
            contract_name="BaseContract",
            path="contracts/Base.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is True
        assert response.error_message is None
        assert response.callees is not None
        assert len(response.callees.internal_callees) == 0
        assert len(response.callees.external_callees) == 0
        assert len(response.callees.library_callees) == 0
        assert response.callees.has_low_level_calls is False

    def test_function_with_internal_callees(self, project_facts_with_callees, child_contract_key):
        """Test getting callees for a function with internal calls."""
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",
            path="contracts/Child.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is True
        assert response.error_message is None
        assert response.callees is not None
        assert len(response.callees.internal_callees) == 1
        assert "BaseContract.baseFunction()" in response.callees.internal_callees
        assert len(response.callees.external_callees) == 0
        assert len(response.callees.library_callees) == 0

    def test_function_with_all_callee_types(
        self, project_facts_with_callees, grandchild_contract_key
    ):
        """Test getting callees for a function with internal, external, and library calls."""
        function_key = FunctionKey(
            signature="grandchildFunction()",
            contract_name="GrandchildContract",
            path="contracts/Grandchild.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is True
        assert response.error_message is None
        assert response.callees is not None

        # Check internal callees
        assert len(response.callees.internal_callees) == 2
        assert "BaseContract.baseFunction()" in response.callees.internal_callees
        assert "BaseContract.initialize()" in response.callees.internal_callees

        # Check external callees
        assert len(response.callees.external_callees) == 1
        assert "ChildContract.childFunction(address)" in response.callees.external_callees

        # Check library callees
        assert len(response.callees.library_callees) == 1
        assert "LibraryB.add(uint256,uint256)" in response.callees.library_callees

        # Check low-level calls flag
        assert response.callees.has_low_level_calls is True

    def test_function_with_low_level_calls_only(self, project_facts):
        """Test function that only has low-level calls."""
        # Use standalone contract but with low-level calls
        from slither_mcp.types import FunctionCallees

        low_level_callees = FunctionCallees(
            internal_callees=[],
            external_callees=[],
            library_callees=[],
            has_low_level_calls=True,
        )

        standalone_key = ContractKey(
            contract_name="StandaloneContract",
            path="contracts/Standalone.sol"
        )

        modified_standalone = ContractModel(
            name="StandaloneContract",
            key=standalone_key,
            path="contracts/Standalone.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[standalone_key],
            functions_declared={
                "standaloneFunction(uint256,address)": FunctionModel(
                    signature="standaloneFunction(uint256,address)",
                    implementation_contract=standalone_key,
                    solidity_modifiers=["public"],
                    visibility="public",
                    function_modifiers=["nonReentrant"],
                    arguments=["uint256", "address"],
                    returns=["bool"],
                    path="contracts/Standalone.sol",
                    line_start=15,
                    line_end=22,
                    callees=low_level_callees,
                ),
            },
            functions_inherited={},
        )

        modified_facts = ProjectFacts(
            contracts={standalone_key: modified_standalone},
            project_dir="/test/project",
        )

        function_key = FunctionKey(
            signature="standaloneFunction(uint256,address)",
            contract_name="StandaloneContract",
            path="contracts/Standalone.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, modified_facts)

        assert response.success is True
        assert response.callees is not None
        assert response.callees.has_low_level_calls is True
        assert len(response.callees.internal_callees) == 0
        assert len(response.callees.external_callees) == 0
        assert len(response.callees.library_callees) == 0

    def test_inherited_function_callees(
        self, project_facts_with_callees, grandchild_contract_key
    ):
        """Test getting callees for an inherited function."""
        # Query childFunction which is inherited by GrandchildContract
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",  # Implemented in ChildContract
            path="contracts/Child.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is True
        assert response.error_message is None
        assert response.callees is not None
        assert len(response.callees.internal_callees) == 1
        assert "BaseContract.baseFunction()" in response.callees.internal_callees

    def test_query_context_is_populated(self, project_facts_with_callees, child_contract_key):
        """Test that query context is properly populated in response."""
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",
            path="contracts/Child.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is True
        assert response.query_context is not None
        assert response.query_context.searched_calling_context is not None
        assert response.query_context.searched_function is not None
        assert "ChildContract.childFunction(address)" in response.query_context.searched_function


class TestListFunctionCalleesErrorCases:
    """Test error cases for list_function_callees."""

    def test_nonexistent_contract(self, project_facts_with_callees):
        """Test getting callees for a function in a non-existent contract."""
        function_key = FunctionKey(
            signature="someFunction()",
            contract_name="NonExistentContract",
            path="contracts/NonExistent.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is False
        assert response.error_message is not None
        assert "NonExistentContract" in response.error_message
        assert response.callees is None

    def test_nonexistent_function(self, project_facts_with_callees, child_contract_key):
        """Test getting callees for a non-existent function."""
        function_key = FunctionKey(
            signature="nonExistentFunction()",
            contract_name="ChildContract",
            path="contracts/Child.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is False
        assert response.error_message is not None
        assert "nonExistentFunction()" in response.error_message
        assert response.callees is None

    def test_function_in_wrong_contract(self, project_facts_with_callees):
        """Test getting callees with function signature not matching the contract."""
        # Try to find childFunction in BaseContract (it doesn't exist there)
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="BaseContract",
            path="contracts/Base.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is False
        assert response.error_message is not None
        assert response.callees is None

    def test_empty_project(self, empty_project_facts):
        """Test getting callees in an empty project."""
        function_key = FunctionKey(
            signature="someFunction()",
            contract_name="SomeContract",
            path="contracts/Some.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, empty_project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert response.callees is None

    def test_wrong_path_for_contract(self, project_facts_with_callees):
        """Test getting callees with correct contract name but wrong path."""
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",
            path="contracts/WrongPath.sol",  # Wrong path
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, project_facts_with_callees)

        assert response.success is False
        assert response.error_message is not None
        assert response.callees is None


class TestListFunctionCalleesEdgeCases:
    """Test edge cases for list_function_callees."""

    def test_function_with_complex_signature(self, project_facts):
        """Test function with complex type signature."""
        complex_contract_key = ContractKey(
            contract_name="ComplexContract",
            path="contracts/Complex.sol"
        )

        complex_callees = FunctionCallees(
            internal_callees=[],
            external_callees=[],
            library_callees=[],
            has_low_level_calls=False,
        )

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
                    callees=complex_callees,
                ),
            },
            functions_inherited={},
        )

        complex_facts = ProjectFacts(
            contracts={complex_contract_key: complex_contract},
            project_dir="/test/project",
        )

        function_key = FunctionKey(
            signature="complexFunction(uint256[],address,(uint256,bool))",
            contract_name="ComplexContract",
            path="contracts/Complex.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, complex_facts)

        assert response.success is True
        assert response.callees is not None

    def test_overloaded_function(self, project_facts):
        """Test function with overloaded signatures."""
        overload_key = ContractKey(
            contract_name="OverloadContract",
            path="contracts/Overload.sol"
        )

        empty_callees = FunctionCallees(
            internal_callees=[],
            external_callees=[],
            library_callees=[],
            has_low_level_calls=False,
        )

        overload_contract = ContractModel(
            name="OverloadContract",
            key=overload_key,
            path="contracts/Overload.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[overload_key],
            functions_declared={
                "transfer(address)": FunctionModel(
                    signature="transfer(address)",
                    implementation_contract=overload_key,
                    solidity_modifiers=["public"],
                    visibility="public",
                    function_modifiers=[],
                    arguments=["address"],
                    returns=[],
                    path="contracts/Overload.sol",
                    line_start=10,
                    line_end=12,
                    callees=empty_callees,
                ),
                "transfer(address,uint256)": FunctionModel(
                    signature="transfer(address,uint256)",
                    implementation_contract=overload_key,
                    solidity_modifiers=["public"],
                    visibility="public",
                    function_modifiers=[],
                    arguments=["address", "uint256"],
                    returns=[],
                    path="contracts/Overload.sol",
                    line_start=14,
                    line_end=16,
                    callees=empty_callees,
                ),
            },
            functions_inherited={},
        )

        overload_facts = ProjectFacts(
            contracts={overload_key: overload_contract},
            project_dir="/test/project",
        )

        # Test first overload
        function_key1 = FunctionKey(
            signature="transfer(address)",
            contract_name="OverloadContract",
            path="contracts/Overload.sol",
        )
        request1 = FunctionCalleesRequest(function_key=function_key1)
        response1 = list_function_callees(request1, overload_facts)
        assert response1.success is True

        # Test second overload
        function_key2 = FunctionKey(
            signature="transfer(address,uint256)",
            contract_name="OverloadContract",
            path="contracts/Overload.sol",
        )
        request2 = FunctionCalleesRequest(function_key=function_key2)
        response2 = list_function_callees(request2, overload_facts)
        assert response2.success is True

    def test_constructor_function(self, project_facts):
        """Test getting callees for constructor."""
        constructor_key = ContractKey(
            contract_name="ConstructorContract",
            path="contracts/Constructor.sol"
        )

        constructor_callees = FunctionCallees(
            internal_callees=["ConstructorContract._initialize()"],
            external_callees=[],
            library_callees=[],
            has_low_level_calls=False,
        )

        constructor_contract = ContractModel(
            name="ConstructorContract",
            key=constructor_key,
            path="contracts/Constructor.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[constructor_key],
            functions_declared={
                "constructor()": FunctionModel(
                    signature="constructor()",
                    implementation_contract=constructor_key,
                    solidity_modifiers=["public"],
                    visibility="public",
                    function_modifiers=[],
                    arguments=[],
                    returns=[],
                    path="contracts/Constructor.sol",
                    line_start=10,
                    line_end=13,
                    callees=constructor_callees,
                ),
                "_initialize()": FunctionModel(
                    signature="_initialize()",
                    implementation_contract=constructor_key,
                    solidity_modifiers=["internal"],
                    visibility="internal",
                    function_modifiers=[],
                    arguments=[],
                    returns=[],
                    path="contracts/Constructor.sol",
                    line_start=15,
                    line_end=18,
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

        constructor_facts = ProjectFacts(
            contracts={constructor_key: constructor_contract},
            project_dir="/test/project",
        )

        function_key = FunctionKey(
            signature="constructor()",
            contract_name="ConstructorContract",
            path="contracts/Constructor.sol",
        )
        request = FunctionCalleesRequest(function_key=function_key)
        response = list_function_callees(request, constructor_facts)

        assert response.success is True
        assert response.callees is not None
        assert len(response.callees.internal_callees) == 1
        assert "ConstructorContract._initialize()" in response.callees.internal_callees

