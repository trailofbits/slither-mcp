"""Tests for find_dead_code tool."""

import pytest

from slither_mcp.tools.find_dead_code import (
    FindDeadCodeRequest,
    find_dead_code,
)
from slither_mcp.types import (
    ContractKey,
    ContractModel,
    FunctionCallees,
    FunctionModel,
    ProjectFacts,
)


@pytest.fixture
def dead_code_project_facts():
    """Project with dead code scenarios for testing."""
    contract_a_key = ContractKey(contract_name="ContractA", path="contracts/A.sol")
    contract_b_key = ContractKey(contract_name="ContractB", path="contracts/B.sol")

    # ContractA has functions that call ContractB
    callees_calling_b = FunctionCallees(
        internal_callees=[],
        external_callees=["ContractB.helperFunction()"],
        library_callees=[],
        has_low_level_calls=False,
    )

    empty_callees = FunctionCallees(
        internal_callees=[],
        external_callees=[],
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
            "publicCaller()": FunctionModel(
                signature="publicCaller()",
                implementation_contract=contract_a_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/A.sol",
                line_start=5,
                line_end=10,
                callees=callees_calling_b,
            ),
            "unusedPrivate()": FunctionModel(
                signature="unusedPrivate()",
                implementation_contract=contract_a_key,
                solidity_modifiers=["private"],
                visibility="private",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/A.sol",
                line_start=12,
                line_end=15,
                callees=empty_callees,
            ),
            "unusedInternal()": FunctionModel(
                signature="unusedInternal()",
                implementation_contract=contract_a_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/A.sol",
                line_start=17,
                line_end=20,
                callees=empty_callees,
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
            "helperFunction()": FunctionModel(
                signature="helperFunction()",
                implementation_contract=contract_b_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/B.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
            "deadExternalFunction()": FunctionModel(
                signature="deadExternalFunction()",
                implementation_contract=contract_b_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/B.sol",
                line_start=10,
                line_end=13,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={
            contract_a_key: contract_a,
            contract_b_key: contract_b,
        },
        project_dir="/test/project",
    )


@pytest.fixture
def special_functions_project():
    """Project with special functions (constructor, receive, fallback, test)."""
    contract_key = ContractKey(contract_name="SpecialContract", path="contracts/Special.sol")

    empty_callees = FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )

    contract = ContractModel(
        name="SpecialContract",
        key=contract_key,
        path="contracts/Special.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_key],
        functions_declared={
            "constructor()": FunctionModel(
                signature="constructor()",
                implementation_contract=contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Special.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
            "receive()": FunctionModel(
                signature="receive()",
                implementation_contract=contract_key,
                solidity_modifiers=["external", "payable"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Special.sol",
                line_start=10,
                line_end=12,
                callees=empty_callees,
            ),
            "fallback()": FunctionModel(
                signature="fallback()",
                implementation_contract=contract_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Special.sol",
                line_start=14,
                line_end=16,
                callees=empty_callees,
            ),
            "testSomething()": FunctionModel(
                signature="testSomething()",
                implementation_contract=contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Special.sol",
                line_start=18,
                line_end=20,
                callees=empty_callees,
            ),
            "setUp()": FunctionModel(
                signature="setUp()",
                implementation_contract=contract_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Special.sol",
                line_start=22,
                line_end=24,
                callees=empty_callees,
            ),
            "regularUnused()": FunctionModel(
                signature="regularUnused()",
                implementation_contract=contract_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Special.sol",
                line_start=26,
                line_end=28,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={contract_key: contract},
        project_dir="/test/project",
    )


def test_find_dead_code_basic(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test basic dead code detection."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True)
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success
    assert response.error_message is None

    # Should find unusedPrivate and unusedInternal
    signatures = [f.function_key.signature for f in response.dead_functions]
    assert "unusedPrivate()" in signatures
    assert "unusedInternal()" in signatures


def test_find_dead_code_exclude_entry_points(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test that entry points (public/external) are excluded by default."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True)
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # Entry points should be excluded
    assert "publicCaller()" not in signatures
    assert "deadExternalFunction()" not in signatures


def test_find_dead_code_include_entry_points(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test including entry points in dead code detection."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=False)
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # Now entry points should be included
    # publicCaller is not called anywhere
    assert "publicCaller()" in signatures
    # deadExternalFunction is not called anywhere
    assert "deadExternalFunction()" in signatures
    # helperFunction IS called by publicCaller, so not dead
    assert "helperFunction()" not in signatures


def test_find_dead_code_special_functions_excluded(
    special_functions_project: ProjectFacts, test_path: str
):
    """Test that special functions are excluded from dead code."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True)
    response = find_dead_code(request, special_functions_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # Special functions should be excluded
    assert "constructor()" not in signatures
    assert "receive()" not in signatures
    assert "fallback()" not in signatures
    assert "testSomething()" not in signatures
    assert "setUp()" not in signatures

    # Regular unused function should be flagged
    assert "regularUnused()" in signatures


def test_find_dead_code_filter_by_contract(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test filtering dead code by contract."""
    contract_a_key = ContractKey(contract_name="ContractA", path="contracts/A.sol")
    request = FindDeadCodeRequest(
        path=test_path, contract_key=contract_a_key, exclude_entry_points=True
    )
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success

    # Should only return functions from ContractA
    for func in response.dead_functions:
        assert func.function_key.contract_name == "ContractA"


def test_find_dead_code_contract_not_found(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test error when contract not found."""
    non_existent_key = ContractKey(contract_name="NonExistent", path="contracts/None.sol")
    request = FindDeadCodeRequest(
        path=test_path, contract_key=non_existent_key, exclude_entry_points=True
    )
    response = find_dead_code(request, dead_code_project_facts)

    assert not response.success
    assert response.error_message is not None
    assert "not found" in response.error_message.lower()


def test_find_dead_code_pagination(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test pagination support."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True, limit=1, offset=0)
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success
    assert len(response.dead_functions) == 1
    assert response.total_count == 2
    assert response.has_more is True


def test_find_dead_code_pagination_offset(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test pagination with offset."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True, limit=1, offset=1)
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success
    assert len(response.dead_functions) == 1
    assert response.total_count == 2
    assert response.has_more is False


def test_find_dead_code_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test dead code detection with empty project."""
    request = FindDeadCodeRequest(path=test_path)
    response = find_dead_code(request, empty_project_facts)

    assert response.success
    assert len(response.dead_functions) == 0
    assert response.total_count == 0


def test_find_dead_code_interfaces_skipped(project_facts: ProjectFacts, test_path: str):
    """Test that interface functions are skipped in dead code analysis."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True)
    response = find_dead_code(request, project_facts)

    assert response.success

    # Interface functions should not be reported as dead code
    for func in response.dead_functions:
        assert func.function_key.contract_name != "InterfaceA"


def test_find_dead_code_libraries_skipped(project_facts: ProjectFacts, test_path: str):
    """Test that library functions are skipped in dead code analysis."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True)
    response = find_dead_code(request, project_facts)

    assert response.success

    # Library functions should not be reported as dead code
    for func in response.dead_functions:
        assert func.function_key.contract_name != "LibraryB"


def test_find_dead_code_reason_field(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test that reason field is populated correctly."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True)
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success

    for func in response.dead_functions:
        assert func.reason is not None
        assert len(func.reason) > 0


def test_find_dead_code_is_entry_point_flag(dead_code_project_facts: ProjectFacts, test_path: str):
    """Test that is_entry_point flag is set correctly."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=False)
    response = find_dead_code(request, dead_code_project_facts)

    assert response.success

    for func in response.dead_functions:
        if func.visibility in ("public", "external"):
            assert func.is_entry_point is True
        else:
            assert func.is_entry_point is False


@pytest.fixture
def slither_internal_project():
    """Project with Slither-generated internal functions."""
    contract_key = ContractKey(contract_name="TestContract", path="contracts/Test.sol")

    empty_callees = FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )

    contract = ContractModel(
        name="TestContract",
        key=contract_key,
        path="contracts/Test.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_key],
        functions_declared={
            "slitherConstructorVariables()": FunctionModel(
                signature="slitherConstructorVariables()",
                implementation_contract=contract_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Test.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
            "slitherConstructorConstantVariables()": FunctionModel(
                signature="slitherConstructorConstantVariables()",
                implementation_contract=contract_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Test.sol",
                line_start=10,
                line_end=13,
                callees=empty_callees,
            ),
            "realDeadCode()": FunctionModel(
                signature="realDeadCode()",
                implementation_contract=contract_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/Test.sol",
                line_start=15,
                line_end=18,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={contract_key: contract},
        project_dir="/test/project",
    )


def test_find_dead_code_slither_internal_functions_excluded(
    slither_internal_project: ProjectFacts, test_path: str
):
    """Test that Slither-generated internal functions are excluded from dead code."""
    request = FindDeadCodeRequest(path=test_path, exclude_entry_points=True)
    response = find_dead_code(request, slither_internal_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # Slither internal functions should be excluded
    assert "slitherConstructorVariables()" not in signatures
    assert "slitherConstructorConstantVariables()" not in signatures

    # Real dead code should still be flagged
    assert "realDeadCode()" in signatures


@pytest.fixture
def exclude_paths_project():
    """Project with contracts in different directories."""
    contract_main_key = ContractKey(contract_name="MainContract", path="src/Main.sol")
    contract_lib_key = ContractKey(contract_name="LibContract", path="lib/forge-std/Lib.sol")
    contract_node_key = ContractKey(contract_name="NodeContract", path="node_modules/dep/Node.sol")

    empty_callees = FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )

    contract_main = ContractModel(
        name="MainContract",
        key=contract_main_key,
        path="src/Main.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_main_key],
        functions_declared={
            "mainFunction()": FunctionModel(
                signature="mainFunction()",
                implementation_contract=contract_main_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="src/Main.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    contract_lib = ContractModel(
        name="LibContract",
        key=contract_lib_key,
        path="lib/forge-std/Lib.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_lib_key],
        functions_declared={
            "libFunction()": FunctionModel(
                signature="libFunction()",
                implementation_contract=contract_lib_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="lib/forge-std/Lib.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    contract_node = ContractModel(
        name="NodeContract",
        key=contract_node_key,
        path="node_modules/dep/Node.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_node_key],
        functions_declared={
            "nodeFunction()": FunctionModel(
                signature="nodeFunction()",
                implementation_contract=contract_node_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="node_modules/dep/Node.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={
            contract_main_key: contract_main,
            contract_lib_key: contract_lib,
            contract_node_key: contract_node,
        },
        project_dir="/test/project",
    )


def test_find_dead_code_exclude_paths(exclude_paths_project: ProjectFacts, test_path: str):
    """Test that exclude_paths filters out contracts in specified directories."""
    request = FindDeadCodeRequest(
        path=test_path,
        exclude_entry_points=True,
        exclude_paths=["lib/", "node_modules/"],
    )
    response = find_dead_code(request, exclude_paths_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]
    paths = [f.function_key.path for f in response.dead_functions]

    # Main contract function should be flagged
    assert "mainFunction()" in signatures

    # Functions in excluded paths should not be flagged
    assert "libFunction()" not in signatures
    assert "nodeFunction()" not in signatures

    # Verify no functions from excluded paths
    for path in paths:
        assert not path.startswith("lib/")
        assert not path.startswith("node_modules/")


def test_find_dead_code_exclude_paths_empty_list(
    exclude_paths_project: ProjectFacts, test_path: str
):
    """Test that empty exclude_paths does not filter anything when exclude_test_frameworks=False."""
    request = FindDeadCodeRequest(
        path=test_path,
        exclude_entry_points=True,
        exclude_paths=[],
        exclude_test_frameworks=False,  # Disable default exclusions
    )
    response = find_dead_code(request, exclude_paths_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # All functions should be flagged when exclude_paths is empty and exclude_test_frameworks=False
    assert "mainFunction()" in signatures
    assert "libFunction()" in signatures
    assert "nodeFunction()" in signatures


def test_find_dead_code_exclude_paths_none(exclude_paths_project: ProjectFacts, test_path: str):
    """Test that None exclude_paths does not filter anything."""
    request = FindDeadCodeRequest(
        path=test_path,
        exclude_entry_points=True,
        exclude_paths=None,
        exclude_test_frameworks=False,  # Disable default exclusions
    )
    response = find_dead_code(request, exclude_paths_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # All functions should be flagged when exclude_paths is None and exclude_test_frameworks=False
    assert "mainFunction()" in signatures
    assert "libFunction()" in signatures
    assert "nodeFunction()" in signatures


def test_find_dead_code_exclude_test_frameworks_default(
    exclude_paths_project: ProjectFacts, test_path: str
):
    """Test that exclude_test_frameworks=True (default) excludes forge-std and node_modules."""
    # Default behavior: exclude_test_frameworks=True
    request = FindDeadCodeRequest(
        path=test_path,
        exclude_entry_points=True,
    )
    response = find_dead_code(request, exclude_paths_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]
    paths = [f.function_key.path for f in response.dead_functions]

    # Main contract function should be flagged
    assert "mainFunction()" in signatures

    # Functions in default excluded paths (forge-std, node_modules) should NOT be flagged
    assert "libFunction()" not in signatures  # lib/forge-std/
    assert "nodeFunction()" not in signatures  # node_modules/

    # Verify no functions from default excluded paths
    for path in paths:
        assert not path.startswith("lib/forge-std/")
        assert not path.startswith("node_modules/")


def test_find_dead_code_exclude_test_frameworks_false(
    exclude_paths_project: ProjectFacts, test_path: str
):
    """Test that exclude_test_frameworks=False disables default exclusions."""
    request = FindDeadCodeRequest(
        path=test_path,
        exclude_entry_points=True,
        exclude_test_frameworks=False,
    )
    response = find_dead_code(request, exclude_paths_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # All functions should be flagged when exclude_test_frameworks=False
    assert "mainFunction()" in signatures
    assert "libFunction()" in signatures
    assert "nodeFunction()" in signatures


def test_find_dead_code_exclude_test_frameworks_with_custom_paths(
    exclude_paths_project: ProjectFacts, test_path: str
):
    """Test that exclude_test_frameworks combines with custom exclude_paths."""
    request = FindDeadCodeRequest(
        path=test_path,
        exclude_entry_points=True,
        exclude_paths=["src/"],  # Custom exclusion
        exclude_test_frameworks=True,  # Default exclusions also apply
    )
    response = find_dead_code(request, exclude_paths_project)

    assert response.success
    signatures = [f.function_key.signature for f in response.dead_functions]

    # Main function is in src/, should be excluded by custom path
    assert "mainFunction()" not in signatures

    # Functions in default excluded paths should also be excluded
    assert "libFunction()" not in signatures
    assert "nodeFunction()" not in signatures
