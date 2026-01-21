"""Tests for the search_functions tool."""

import pytest

from slither_mcp.tools.search_functions import (
    SearchFunctionsRequest,
    search_functions,
)
from slither_mcp.types import ProjectFacts


class TestSearchFunctions:
    """Tests for search_functions function."""

    def test_search_by_exact_name(self, project_facts: ProjectFacts, test_path: str):
        """Test searching for a function by exact name."""
        request = SearchFunctionsRequest(path=test_path, pattern="initialize")
        response = search_functions(request, project_facts)

        assert response.success
        assert response.total_count >= 1
        # Should find initialize() in multiple contracts (declared and inherited)
        assert any(m.signature == "initialize()" for m in response.matches)

    def test_search_by_partial_name(self, project_facts: ProjectFacts, test_path: str):
        """Test searching for functions by partial name."""
        request = SearchFunctionsRequest(path=test_path, pattern="Function")
        response = search_functions(request, project_facts)

        assert response.success
        # Should match: baseFunction, childFunction, grandchildFunction,
        # standaloneFunction, multiFunction
        assert response.total_count >= 5
        for match in response.matches:
            assert "Function" in match.signature or "function" in match.signature.lower()

    def test_search_case_insensitive(self, project_facts: ProjectFacts, test_path: str):
        """Test case-insensitive search (default)."""
        request = SearchFunctionsRequest(path=test_path, pattern="INITIALIZE")
        response = search_functions(request, project_facts)

        assert response.success
        assert response.total_count >= 1

    def test_search_case_sensitive(self, project_facts: ProjectFacts, test_path: str):
        """Test case-sensitive search."""
        request = SearchFunctionsRequest(path=test_path, pattern="INITIALIZE", case_sensitive=True)
        response = search_functions(request, project_facts)

        assert response.success
        assert response.total_count == 0

    def test_search_by_signature(self, project_facts: ProjectFacts, test_path: str):
        """Test searching by full signature."""
        request = SearchFunctionsRequest(
            path=test_path, pattern="add\\(uint256,uint256\\)", search_signatures=True
        )
        response = search_functions(request, project_facts)

        assert response.success
        assert response.total_count >= 1
        assert any(m.signature == "add(uint256,uint256)" for m in response.matches)

    def test_search_signature_with_address(self, project_facts: ProjectFacts, test_path: str):
        """Test searching signatures containing address type."""
        request = SearchFunctionsRequest(path=test_path, pattern="address", search_signatures=True)
        response = search_functions(request, project_facts)

        assert response.success
        # Should find childFunction(address) and standaloneFunction(uint256,address)
        assert response.total_count >= 1

    def test_search_with_regex_pattern(self, project_facts: ProjectFacts, test_path: str):
        """Test searching with regex pattern."""
        # Match functions starting with 'child' or 'grand'
        request = SearchFunctionsRequest(path=test_path, pattern="^(child|grand)")
        response = search_functions(request, project_facts)

        assert response.success
        assert response.total_count >= 2
        names = {m.signature.split("(")[0] for m in response.matches}
        assert "childFunction" in names
        assert "grandchildFunction" in names

    def test_search_with_limit(self, project_facts: ProjectFacts, test_path: str):
        """Test search with limit parameter."""
        request = SearchFunctionsRequest(path=test_path, pattern="Function", limit=2)
        response = search_functions(request, project_facts)

        assert response.success
        assert len(response.matches) == 2
        assert response.total_count >= 5  # Total matches without limit

    def test_search_no_matches(self, project_facts: ProjectFacts, test_path: str):
        """Test search that returns no matches."""
        request = SearchFunctionsRequest(path=test_path, pattern="nonExistentFunction")
        response = search_functions(request, project_facts)

        assert response.success
        assert response.total_count == 0
        assert len(response.matches) == 0

    def test_search_empty_project(self, empty_project_facts: ProjectFacts, test_path: str):
        """Test search on empty project."""
        request = SearchFunctionsRequest(path=test_path, pattern=".*")
        response = search_functions(request, empty_project_facts)

        assert response.success
        assert response.total_count == 0
        assert len(response.matches) == 0

    def test_search_invalid_regex(self, test_path: str):
        """Test search with invalid regex pattern raises validation error."""
        # Invalid regex is caught at request validation time, not during search
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SearchFunctionsRequest(path=test_path, pattern="[invalid")

    def test_search_includes_inherited_functions(self, project_facts: ProjectFacts, test_path: str):
        """Test that search includes inherited functions."""
        # baseFunction is declared in BaseContract but inherited by ChildContract
        request = SearchFunctionsRequest(path=test_path, pattern="baseFunction")
        response = search_functions(request, project_facts)

        assert response.success
        # Should find in BaseContract (declared) and possibly inherited copies
        assert response.total_count >= 1
        contract_names = {m.contract_name for m in response.matches}
        assert "BaseContract" in contract_names

    def test_search_method_modifier_pattern(self, project_facts: ProjectFacts, test_path: str):
        """Test searching for interface methods."""
        request = SearchFunctionsRequest(path=test_path, pattern="interfaceMethod")
        response = search_functions(request, project_facts)

        assert response.success
        assert response.total_count >= 1
        # Should find in InterfaceA and MultiInheritContract
        contract_names = {m.contract_name for m in response.matches}
        assert "InterfaceA" in contract_names or "MultiInheritContract" in contract_names


class TestSearchFunctionsValidation:
    """Tests for request validation."""

    def test_invalid_limit_zero(self, test_path: str):
        """Test that limit=0 raises validation error."""
        with pytest.raises(ValueError, match="limit must be >= 1"):
            SearchFunctionsRequest(path=test_path, pattern="test", limit=0)

    def test_invalid_limit_negative(self, test_path: str):
        """Test that negative limit raises validation error."""
        with pytest.raises(ValueError, match="limit must be >= 1"):
            SearchFunctionsRequest(path=test_path, pattern="test", limit=-1)

    def test_invalid_regex_in_request(self, test_path: str):
        """Test that invalid regex raises validation error."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SearchFunctionsRequest(path=test_path, pattern="[unclosed")
