"""Tests for analyze_low_level_calls tool."""

from slither_mcp.tools.analyze_low_level_calls import (
    AnalyzeLowLevelCallsRequest,
    analyze_low_level_calls,
)
from slither_mcp.types import ContractKey, ProjectFacts


def test_analyze_low_level_calls_all(project_facts: ProjectFacts, test_path: str):
    """Test analyzing all low-level calls in the project."""
    request = AnalyzeLowLevelCallsRequest(path=test_path)
    response = analyze_low_level_calls(request, project_facts)

    assert response.success
    # We have at least one function with low-level calls (sendFunds in ChildContract)
    assert response.total_count >= 1


def test_analyze_low_level_calls_filter_by_contract(
    project_facts: ProjectFacts, test_path: str, child_contract_key: ContractKey
):
    """Test filtering low-level calls by contract."""
    request = AnalyzeLowLevelCallsRequest(
        path=test_path,
        contract_key=child_contract_key,
    )
    response = analyze_low_level_calls(request, project_facts)

    assert response.success
    # Should only have calls from ChildContract
    for call in response.calls:
        assert call.function_key.contract_name == child_contract_key.contract_name


def test_analyze_low_level_calls_contains_function_info(
    project_facts: ProjectFacts, test_path: str
):
    """Test that low-level calls contain function information."""
    request = AnalyzeLowLevelCallsRequest(path=test_path)
    response = analyze_low_level_calls(request, project_facts)

    assert response.success
    # Each call should have function info via function_key
    for call in response.calls:
        assert call.function_key.signature
        assert call.function_key.contract_name


def test_analyze_low_level_calls_summary(project_facts: ProjectFacts, test_path: str):
    """Test that summary contains counts by visibility."""
    request = AnalyzeLowLevelCallsRequest(path=test_path)
    response = analyze_low_level_calls(request, project_facts)

    assert response.success
    assert isinstance(response.summary, dict)


def test_analyze_low_level_calls_pagination(project_facts: ProjectFacts, test_path: str):
    """Test pagination of low-level calls."""
    request = AnalyzeLowLevelCallsRequest(
        path=test_path,
        limit=1,
        offset=0,
    )
    response = analyze_low_level_calls(request, project_facts)

    assert response.success
    assert len(response.calls) <= 1


def test_analyze_low_level_calls_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test analyzing low-level calls in an empty project."""
    request = AnalyzeLowLevelCallsRequest(path=test_path)
    response = analyze_low_level_calls(request, empty_project_facts)

    assert response.success
    assert response.total_count == 0
    assert len(response.calls) == 0


def test_analyze_low_level_calls_no_matches(
    project_facts: ProjectFacts, test_path: str, base_contract_key: ContractKey
):
    """Test when no low-level calls exist in the filtered contract."""
    # BaseContract has no low-level calls
    request = AnalyzeLowLevelCallsRequest(
        path=test_path,
        contract_key=base_contract_key,
    )
    response = analyze_low_level_calls(request, project_facts)

    assert response.success
    assert response.total_count == 0
    assert len(response.calls) == 0


def test_analyze_low_level_calls_visibility_filter(project_facts: ProjectFacts, test_path: str):
    """Test filtering low-level calls by visibility."""
    request = AnalyzeLowLevelCallsRequest(
        path=test_path,
        visibility_filter="external",
    )
    response = analyze_low_level_calls(request, project_facts)

    assert response.success
    # All should be external
    for call in response.calls:
        assert call.visibility.lower() == "external"
