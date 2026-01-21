"""Tests for get_project_overview tool."""

from slither_mcp.tools.get_project_overview import (
    GetProjectOverviewRequest,
    get_project_overview,
)
from slither_mcp.types import ProjectFacts


def test_get_project_overview_basic(project_facts: ProjectFacts, test_path: str):
    """Test basic project overview generation."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts)

    assert response.success
    assert response.overview is not None
    assert response.error_message is None

    overview = response.overview
    # Should count all contract types
    assert overview.contract_counts.total == 8
    assert overview.contract_counts.concrete >= 1
    assert overview.contract_counts.abstract >= 1
    assert overview.contract_counts.interface >= 1
    assert overview.contract_counts.library >= 1


def test_get_project_overview_function_counts(project_facts: ProjectFacts, test_path: str):
    """Test function count aggregation."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts)

    assert response.success
    assert response.overview is not None
    overview = response.overview
    assert overview.function_counts.total_declared > 0
    assert overview.function_counts.total_inherited >= 0


def test_get_project_overview_visibility_distribution(project_facts: ProjectFacts, test_path: str):
    """Test visibility distribution calculation."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts)

    assert response.success
    assert response.overview is not None
    overview = response.overview
    vis_dist = overview.visibility_distribution

    # All visibilities should be non-negative
    assert vis_dist.public >= 0
    assert vis_dist.external >= 0
    assert vis_dist.internal >= 0
    assert vis_dist.private >= 0

    # Total should match declared functions
    total_vis = vis_dist.public + vis_dist.external + vis_dist.internal + vis_dist.private
    assert total_vis == overview.function_counts.total_declared


def test_get_project_overview_complexity_distribution(project_facts: ProjectFacts, test_path: str):
    """Test complexity distribution calculation."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts)

    assert response.success
    assert response.overview is not None
    overview = response.overview
    complexity = overview.complexity_distribution

    # All categories should be non-negative
    assert complexity.small >= 0
    assert complexity.medium >= 0
    assert complexity.large >= 0
    assert complexity.very_large >= 0

    # Total should match declared functions
    total_complexity = (
        complexity.small + complexity.medium + complexity.large + complexity.very_large
    )
    assert total_complexity == overview.function_counts.total_declared


def test_get_project_overview_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test project overview with empty project."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, empty_project_facts)

    assert response.success
    assert response.overview is not None
    overview = response.overview
    assert overview.contract_counts.total == 0
    assert overview.contract_counts.concrete == 0
    assert overview.function_counts.total_declared == 0
    assert overview.function_counts.total_inherited == 0


def test_get_project_overview_with_detectors(
    project_facts_with_detectors: ProjectFacts, test_path: str
):
    """Test project overview with detector results."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts_with_detectors)

    assert response.success
    assert response.overview is not None
    overview = response.overview

    # Should have detector findings
    findings = overview.detector_findings_by_impact
    total_findings = findings.high + findings.medium + findings.low + findings.informational
    assert total_findings > 0

    # Should have top detectors
    assert overview.top_detectors is not None
    assert len(overview.top_detectors) > 0


def test_get_project_overview_contract_type_counts(project_facts: ProjectFacts, test_path: str):
    """Test specific contract type counts."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts)

    assert response.success
    assert response.overview is not None
    overview = response.overview

    # From fixture: 1 abstract (BaseContract), 1 interface (InterfaceA),
    # 1 library (LibraryB), others are concrete
    assert overview.contract_counts.abstract == 1
    assert overview.contract_counts.interface == 1
    assert overview.contract_counts.library == 1
    assert overview.contract_counts.concrete == 5  # Child, Grandchild, Multi, Standalone, Empty


def test_get_project_overview_top_detectors_limit(
    project_facts_with_detectors: ProjectFacts, test_path: str
):
    """Test that top detectors is limited to 5."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts_with_detectors)

    assert response.success
    assert response.overview is not None
    # Should have at most 5 top detectors
    assert len(response.overview.top_detectors) <= 5


def test_get_project_overview_detector_finding_structure(
    project_facts_with_detectors: ProjectFacts, test_path: str
):
    """Test that top detectors have correct structure."""
    request = GetProjectOverviewRequest(path=test_path)
    response = get_project_overview(request, project_facts_with_detectors)

    assert response.success
    assert response.overview is not None
    for detector in response.overview.top_detectors:
        assert detector.name is not None
        assert detector.finding_count > 0
        assert detector.impact is not None
