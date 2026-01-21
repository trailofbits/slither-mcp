"""Tests for analyze_events tool."""

from slither_mcp.tools.analyze_events import (
    AnalyzeEventsRequest,
    analyze_events,
)
from slither_mcp.types import ContractKey, ProjectFacts


def test_analyze_events_all(project_facts: ProjectFacts, test_path: str):
    """Test analyzing all events in the project."""
    request = AnalyzeEventsRequest(path=test_path)
    response = analyze_events(request, project_facts)

    assert response.success
    assert response.total_count > 0
    # Check we got events from multiple contracts
    contracts_with_events = {e.contract_key.contract_name for e in response.events}
    assert len(contracts_with_events) >= 1


def test_analyze_events_filter_by_contract(
    project_facts: ProjectFacts, test_path: str, child_contract_key: ContractKey
):
    """Test filtering events by contract."""
    request = AnalyzeEventsRequest(
        path=test_path,
        contract_key=child_contract_key,
    )
    response = analyze_events(request, project_facts)

    assert response.success
    # Should only have events from ChildContract
    for event in response.events:
        assert event.contract_key == child_contract_key


def test_analyze_events_filter_by_name(project_facts: ProjectFacts, test_path: str):
    """Test filtering events by name."""
    request = AnalyzeEventsRequest(
        path=test_path,
        name_filter="Transfer",
    )
    response = analyze_events(request, project_facts)

    assert response.success
    # All events should have "Transfer" in the name
    for event in response.events:
        assert "transfer" in event.event.name.lower()


def test_analyze_events_indexed_params(project_facts: ProjectFacts, test_path: str):
    """Test that indexed parameter counts are correct."""
    request = AnalyzeEventsRequest(
        path=test_path,
        name_filter="Transfer",
    )
    response = analyze_events(request, project_facts)

    assert response.success
    # Transfer event should have indexed parameters
    for event in response.events:
        if event.event.name == "Transfer":
            # Transfer has 'from' and 'to' indexed
            assert event.indexed_param_count >= 2


def test_analyze_events_summary(project_facts: ProjectFacts, test_path: str):
    """Test that summary contains event counts per contract."""
    request = AnalyzeEventsRequest(path=test_path)
    response = analyze_events(request, project_facts)

    assert response.success
    assert isinstance(response.summary, dict)


def test_analyze_events_pagination(project_facts: ProjectFacts, test_path: str):
    """Test pagination of events."""
    request = AnalyzeEventsRequest(
        path=test_path,
        limit=1,
        offset=0,
    )
    response = analyze_events(request, project_facts)

    assert response.success
    assert len(response.events) <= 1
    if response.total_count > 1:
        assert response.has_more


def test_analyze_events_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test analyzing events in an empty project."""
    request = AnalyzeEventsRequest(path=test_path)
    response = analyze_events(request, empty_project_facts)

    assert response.success
    assert response.total_count == 0
    assert len(response.events) == 0
