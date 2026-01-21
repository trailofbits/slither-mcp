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


class TestSearchFunctionsExcludePaths:
    """Tests for exclude_paths parameter."""

    def test_exclude_lib_path(self, project_facts_with_lib_and_test: ProjectFacts, test_path: str):
        """Test excluding functions from lib/ directory."""
        request = SearchFunctionsRequest(
            path=test_path, pattern=".*", exclude_paths=["lib/"]
        )
        response = search_functions(request, project_facts_with_lib_and_test)

        assert response.success
        # helperFunction from LibDependency should be excluded
        lib_functions = [
            m for m in response.matches if m.contract_name == "LibDependency"
        ]
        assert len(lib_functions) == 0

    def test_exclude_test_path(self, project_facts_with_lib_and_test: ProjectFacts, test_path: str):
        """Test excluding functions from test/ directory."""
        request = SearchFunctionsRequest(
            path=test_path, pattern=".*", exclude_paths=["test/"]
        )
        response = search_functions(request, project_facts_with_lib_and_test)

        assert response.success
        # setUp from TestHelper should be excluded
        test_functions = [
            m for m in response.matches if m.contract_name == "TestHelper"
        ]
        assert len(test_functions) == 0

    def test_exclude_multiple_paths(
        self, project_facts_with_lib_and_test: ProjectFacts, test_path: str
    ):
        """Test excluding functions from multiple directories."""
        request = SearchFunctionsRequest(
            path=test_path, pattern=".*", exclude_paths=["lib/", "test/"]
        )
        response = search_functions(request, project_facts_with_lib_and_test)

        assert response.success
        # Both should be excluded
        excluded_contracts = {"LibDependency", "TestHelper"}
        for match in response.matches:
            assert match.contract_name not in excluded_contracts


class TestSearchFunctionsDeduplication:
    """Tests for deduplicate parameter."""

    def test_deduplication_enabled_by_default(self, project_facts: ProjectFacts, test_path: str):
        """Test that deduplication is enabled by default."""
        request = SearchFunctionsRequest(path=test_path, pattern="initialize")
        response = search_functions(request, project_facts)

        assert response.success
        # With deduplication, we should not see the same (contract_name, signature) twice
        seen = set()
        for match in response.matches:
            key = (match.contract_name, match.signature)
            assert key not in seen, f"Duplicate found: {key}"
            seen.add(key)

    def test_deduplication_disabled(self, project_facts: ProjectFacts, test_path: str):
        """Test that deduplication can be disabled."""
        request = SearchFunctionsRequest(
            path=test_path, pattern="initialize", deduplicate=False
        )
        response = search_functions(request, project_facts)

        assert response.success
        # With deduplication disabled, we might see more results
        # (this depends on whether there are actually duplicates in the test data)

    def test_deduplication_handles_inherited_functions(
        self, project_facts: ProjectFacts, test_path: str
    ):
        """Test that deduplication properly handles inherited functions."""
        # baseFunction is declared in BaseContract and inherited by multiple contracts
        request = SearchFunctionsRequest(path=test_path, pattern="baseFunction")
        response = search_functions(request, project_facts)

        assert response.success
        # Each contract should appear at most once for this function
        contract_names = [m.contract_name for m in response.matches]
        # Check no duplicate contract names (for same signature)
        signatures_by_contract = {}
        for match in response.matches:
            if match.contract_name not in signatures_by_contract:
                signatures_by_contract[match.contract_name] = set()
            assert match.signature not in signatures_by_contract[match.contract_name]
            signatures_by_contract[match.contract_name].add(match.signature)
