"""Tests for run_detectors tool."""

import pytest
from slither_mcp.tools.run_detectors import (
    RunDetectorsRequest,
    run_detectors,
)


class TestRunDetectorsHappyPath:
    """Test happy path scenarios for run_detectors."""

    def test_run_all_detectors(self, test_path, project_facts_with_detectors):
        """Test running all detectors without filters."""
        request = RunDetectorsRequest(path=test_path)
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        # 1 reentrancy + 1 uninitialized + 2 naming = 4 total
        assert response.total_count == 4
        assert len(response.results) == 4

    def test_run_detectors_by_name(self, test_path, project_facts_with_detectors):
        """Test running specific detectors by name."""
        request = RunDetectorsRequest(path=test_path, detector_names=["reentrancy-eth"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 1
        assert len(response.results) == 1
        assert response.results[0].detector_name == "reentrancy-eth"

    def test_run_multiple_detectors_by_name(self, test_path, project_facts_with_detectors):
        """Test running multiple specific detectors."""
        request = RunDetectorsRequest(path=test_path, 
            detector_names=["reentrancy-eth", "uninitialized-storage"]
        )
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 2
        assert len(response.results) == 2
        
        detector_names = {r.detector_name for r in response.results}
        assert detector_names == {"reentrancy-eth", "uninitialized-storage"}

    def test_filter_by_impact_high(self, test_path, project_facts_with_detectors):
        """Test filtering results by high impact."""
        request = RunDetectorsRequest(path=test_path, impact=["High"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        # reentrancy-eth + uninitialized-storage = 2
        assert response.total_count == 2
        
        for result in response.results:
            assert result.impact == "High"

    def test_filter_by_impact_informational(self, test_path, project_facts_with_detectors):
        """Test filtering results by informational impact."""
        request = RunDetectorsRequest(path=test_path, impact=["Informational"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        # 2 naming-convention results
        assert response.total_count == 2
        
        for result in response.results:
            assert result.impact == "Informational"

    def test_filter_by_multiple_impacts(self, test_path, project_facts_with_detectors):
        """Test filtering by multiple impact levels."""
        request = RunDetectorsRequest(path=test_path, impact=["High", "Informational"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        # All 4 results are either High or Informational
        assert response.total_count == 4

    def test_filter_by_confidence_high(self, test_path, project_facts_with_detectors):
        """Test filtering results by high confidence."""
        request = RunDetectorsRequest(path=test_path, confidence=["High"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        # uninitialized-storage + 2 naming-convention = 3
        assert response.total_count == 3
        
        for result in response.results:
            assert result.confidence == "High"

    def test_filter_by_confidence_medium(self, test_path, project_facts_with_detectors):
        """Test filtering results by medium confidence."""
        request = RunDetectorsRequest(path=test_path, confidence=["Medium"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        # Only reentrancy-eth
        assert response.total_count == 1
        assert response.results[0].detector_name == "reentrancy-eth"

    def test_combined_filters(self, test_path, project_facts_with_detectors):
        """Test combining detector name, impact, and confidence filters."""
        request = RunDetectorsRequest(path=test_path, 
            detector_names=["naming-convention"],
            impact=["Informational"],
            confidence=["High"]
        )
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        # Both naming-convention results match all criteria
        assert response.total_count == 2
        
        for result in response.results:
            assert result.detector_name == "naming-convention"
            assert result.impact == "Informational"
            assert result.confidence == "High"

    def test_result_contains_source_locations(self, test_path, project_facts_with_detectors):
        """Test that results include source location information."""
        request = RunDetectorsRequest(path=test_path, detector_names=["reentrancy-eth"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert len(response.results) == 1
        
        result = response.results[0]
        assert len(result.source_locations) == 1
        
        location = result.source_locations[0]
        assert location.file_path == "contracts/Contract.sol"
        assert location.start_line == 5
        assert location.end_line == 10

    def test_result_contains_description(self, test_path, project_facts_with_detectors):
        """Test that results include detailed descriptions."""
        request = RunDetectorsRequest(path=test_path, detector_names=["uninitialized-storage"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert len(response.results) == 1
        
        result = response.results[0]
        assert "Contract.storageVar" in result.description
        assert "never initialized" in result.description


class TestRunDetectorsEdgeCases:
    """Test edge cases for run_detectors."""

    def test_run_detectors_nonexistent_name(self, test_path, project_facts_with_detectors):
        """Test running a detector that doesn't exist."""
        request = RunDetectorsRequest(path=test_path, detector_names=["nonexistent-detector"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.results) == 0

    def test_run_detectors_empty_project(self, test_path, empty_project_facts):
        """Test running detectors on empty project."""
        request = RunDetectorsRequest(path=test_path)
        response = run_detectors(request, empty_project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.results) == 0

    def test_run_detectors_case_insensitive_name(self, test_path, project_facts_with_detectors):
        """Test that detector name filter is case-insensitive."""
        request = RunDetectorsRequest(path=test_path, detector_names=["REENTRANCY-ETH"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.total_count == 1
        assert response.results[0].detector_name == "reentrancy-eth"

    def test_run_detectors_case_insensitive_impact(self, test_path, project_facts_with_detectors):
        """Test that impact filter is case-insensitive."""
        request = RunDetectorsRequest(path=test_path, impact=["high"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.total_count == 2

    def test_run_detectors_case_insensitive_confidence(self, test_path, project_facts_with_detectors):
        """Test that confidence filter is case-insensitive."""
        request = RunDetectorsRequest(path=test_path, confidence=["medium"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.total_count == 1

    def test_filter_excludes_all_results(self, test_path, project_facts_with_detectors):
        """Test filters that exclude all results."""
        request = RunDetectorsRequest(path=test_path, 
            impact=["High"],
            confidence=["Low"]
        )
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.total_count == 0
        # No results match both High impact AND Low confidence

    def test_multiple_results_from_same_detector(self, test_path, project_facts_with_detectors):
        """Test that multiple results from same detector are all returned."""
        request = RunDetectorsRequest(path=test_path, detector_names=["naming-convention"])
        response = run_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.total_count == 2
        assert all(r.detector_name == "naming-convention" for r in response.results)

