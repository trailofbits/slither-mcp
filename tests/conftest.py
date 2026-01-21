"""Shared pytest fixtures for slither-mcp tests."""

import pytest

from slither_mcp.types import (
    ContractKey,
    ContractModel,
    DetectorMetadata,
    DetectorResult,
    EventModel,
    EventParameter,
    FunctionCallees,
    FunctionModel,
    ProjectFacts,
    SourceLocation,
    StateVariableModel,
)


@pytest.fixture
def test_path():
    """Default test project path for use in tool requests."""
    return "/test/project"


@pytest.fixture
def base_contract_key():
    """ContractKey for BaseContract."""
    return ContractKey(contract_name="BaseContract", path="contracts/Base.sol")


@pytest.fixture
def interface_a_key():
    """ContractKey for InterfaceA."""
    return ContractKey(contract_name="InterfaceA", path="contracts/IInterface.sol")


@pytest.fixture
def library_b_key():
    """ContractKey for LibraryB."""
    return ContractKey(contract_name="LibraryB", path="contracts/Library.sol")


@pytest.fixture
def child_contract_key():
    """ContractKey for ChildContract."""
    return ContractKey(contract_name="ChildContract", path="contracts/Child.sol")


@pytest.fixture
def grandchild_contract_key():
    """ContractKey for GrandchildContract."""
    return ContractKey(contract_name="GrandchildContract", path="contracts/Grandchild.sol")


@pytest.fixture
def multi_inherit_contract_key():
    """ContractKey for MultiInheritContract."""
    return ContractKey(contract_name="MultiInheritContract", path="contracts/Multi.sol")


@pytest.fixture
def standalone_contract_key():
    """ContractKey for StandaloneContract."""
    return ContractKey(contract_name="StandaloneContract", path="contracts/Standalone.sol")


@pytest.fixture
def empty_callees():
    """Empty FunctionCallees for test functions."""
    return FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )


@pytest.fixture
def base_contract(base_contract_key, empty_callees):
    """Mock BaseContract - abstract base contract."""
    return ContractModel(
        name="BaseContract",
        key=base_contract_key,
        path="contracts/Base.sol",
        is_abstract=True,
        is_fully_implemented=False,
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
        functions_inherited={},
        state_variables=[
            StateVariableModel(
                name="owner",
                type_str="address",
                visibility="internal",
                is_constant=False,
                is_immutable=False,
                line_number=5,
            ),
            StateVariableModel(
                name="VERSION",
                type_str="uint256",
                visibility="public",
                is_constant=True,
                is_immutable=False,
                line_number=6,
            ),
        ],
        events=[
            EventModel(
                name="Initialized",
                parameters=[
                    EventParameter(name="version", type_str="uint256", indexed=True),
                ],
                line_number=8,
            ),
        ],
    )


@pytest.fixture
def interface_a(interface_a_key, empty_callees):
    """Mock InterfaceA - interface contract."""
    return ContractModel(
        name="InterfaceA",
        key=interface_a_key,
        path="contracts/IInterface.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=True,
        is_library=False,
        directly_inherits=[],
        scopes=[interface_a_key],
        functions_declared={
            "interfaceMethod()": FunctionModel(
                signature="interfaceMethod()",
                implementation_contract=interface_a_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/IInterface.sol",
                line_start=5,
                line_end=5,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )


@pytest.fixture
def library_b(library_b_key, empty_callees):
    """Mock LibraryB - library contract."""
    return ContractModel(
        name="LibraryB",
        key=library_b_key,
        path="contracts/Library.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=True,
        directly_inherits=[],
        scopes=[library_b_key],
        functions_declared={
            "add(uint256,uint256)": FunctionModel(
                signature="add(uint256,uint256)",
                implementation_contract=library_b_key,
                solidity_modifiers=["internal", "pure"],
                visibility="internal",
                function_modifiers=[],
                arguments=["uint256", "uint256"],
                returns=["uint256"],
                path="contracts/Library.sol",
                line_start=7,
                line_end=10,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )


@pytest.fixture
def child_contract(child_contract_key, base_contract_key, base_contract, empty_callees):
    """Mock ChildContract - concrete contract inheriting from BaseContract."""
    # FunctionCallees with low-level call for testing
    callees_with_low_level = FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=True,
    )
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
                callees=empty_callees,
            ),
            "sendFunds(address,uint256)": FunctionModel(
                signature="sendFunds(address,uint256)",
                implementation_contract=child_contract_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=["onlyOwner", "nonReentrant"],
                arguments=["address", "uint256"],
                returns=["bool"],
                path="contracts/Child.sol",
                line_start=20,
                line_end=30,
                callees=callees_with_low_level,
            ),
        },
        functions_inherited={
            "initialize()": base_contract.functions_declared["initialize()"],
            "baseFunction()": base_contract.functions_declared["baseFunction()"],
        },
        state_variables=[
            StateVariableModel(
                name="balance",
                type_str="uint256",
                visibility="public",
                is_constant=False,
                is_immutable=False,
                line_number=8,
            ),
            StateVariableModel(
                name="deployTime",
                type_str="uint256",
                visibility="private",
                is_constant=False,
                is_immutable=True,
                line_number=9,
            ),
        ],
        events=[
            EventModel(
                name="Transfer",
                parameters=[
                    EventParameter(name="from", type_str="address", indexed=True),
                    EventParameter(name="to", type_str="address", indexed=True),
                    EventParameter(name="amount", type_str="uint256", indexed=False),
                ],
                line_number=6,
            ),
        ],
    )


@pytest.fixture
def grandchild_contract(
    grandchild_contract_key,
    child_contract_key,
    base_contract_key,
    child_contract,
    base_contract,
    empty_callees,
):
    """Mock GrandchildContract - concrete contract inheriting from ChildContract."""
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
                callees=empty_callees,
            ),
        },
        functions_inherited={
            "childFunction(address)": child_contract.functions_declared["childFunction(address)"],
            "initialize()": base_contract.functions_declared["initialize()"],
            "baseFunction()": base_contract.functions_declared["baseFunction()"],
        },
    )


@pytest.fixture
def multi_inherit_contract(
    multi_inherit_contract_key,
    base_contract_key,
    interface_a_key,
    base_contract,
    interface_a,
    empty_callees,
):
    """Mock MultiInheritContract - contract with multiple inheritance."""
    return ContractModel(
        name="MultiInheritContract",
        key=multi_inherit_contract_key,
        path="contracts/Multi.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[base_contract_key, interface_a_key],
        scopes=[multi_inherit_contract_key, base_contract_key, interface_a_key],
        functions_declared={
            "interfaceMethod()": FunctionModel(
                signature="interfaceMethod()",
                implementation_contract=multi_inherit_contract_key,
                solidity_modifiers=["external", "override"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Multi.sol",
                line_start=8,
                line_end=11,
                callees=empty_callees,
            ),
            "multiFunction()": FunctionModel(
                signature="multiFunction()",
                implementation_contract=multi_inherit_contract_key,
                solidity_modifiers=["private"],
                visibility="private",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Multi.sol",
                line_start=13,
                line_end=16,
                callees=empty_callees,
            ),
        },
        functions_inherited={
            "initialize()": base_contract.functions_declared["initialize()"],
            "baseFunction()": base_contract.functions_declared["baseFunction()"],
        },
    )


@pytest.fixture
def standalone_contract(standalone_contract_key, empty_callees):
    """Mock StandaloneContract - contract with no inheritance."""
    return ContractModel(
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
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )


@pytest.fixture
def empty_contract_key():
    """ContractKey for EmptyContract."""
    return ContractKey(contract_name="EmptyContract", path="contracts/Empty.sol")


@pytest.fixture
def empty_contract(empty_contract_key):
    """Mock EmptyContract - contract with no functions."""
    return ContractModel(
        name="EmptyContract",
        key=empty_contract_key,
        path="contracts/Empty.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[empty_contract_key],
        functions_declared={},
        functions_inherited={},
    )


@pytest.fixture
def project_facts(
    base_contract,
    interface_a,
    library_b,
    child_contract,
    grandchild_contract,
    multi_inherit_contract,
    standalone_contract,
    empty_contract,
    base_contract_key,
    interface_a_key,
    library_b_key,
    child_contract_key,
    grandchild_contract_key,
    multi_inherit_contract_key,
    standalone_contract_key,
    empty_contract_key,
):
    """Complete ProjectFacts with all mock contracts."""
    return ProjectFacts(
        contracts={
            base_contract_key: base_contract,
            interface_a_key: interface_a,
            library_b_key: library_b,
            child_contract_key: child_contract,
            grandchild_contract_key: grandchild_contract,
            multi_inherit_contract_key: multi_inherit_contract,
            standalone_contract_key: standalone_contract,
            empty_contract_key: empty_contract,
        },
        project_dir="/test/project",
    )


@pytest.fixture
def empty_project_facts():
    """Empty ProjectFacts for edge case testing."""
    return ProjectFacts(contracts={}, project_dir="/test/empty")


@pytest.fixture
def detector_metadata_list():
    """List of mock detector metadata."""
    return [
        DetectorMetadata(
            name="reentrancy-eth",
            description="Reentrancy vulnerabilities (theft of ethers)",
            impact="High",
            confidence="Medium",
        ),
        DetectorMetadata(
            name="uninitialized-storage",
            description="Uninitialized storage variables",
            impact="High",
            confidence="High",
        ),
        DetectorMetadata(
            name="naming-convention",
            description="Conformity to Solidity naming conventions",
            impact="Informational",
            confidence="High",
        ),
        DetectorMetadata(
            name="solc-version",
            description="Incorrect Solidity version",
            impact="Informational",
            confidence="High",
        ),
    ]


@pytest.fixture
def detector_results_dict():
    """Dictionary of mock detector results."""
    return {
        "reentrancy-eth": [
            DetectorResult(
                detector_name="reentrancy-eth",
                check="reentrancy-eth",
                impact="High",
                confidence="Medium",
                description="Reentrancy in Contract.withdraw() (contracts/Contract.sol#5-10)",
                source_locations=[
                    SourceLocation(file_path="contracts/Contract.sol", start_line=5, end_line=10)
                ],
            )
        ],
        "uninitialized-storage": [
            DetectorResult(
                detector_name="uninitialized-storage",
                check="uninitialized-storage",
                impact="High",
                confidence="High",
                description="Contract.storageVar (contracts/Contract.sol#3) is never initialized",
                source_locations=[
                    SourceLocation(file_path="contracts/Contract.sol", start_line=3, end_line=3)
                ],
            )
        ],
        "naming-convention": [
            DetectorResult(
                detector_name="naming-convention",
                check="naming-convention",
                impact="Informational",
                confidence="High",
                description="Parameter 'MyContract._value' (contracts/Contract.sol#15) is not in mixedCase",
                source_locations=[
                    SourceLocation(file_path="contracts/Contract.sol", start_line=15, end_line=15)
                ],
            ),
            DetectorResult(
                detector_name="naming-convention",
                check="naming-convention",
                impact="Informational",
                confidence="High",
                description="Function 'MyContract.DoSomething' (contracts/Contract.sol#20-25) is not in mixedCase",
                source_locations=[
                    SourceLocation(file_path="contracts/Contract.sol", start_line=20, end_line=25)
                ],
            ),
        ],
    }


@pytest.fixture
def project_facts_with_detectors(
    base_contract,
    child_contract,
    base_contract_key,
    child_contract_key,
    detector_metadata_list,
    detector_results_dict,
):
    """ProjectFacts with detector data for testing detector tools."""
    return ProjectFacts(
        contracts={
            base_contract_key: base_contract,
            child_contract_key: child_contract,
        },
        project_dir="/test/project",
        detector_results=detector_results_dict,
        available_detectors=detector_metadata_list,
    )


# Fixtures for testing exclude_paths feature


@pytest.fixture
def lib_contract_key():
    """ContractKey for a contract in lib/ directory."""
    return ContractKey(contract_name="LibDependency", path="lib/dependency/src/Dependency.sol")


@pytest.fixture
def test_contract_key():
    """ContractKey for a contract in test/ directory."""
    return ContractKey(contract_name="TestHelper", path="test/helpers/TestHelper.sol")


@pytest.fixture
def lib_contract(lib_contract_key, empty_callees):
    """Mock contract in lib/ directory."""
    return ContractModel(
        name="LibDependency",
        key=lib_contract_key,
        path="lib/dependency/src/Dependency.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=True,
        directly_inherits=[],
        scopes=[lib_contract_key],
        functions_declared={
            "helperFunction()": FunctionModel(
                signature="helperFunction()",
                implementation_contract=lib_contract_key,
                solidity_modifiers=["internal", "pure"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=["uint256"],
                path="lib/dependency/src/Dependency.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )


@pytest.fixture
def test_helper_contract(test_contract_key, empty_callees):
    """Mock contract in test/ directory."""
    return ContractModel(
        name="TestHelper",
        key=test_contract_key,
        path="test/helpers/TestHelper.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[test_contract_key],
        functions_declared={
            "setUp()": FunctionModel(
                signature="setUp()",
                implementation_contract=test_contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="test/helpers/TestHelper.sol",
                line_start=5,
                line_end=10,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )


@pytest.fixture
def project_facts_with_lib_and_test(
    project_facts,
    lib_contract,
    test_helper_contract,
    lib_contract_key,
    test_contract_key,
):
    """ProjectFacts with contracts in lib/ and test/ directories for exclude_paths testing."""
    contracts = dict(project_facts.contracts)
    contracts[lib_contract_key] = lib_contract
    contracts[test_contract_key] = test_helper_contract
    return ProjectFacts(
        contracts=contracts,
        project_dir="/test/project",
        detector_results=project_facts.detector_results,
        available_detectors=project_facts.available_detectors,
    )


@pytest.fixture
def detector_results_with_test_findings():
    """Detector results that include findings in test and lib directories."""
    return {
        "reentrancy-eth": [
            DetectorResult(
                detector_name="reentrancy-eth",
                check="reentrancy-eth",
                impact="High",
                confidence="Medium",
                description="Reentrancy in Contract.withdraw()",
                source_locations=[
                    SourceLocation(file_path="contracts/Contract.sol", start_line=5, end_line=10)
                ],
            )
        ],
        "uninitialized-storage": [
            DetectorResult(
                detector_name="uninitialized-storage",
                check="uninitialized-storage",
                impact="High",
                confidence="High",
                description="Test helper has uninitialized storage",
                source_locations=[
                    SourceLocation(file_path="test/helpers/TestHelper.sol", start_line=3, end_line=3)
                ],
            ),
            DetectorResult(
                detector_name="uninitialized-storage",
                check="uninitialized-storage",
                impact="High",
                confidence="High",
                description="Lib dependency has uninitialized storage",
                source_locations=[
                    SourceLocation(
                        file_path="lib/dependency/src/Dependency.sol", start_line=2, end_line=2
                    )
                ],
            ),
        ],
    }


@pytest.fixture
def project_facts_with_detector_findings_in_test(
    project_facts_with_lib_and_test,
    detector_results_with_test_findings,
    detector_metadata_list,
):
    """ProjectFacts with detector findings in test/lib directories."""
    return ProjectFacts(
        contracts=project_facts_with_lib_and_test.contracts,
        project_dir="/test/project",
        detector_results=detector_results_with_test_findings,
        available_detectors=detector_metadata_list,
    )
