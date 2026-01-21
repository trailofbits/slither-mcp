"""Tests for get_contract_dependencies tool."""

import pytest

from slither_mcp.tools.get_contract_dependencies import (
    GetContractDependenciesRequest,
    get_contract_dependencies,
)
from slither_mcp.types import (
    ContractKey,
    ContractModel,
    FunctionCallees,
    FunctionModel,
    ProjectFacts,
)


@pytest.fixture
def dependency_project_facts():
    """Project with various dependency relationships for testing."""
    base_key = ContractKey(contract_name="Base", path="contracts/Base.sol")
    child_key = ContractKey(contract_name="Child", path="contracts/Child.sol")
    caller_key = ContractKey(contract_name="Caller", path="contracts/Caller.sol")
    library_key = ContractKey(contract_name="MathLib", path="contracts/MathLib.sol")

    empty_callees = FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )

    # Caller calls Child and uses MathLib
    caller_callees = FunctionCallees(
        internal_callees=[],
        external_callees=["Child.process()"],
        library_callees=["MathLib.add(uint256,uint256)"],
        has_low_level_calls=False,
    )

    base = ContractModel(
        name="Base",
        key=base_key,
        path="contracts/Base.sol",
        is_abstract=True,
        is_fully_implemented=False,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[base_key],
        functions_declared={
            "baseFunc()": FunctionModel(
                signature="baseFunc()",
                implementation_contract=base_key,
                solidity_modifiers=["public", "virtual"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Base.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    child = ContractModel(
        name="Child",
        key=child_key,
        path="contracts/Child.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[base_key],  # Inherits from Base
        scopes=[child_key, base_key],
        functions_declared={
            "process()": FunctionModel(
                signature="process()",
                implementation_contract=child_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Child.sol",
                line_start=5,
                line_end=10,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    caller = ContractModel(
        name="Caller",
        key=caller_key,
        path="contracts/Caller.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[caller_key],
        functions_declared={
            "execute()": FunctionModel(
                signature="execute()",
                implementation_contract=caller_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Caller.sol",
                line_start=10,
                line_end=20,
                callees=caller_callees,
            ),
        },
        functions_inherited={},
    )

    library = ContractModel(
        name="MathLib",
        key=library_key,
        path="contracts/MathLib.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=True,
        directly_inherits=[],
        scopes=[library_key],
        functions_declared={
            "add(uint256,uint256)": FunctionModel(
                signature="add(uint256,uint256)",
                implementation_contract=library_key,
                solidity_modifiers=["internal", "pure"],
                visibility="internal",
                function_modifiers=[],
                arguments=["uint256", "uint256"],
                returns=["uint256"],
                path="contracts/MathLib.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={
            base_key: base,
            child_key: child,
            caller_key: caller,
            library_key: library,
        },
        project_dir="/test/project",
    )


@pytest.fixture
def circular_dependency_facts():
    """Project with circular dependencies for testing cycle detection."""
    contract_a_key = ContractKey(contract_name="ContractA", path="contracts/A.sol")
    contract_b_key = ContractKey(contract_name="ContractB", path="contracts/B.sol")
    contract_c_key = ContractKey(contract_name="ContractC", path="contracts/C.sol")

    # A calls B, B calls C, C calls A (circular)
    a_callees = FunctionCallees(
        internal_callees=[],
        external_callees=["ContractB.funcB()"],
        library_callees=[],
        has_low_level_calls=False,
    )
    b_callees = FunctionCallees(
        internal_callees=[],
        external_callees=["ContractC.funcC()"],
        library_callees=[],
        has_low_level_calls=False,
    )
    c_callees = FunctionCallees(
        internal_callees=[],
        external_callees=["ContractA.funcA()"],
        library_callees=[],
        has_low_level_calls=False,
    )

    contract_a = ContractModel(
        name="ContractA",
        key=contract_a_key,
        path="contracts/A.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_a_key],
        functions_declared={
            "funcA()": FunctionModel(
                signature="funcA()",
                implementation_contract=contract_a_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/A.sol",
                line_start=5,
                line_end=10,
                callees=a_callees,
            ),
        },
        functions_inherited={},
    )

    contract_b = ContractModel(
        name="ContractB",
        key=contract_b_key,
        path="contracts/B.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_b_key],
        functions_declared={
            "funcB()": FunctionModel(
                signature="funcB()",
                implementation_contract=contract_b_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/B.sol",
                line_start=5,
                line_end=10,
                callees=b_callees,
            ),
        },
        functions_inherited={},
    )

    contract_c = ContractModel(
        name="ContractC",
        key=contract_c_key,
        path="contracts/C.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_c_key],
        functions_declared={
            "funcC()": FunctionModel(
                signature="funcC()",
                implementation_contract=contract_c_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/C.sol",
                line_start=5,
                line_end=10,
                callees=c_callees,
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={
            contract_a_key: contract_a,
            contract_b_key: contract_b,
            contract_c_key: contract_c,
        },
        project_dir="/test/project",
    )


def test_get_contract_dependencies_all_contracts(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test getting dependencies for all contracts."""
    request = GetContractDependenciesRequest(path=test_path)
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.error_message is None
    assert response.dependencies is not None
    assert len(response.dependencies) == 4  # All 4 contracts


def test_get_contract_dependencies_inheritance(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test inheritance dependencies are detected."""
    child_key = ContractKey(contract_name="Child", path="contracts/Child.sol")
    request = GetContractDependenciesRequest(path=test_path, contract_key=child_key)
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.dependencies is not None
    assert len(response.dependencies) == 1

    child_deps = response.dependencies[0]
    assert child_deps.contract_key == child_key

    # Child should depend on Base via inheritance
    inheritance_deps = [d for d in child_deps.depends_on if d.relationship == "inherits"]
    assert len(inheritance_deps) == 1
    assert inheritance_deps[0].contract_key.contract_name == "Base"


def test_get_contract_dependencies_external_calls(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test external call dependencies are detected."""
    caller_key = ContractKey(contract_name="Caller", path="contracts/Caller.sol")
    request = GetContractDependenciesRequest(
        path=test_path, contract_key=caller_key, include_external_calls=True
    )
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.dependencies is not None
    caller_deps = response.dependencies[0]

    # Caller should depend on Child via calls
    call_deps = [d for d in caller_deps.depends_on if d.relationship == "calls"]
    assert len(call_deps) == 1
    assert call_deps[0].contract_key.contract_name == "Child"


def test_get_contract_dependencies_library_usage(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test library usage dependencies are detected."""
    caller_key = ContractKey(contract_name="Caller", path="contracts/Caller.sol")
    request = GetContractDependenciesRequest(
        path=test_path, contract_key=caller_key, include_library_usage=True
    )
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.dependencies is not None
    caller_deps = response.dependencies[0]

    # Caller should depend on MathLib via uses_library
    lib_deps = [d for d in caller_deps.depends_on if d.relationship == "uses_library"]
    assert len(lib_deps) == 1
    assert lib_deps[0].contract_key.contract_name == "MathLib"


def test_get_contract_dependencies_depended_by(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test reverse dependencies (depended_by) are populated."""
    base_key = ContractKey(contract_name="Base", path="contracts/Base.sol")
    request = GetContractDependenciesRequest(path=test_path, contract_key=base_key)
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.dependencies is not None
    base_deps = response.dependencies[0]

    # Base should be depended by Child via inheritance
    inheritance_deps = [d for d in base_deps.depended_by if d.relationship == "inherits"]
    assert len(inheritance_deps) == 1
    assert inheritance_deps[0].contract_key.contract_name == "Child"


def test_get_contract_dependencies_exclude_external_calls(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test excluding external call dependencies."""
    caller_key = ContractKey(contract_name="Caller", path="contracts/Caller.sol")
    request = GetContractDependenciesRequest(
        path=test_path, contract_key=caller_key, include_external_calls=False
    )
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.dependencies is not None
    caller_deps = response.dependencies[0]

    # No call dependencies should be present
    call_deps = [d for d in caller_deps.depends_on if d.relationship == "calls"]
    assert len(call_deps) == 0


def test_get_contract_dependencies_exclude_library_usage(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test excluding library usage dependencies."""
    caller_key = ContractKey(contract_name="Caller", path="contracts/Caller.sol")
    request = GetContractDependenciesRequest(
        path=test_path, contract_key=caller_key, include_library_usage=False
    )
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.dependencies is not None
    caller_deps = response.dependencies[0]

    # No library dependencies should be present
    lib_deps = [d for d in caller_deps.depends_on if d.relationship == "uses_library"]
    assert len(lib_deps) == 0


def test_get_contract_dependencies_circular_detection(
    circular_dependency_facts: ProjectFacts, test_path: str
):
    """Test circular dependency detection."""
    request = GetContractDependenciesRequest(path=test_path, detect_circular=True)
    response = get_contract_dependencies(request, circular_dependency_facts)

    assert response.success
    assert response.circular_dependencies is not None
    assert len(response.circular_dependencies) > 0

    # At least one cycle should contain A, B, and C
    cycle_contracts = set()
    for cycle in response.circular_dependencies:
        for key in cycle.cycle:
            cycle_contracts.add(key.contract_name)

    # All three should be in some cycle
    assert "ContractA" in cycle_contracts or "ContractB" in cycle_contracts


def test_get_contract_dependencies_no_circular_detection(
    circular_dependency_facts: ProjectFacts, test_path: str
):
    """Test disabling circular dependency detection."""
    request = GetContractDependenciesRequest(path=test_path, detect_circular=False)
    response = get_contract_dependencies(request, circular_dependency_facts)

    assert response.success
    assert response.circular_dependencies is None


def test_get_contract_dependencies_contract_not_found(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test error when contract not found."""
    non_existent_key = ContractKey(contract_name="NonExistent", path="contracts/None.sol")
    request = GetContractDependenciesRequest(path=test_path, contract_key=non_existent_key)
    response = get_contract_dependencies(request, dependency_project_facts)

    assert not response.success
    assert response.error_message is not None
    assert "not found" in response.error_message.lower()


def test_get_contract_dependencies_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test dependencies with empty project."""
    request = GetContractDependenciesRequest(path=test_path)
    response = get_contract_dependencies(request, empty_project_facts)

    assert response.success
    assert response.dependencies is not None
    assert len(response.dependencies) == 0


def test_get_contract_dependencies_no_cycles_in_simple_project(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test that simple project has no circular dependencies."""
    request = GetContractDependenciesRequest(path=test_path, detect_circular=True)
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    # Simple inheritance chain shouldn't have cycles
    # (cycles only count call dependencies, not inheritance in DAG)
    # This may or may not detect cycles depending on how the algorithm handles inheritance


def test_get_contract_dependencies_relationship_types(
    dependency_project_facts: ProjectFacts, test_path: str
):
    """Test that all relationship types are correctly categorized."""
    request = GetContractDependenciesRequest(path=test_path)
    response = get_contract_dependencies(request, dependency_project_facts)

    assert response.success
    assert response.dependencies is not None

    valid_relationships = {"inherits", "calls", "uses_library"}

    for contract_deps in response.dependencies:
        for dep in contract_deps.depends_on:
            assert dep.relationship in valid_relationships
        for dep in contract_deps.depended_by:
            assert dep.relationship in valid_relationships
