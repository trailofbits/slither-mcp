"""Tests for analyze_state_variables tool."""

from slither_mcp.tools.analyze_state_variables import (
    AnalyzeStateVariablesRequest,
    analyze_state_variables,
)
from slither_mcp.types import ContractKey, ProjectFacts


def test_analyze_state_variables_all(project_facts: ProjectFacts, test_path: str):
    """Test analyzing all state variables in the project."""
    request = AnalyzeStateVariablesRequest(path=test_path)
    response = analyze_state_variables(request, project_facts)

    assert response.success
    assert response.total_count > 0
    # Check we got variables from multiple contracts
    contracts_with_vars = set(v.contract_key.contract_name for v in response.variables)
    assert len(contracts_with_vars) >= 2


def test_analyze_state_variables_filter_by_contract(
    project_facts: ProjectFacts, test_path: str, child_contract_key: ContractKey
):
    """Test filtering state variables by contract."""
    request = AnalyzeStateVariablesRequest(
        path=test_path,
        contract_key=child_contract_key,
    )
    response = analyze_state_variables(request, project_facts)

    assert response.success
    # Should only have variables from ChildContract
    for var in response.variables:
        assert var.contract_key == child_contract_key


def test_analyze_state_variables_filter_by_visibility(project_facts: ProjectFacts, test_path: str):
    """Test filtering state variables by visibility."""
    request = AnalyzeStateVariablesRequest(
        path=test_path,
        visibility_filter="public",
    )
    response = analyze_state_variables(request, project_facts)

    assert response.success
    # All should be public
    for var in response.variables:
        assert var.variable.visibility == "public"


def test_analyze_state_variables_exclude_constants(project_facts: ProjectFacts, test_path: str):
    """Test excluding constant variables."""
    request = AnalyzeStateVariablesRequest(
        path=test_path,
        include_constants=False,
    )
    response = analyze_state_variables(request, project_facts)

    assert response.success
    # No constants should be present
    for var in response.variables:
        assert not var.variable.is_constant


def test_analyze_state_variables_exclude_immutables(project_facts: ProjectFacts, test_path: str):
    """Test excluding immutable variables."""
    request = AnalyzeStateVariablesRequest(
        path=test_path,
        include_immutables=False,
    )
    response = analyze_state_variables(request, project_facts)

    assert response.success
    # No immutables should be present
    for var in response.variables:
        assert not var.variable.is_immutable


def test_analyze_state_variables_summary(project_facts: ProjectFacts, test_path: str):
    """Test that summary contains visibility counts."""
    request = AnalyzeStateVariablesRequest(path=test_path)
    response = analyze_state_variables(request, project_facts)

    assert response.success
    # Summary should have visibility counts
    assert isinstance(response.summary, dict)


def test_analyze_state_variables_pagination(project_facts: ProjectFacts, test_path: str):
    """Test pagination of state variables."""
    request = AnalyzeStateVariablesRequest(
        path=test_path,
        limit=2,
        offset=0,
    )
    response = analyze_state_variables(request, project_facts)

    assert response.success
    assert len(response.variables) <= 2
    # Check if has_more is set correctly when there are more results
    if response.total_count > 2:
        assert response.has_more


def test_analyze_state_variables_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test analyzing state variables in an empty project."""
    request = AnalyzeStateVariablesRequest(path=test_path)
    response = analyze_state_variables(request, empty_project_facts)

    assert response.success
    assert response.total_count == 0
    assert len(response.variables) == 0
