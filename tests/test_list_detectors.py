"""Tests for list_detectors tool."""

import pytest
from slither_mcp.tools.list_detectors import (
    ListDetectorsRequest,
    list_detectors,
)


class TestListDetectorsHappyPath:
    """Test happy path scenarios for list_detectors."""

    def test_list_all_detectors(self, test_path, project_facts_with_detectors):
        """Test listing all detectors without filters."""
        request = ListDetectorsRequest(path=test_path)
        response = list_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 4
        assert len(response.detectors) == 4

        # Verify all detector names are present
        detector_names = {d.name for d in response.detectors}
        expected_names = {
            "reentrancy-eth",
            "uninitialized-storage",
            "naming-convention",
            "solc-version",
        }
        assert detector_names == expected_names

    def test_list_detectors_with_name_filter(self, test_path, project_facts_with_detectors):
        """Test listing detectors with name filter."""
        request = ListDetectorsRequest(path=test_path, name_filter="reentrancy")
        response = list_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 1
        assert len(response.detectors) == 1
        assert response.detectors[0].name == "reentrancy-eth"

    def test_list_detectors_with_description_filter(self, test_path, project_facts_with_detectors):
        """Test listing detectors filtering by description."""
        request = ListDetectorsRequest(path=test_path, name_filter="naming")
        response = list_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 1
        assert response.detectors[0].name == "naming-convention"

    def test_detector_metadata_fields(self, test_path, project_facts_with_detectors):
        """Test that detector metadata contains all expected fields."""
        request = ListDetectorsRequest(path=test_path, name_filter="reentrancy-eth")
        response = list_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert len(response.detectors) == 1
        
        detector = response.detectors[0]
        assert detector.name == "reentrancy-eth"
        assert detector.description == "Reentrancy vulnerabilities (theft of ethers)"
        assert detector.impact == "High"
        assert detector.confidence == "Medium"


class TestListDetectorsEdgeCases:
    """Test edge cases for list_detectors."""

    def test_list_detectors_with_no_matches(self, test_path, project_facts_with_detectors):
        """Test listing detectors with filter that matches nothing."""
        request = ListDetectorsRequest(path=test_path, name_filter="nonexistent-detector")
        response = list_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.detectors) == 0

    def test_list_detectors_empty_project(self, test_path, empty_project_facts):
        """Test listing detectors with empty project."""
        request = ListDetectorsRequest(path=test_path)
        response = list_detectors(request, empty_project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.detectors) == 0

    def test_list_detectors_case_insensitive_filter(self, test_path, project_facts_with_detectors):
        """Test that name filter is case-insensitive."""
        request = ListDetectorsRequest(path=test_path, name_filter="REENTRANCY")
        response = list_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.total_count == 1
        assert response.detectors[0].name == "reentrancy-eth"

    def test_list_detectors_partial_match(self, test_path, project_facts_with_detectors):
        """Test that filter matches partial strings."""
        request = ListDetectorsRequest(path=test_path, name_filter="storage")
        response = list_detectors(request, project_facts_with_detectors)

        assert response.success is True
        assert response.total_count == 1
        assert response.detectors[0].name == "uninitialized-storage"

