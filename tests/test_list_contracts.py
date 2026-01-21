"""Tests for list_contracts tool."""

from slither_mcp.tools.list_contracts import (
    ListContractsRequest,
    list_contracts,
)


class TestListContractsHappyPath:
    """Test happy path scenarios for list_contracts."""

    def test_list_all_contracts(self, test_path, project_facts):
        """Test listing all contracts without filters."""
        request = ListContractsRequest(path=test_path, filter_type="all")
        response = list_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 8
        assert len(response.contracts) == 8

        # Verify all contract names are present
        contract_names = {c.key.contract_name for c in response.contracts}
        expected_names = {
            "BaseContract",
            "InterfaceA",
            "LibraryB",
            "ChildContract",
            "GrandchildContract",
            "MultiInheritContract",
            "StandaloneContract",
            "EmptyContract",
        }
        assert contract_names == expected_names

    def test_list_concrete_contracts(self, test_path, project_facts):
        """Test listing only concrete (non-abstract, non-interface, non-library) contracts."""
        request = ListContractsRequest(path=test_path, filter_type="concrete")
        response = list_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 5

        # Should include concrete contracts only
        contract_names = {c.key.contract_name for c in response.contracts}
        expected_names = {
            "ChildContract",
            "GrandchildContract",
            "MultiInheritContract",
            "StandaloneContract",
            "EmptyContract",
        }
        assert contract_names == expected_names

        # Verify they are all concrete
        for contract in response.contracts:
            assert contract.is_abstract is False
            assert contract.is_interface is False
            assert contract.is_library is False

    def test_list_interface_contracts(self, test_path, project_facts):
        """Test listing only interface contracts."""
        request = ListContractsRequest(path=test_path, filter_type="interface")
        response = list_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 1
        assert len(response.contracts) == 1

        contract = response.contracts[0]
        assert contract.key.contract_name == "InterfaceA"
        assert contract.is_interface is True

    def test_list_library_contracts(self, test_path, project_facts):
        """Test listing only library contracts."""
        request = ListContractsRequest(path=test_path, filter_type="library")
        response = list_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 1
        assert len(response.contracts) == 1

        contract = response.contracts[0]
        assert contract.key.contract_name == "LibraryB"
        assert contract.is_library is True

    def test_list_abstract_contracts(self, test_path, project_facts):
        """Test listing only abstract contracts."""
        request = ListContractsRequest(path=test_path, filter_type="abstract")
        response = list_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 1
        assert len(response.contracts) == 1

        contract = response.contracts[0]
        assert contract.key.contract_name == "BaseContract"
        assert contract.is_abstract is True

    def test_contract_info_completeness(self, test_path, project_facts):
        """Test that ContractInfo contains all required fields."""
        request = ListContractsRequest(path=test_path, filter_type="all")
        response = list_contracts(request, project_facts)

        for contract in response.contracts:
            # Verify all fields are present and have expected types
            assert isinstance(contract.key.contract_name, str)
            assert isinstance(contract.key.path, str)
            assert isinstance(contract.is_abstract, bool)
            assert isinstance(contract.is_interface, bool)
            assert isinstance(contract.is_library, bool)
            assert isinstance(contract.is_fully_implemented, bool)


class TestListContractsEdgeCases:
    """Test edge cases for list_contracts."""

    def test_empty_project(self, test_path, empty_project_facts):
        """Test listing contracts in an empty project."""
        request = ListContractsRequest(path=test_path, filter_type="all")
        response = list_contracts(request, empty_project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.contracts) == 0

    def test_empty_project_with_filter(self, test_path, empty_project_facts):
        """Test listing contracts with filter in an empty project."""
        request = ListContractsRequest(path=test_path, filter_type="concrete")
        response = list_contracts(request, empty_project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.contracts) == 0

    def test_filter_with_no_matches(self, test_path, project_facts):
        """Test that filtering returns empty list when no contracts match."""
        # Create a project with only abstract contracts
        from slither_mcp.types import ProjectFacts

        abstract_only = ProjectFacts(
            contracts={k: v for k, v in project_facts.contracts.items() if v.is_abstract},
            project_dir="/test/abstract_only",
        )

        # Request concrete contracts (should find none)
        request = ListContractsRequest(path=test_path, filter_type="interface")
        response = list_contracts(request, abstract_only)

        assert response.success is True
        assert response.error_message is None
        assert response.total_count == 0
        assert len(response.contracts) == 0

    def test_default_filter_type(self, test_path, project_facts):
        """Test that default filter_type is 'all'."""
        request = ListContractsRequest(path=test_path)
        response = list_contracts(request, project_facts)

        assert response.success is True
        assert response.total_count == 8  # Should list all contracts

    def test_contract_properties_accuracy(self, test_path, project_facts):
        """Test that contract properties accurately reflect their types."""
        request = ListContractsRequest(path=test_path, filter_type="all")
        response = list_contracts(request, project_facts)

        # Find specific contracts and verify their properties
        contracts_by_name = {c.key.contract_name: c for c in response.contracts}

        # BaseContract should be abstract
        base = contracts_by_name["BaseContract"]
        assert base.is_abstract is True
        assert base.is_fully_implemented is False

        # InterfaceA should be an interface
        interface = contracts_by_name["InterfaceA"]
        assert interface.is_interface is True

        # LibraryB should be a library
        library = contracts_by_name["LibraryB"]
        assert library.is_library is True

        # ChildContract should be concrete and fully implemented
        child = contracts_by_name["ChildContract"]
        assert child.is_abstract is False
        assert child.is_interface is False
        assert child.is_library is False
        assert child.is_fully_implemented is True
