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
