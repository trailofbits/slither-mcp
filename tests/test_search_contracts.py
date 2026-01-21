"""Tests for the search_contracts tool."""

import pytest

from slither_mcp.tools.search_contracts import (
    SearchContractsRequest,
    search_contracts,
)
from slither_mcp.types import ProjectFacts


class TestSearchContracts:
    """Tests for search_contracts function."""

    def test_search_by_exact_name(self, project_facts: ProjectFacts, test_path: str):
        """Test searching for a contract by exact name."""
        request = SearchContractsRequest(path=test_path, pattern="BaseContract")
        response = search_contracts(request, project_facts)

        assert response.success
        assert response.total_count == 1
        assert len(response.matches) == 1
        assert response.matches[0].contract_name == "BaseContract"

    def test_search_by_partial_name(self, project_facts: ProjectFacts, test_path: str):
        """Test searching for contracts by partial name."""
        request = SearchContractsRequest(path=test_path, pattern="Contract")
        response = search_contracts(request, project_facts)

        assert response.success
        # Should match: BaseContract, ChildContract, GrandchildContract,
        # MultiInheritContract, StandaloneContract, EmptyContract
        assert response.total_count >= 6
        for match in response.matches:
            assert "Contract" in match.contract_name

    def test_search_case_insensitive(self, project_facts: ProjectFacts, test_path: str):
        """Test case-insensitive search (default)."""
        request = SearchContractsRequest(path=test_path, pattern="basecontract")
        response = search_contracts(request, project_facts)

        assert response.success
        assert response.total_count == 1
        assert response.matches[0].contract_name == "BaseContract"

    def test_search_case_sensitive(self, project_facts: ProjectFacts, test_path: str):
        """Test case-sensitive search."""
        request = SearchContractsRequest(
            path=test_path, pattern="basecontract", case_sensitive=True
        )
        response = search_contracts(request, project_facts)

        assert response.success
        assert response.total_count == 0

    def test_search_with_regex_pattern(self, project_facts: ProjectFacts, test_path: str):
        """Test searching with regex pattern."""
        # Match contracts starting with 'Child' or 'Grand'
        request = SearchContractsRequest(path=test_path, pattern="^(Child|Grand)")
        response = search_contracts(request, project_facts)

        assert response.success
        assert response.total_count == 2
        names = {m.contract_name for m in response.matches}
        assert names == {"ChildContract", "GrandchildContract"}

    def test_search_with_limit(self, project_facts: ProjectFacts, test_path: str):
        """Test search with limit parameter."""
        request = SearchContractsRequest(path=test_path, pattern="Contract", limit=2)
        response = search_contracts(request, project_facts)

        assert response.success
        assert len(response.matches) == 2
        assert response.total_count >= 6  # Total matches without limit

    def test_search_no_matches(self, project_facts: ProjectFacts, test_path: str):
        """Test search that returns no matches."""
        request = SearchContractsRequest(path=test_path, pattern="NonExistent")
        response = search_contracts(request, project_facts)

        assert response.success
        assert response.total_count == 0
        assert len(response.matches) == 0

    def test_search_empty_project(self, empty_project_facts: ProjectFacts, test_path: str):
        """Test search on empty project."""
        request = SearchContractsRequest(path=test_path, pattern=".*")
        response = search_contracts(request, empty_project_facts)

        assert response.success
        assert response.total_count == 0
        assert len(response.matches) == 0

    def test_search_invalid_regex(self, test_path: str):
        """Test search with invalid regex pattern raises validation error."""
        # Invalid regex is caught at request validation time, not during search
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SearchContractsRequest(path=test_path, pattern="[invalid")

    def test_search_interface_pattern(self, project_facts: ProjectFacts, test_path: str):
        """Test searching for interfaces by pattern."""
        request = SearchContractsRequest(path=test_path, pattern="Interface")
        response = search_contracts(request, project_facts)

        assert response.success
        assert response.total_count >= 1
        assert any(m.contract_name == "InterfaceA" for m in response.matches)

    def test_search_library_pattern(self, project_facts: ProjectFacts, test_path: str):
        """Test searching for libraries by pattern."""
        request = SearchContractsRequest(path=test_path, pattern="Library")
        response = search_contracts(request, project_facts)

        assert response.success
        assert response.total_count >= 1
        assert any(m.contract_name == "LibraryB" for m in response.matches)


class TestSearchContractsValidation:
    """Tests for request validation."""

    def test_invalid_limit_zero(self, test_path: str):
        """Test that limit=0 raises validation error."""
        with pytest.raises(ValueError, match="limit must be >= 1"):
            SearchContractsRequest(path=test_path, pattern="test", limit=0)

    def test_invalid_limit_negative(self, test_path: str):
        """Test that negative limit raises validation error."""
        with pytest.raises(ValueError, match="limit must be >= 1"):
            SearchContractsRequest(path=test_path, pattern="test", limit=-1)

    def test_invalid_regex_in_request(self, test_path: str):
        """Test that invalid regex raises validation error."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SearchContractsRequest(path=test_path, pattern="[unclosed")
