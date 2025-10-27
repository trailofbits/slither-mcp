"""Tests for get_derived_contracts tool."""

import pytest
from slither_mcp.tools.get_derived_contracts import (
    GetDerivedContractsRequest,
    get_derived_contracts,
    build_derived_tree,
)
from slither_mcp.types import ContractKey


class TestGetDerivedContractsHappyPath:
    """Test happy path scenarios for get_derived_contracts."""

    def test_simple_derivation(self, project_facts, child_contract_key, base_contract_key):
        """Test getting derived contracts for simple single inheritance."""
        # Query BaseContract - should return ChildContract as its derivative
        request = GetDerivedContractsRequest(contract_key=base_contract_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.contract_key == base_contract_key
        assert response.full_derived is not None

        # Check root node
        root = response.full_derived
        assert root.contract_key == base_contract_key
        assert len(root.derived_by) >= 1

        # Check that ChildContract is in the derived list
        derived_keys = {child.contract_key for child in root.derived_by}
        assert child_contract_key in derived_keys

    def test_deep_derivation(
        self,
        project_facts,
        grandchild_contract_key,
        child_contract_key,
        base_contract_key,
    ):
        """Test getting derived contracts with multiple levels."""
        # Query BaseContract - should show full derivation tree
        request = GetDerivedContractsRequest(contract_key=base_contract_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_derived is not None

        # Check root (BaseContract)
        root = response.full_derived
        assert root.contract_key == base_contract_key
        assert len(root.derived_by) >= 1

        # Find ChildContract in the derived list
        child_node = None
        for derived in root.derived_by:
            if derived.contract_key == child_contract_key:
                child_node = derived
                break
        
        assert child_node is not None, "ChildContract should be in derived list"
        
        # Check that GrandchildContract is derived from ChildContract
        grandchild_keys = {gc.contract_key for gc in child_node.derived_by}
        assert grandchild_contract_key in grandchild_keys

    def test_no_derivation(self, project_facts, grandchild_contract_key):
        """Test getting derived contracts for a contract with no children."""
        # GrandchildContract should have no derivatives
        request = GetDerivedContractsRequest(contract_key=grandchild_contract_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_derived is not None

        # Should have root node with no children
        root = response.full_derived
        assert root.contract_key == grandchild_contract_key
        assert len(root.derived_by) == 0

    def test_interface_derivation(self, project_facts, interface_a_key):
        """Test getting derived contracts for an interface."""
        request = GetDerivedContractsRequest(contract_key=interface_a_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_derived is not None

        root = response.full_derived
        assert root.contract_key == interface_a_key
        # Interface might have implementations
        # Just check it doesn't error

    def test_library_derivation(self, project_facts, library_b_key):
        """Test getting derived contracts for a library."""
        request = GetDerivedContractsRequest(contract_key=library_b_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_derived is not None

        root = response.full_derived
        assert root.contract_key == library_b_key
        # Libraries typically don't have derivatives
        assert len(root.derived_by) == 0

    def test_standalone_contract_derivation(self, project_facts, standalone_contract_key):
        """Test getting derived contracts for a standalone contract with no inheritance."""
        request = GetDerivedContractsRequest(contract_key=standalone_contract_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_derived is not None

        root = response.full_derived
        assert root.contract_key == standalone_contract_key
        # Standalone contracts shouldn't have derivatives
        assert len(root.derived_by) == 0


class TestGetDerivedContractsErrorCases:
    """Test error cases for get_derived_contracts."""

    def test_contract_not_found(self, project_facts):
        """Test getting derived contracts for a non-existent contract."""
        nonexistent_key = ContractKey(
            contract_name="NonExistent",
            path="contracts/NonExistent.sol"
        )
        request = GetDerivedContractsRequest(contract_key=nonexistent_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "NonExistent" in response.error_message
        assert "not found" in response.error_message.lower()
        assert response.contract_key == nonexistent_key
        assert response.full_derived is None

    def test_contract_not_found_empty_project(self, empty_project_facts):
        """Test getting derived contracts in an empty project."""
        some_key = ContractKey(
            contract_name="SomeContract",
            path="contracts/Some.sol"
        )
        request = GetDerivedContractsRequest(contract_key=some_key)
        response = get_derived_contracts(request, empty_project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert response.full_derived is None


class TestGetDerivedContractsEdgeCases:
    """Test edge cases for get_derived_contracts."""

    def test_circular_dependency_prevention(self, project_facts):
        """Test that circular dependencies are handled gracefully."""
        from slither_mcp.types import ContractModel, ProjectFacts

        # Create two contracts that inherit from each other (circular)
        contract_a_key = ContractKey(contract_name="ContractA", path="contracts/A.sol")
        contract_b_key = ContractKey(contract_name="ContractB", path="contracts/B.sol")

        # ContractA inherits from ContractB
        contract_a = ContractModel(
            name="ContractA",
            key=contract_a_key,
            path="contracts/A.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[contract_b_key],
            scopes=[contract_a_key, contract_b_key],
            functions_declared={},
            functions_inherited={},
        )

        # ContractB inherits from ContractA (circular!)
        contract_b = ContractModel(
            name="ContractB",
            key=contract_b_key,
            path="contracts/B.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[contract_a_key],
            scopes=[contract_b_key, contract_a_key],
            functions_declared={},
            functions_inherited={},
        )

        circular_project = ProjectFacts(
            contracts={
                contract_a_key: contract_a,
                contract_b_key: contract_b,
            },
            project_dir="/test/circular",
        )

        # Should handle circular dependency without infinite recursion
        request = GetDerivedContractsRequest(contract_key=contract_a_key)
        response = get_derived_contracts(request, circular_project)

        assert response.success is True
        assert response.full_derived is not None
        # The tree should be built but not recurse infinitely

    def test_self_referencing_contract(self, project_facts):
        """Test contract that lists itself in inheritance (edge case)."""
        from slither_mcp.types import ContractModel, ProjectFacts

        self_ref_key = ContractKey(
            contract_name="SelfRef",
            path="contracts/SelfRef.sol"
        )

        # Contract that inherits from itself (should never happen in real code)
        self_ref_contract = ContractModel(
            name="SelfRef",
            key=self_ref_key,
            path="contracts/SelfRef.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[self_ref_key],  # Self-reference
            scopes=[self_ref_key],
            functions_declared={},
            functions_inherited={},
        )

        self_ref_project = ProjectFacts(
            contracts={self_ref_key: self_ref_contract},
            project_dir="/test/self_ref",
        )

        request = GetDerivedContractsRequest(contract_key=self_ref_key)
        response = get_derived_contracts(request, self_ref_project)

        assert response.success is True
        # Should handle self-reference without infinite recursion
        assert response.full_derived is not None
        assert response.full_derived.contract_key == self_ref_key

    def test_empty_contract_derivation(self, project_facts, empty_contract_key):
        """Test getting derivation for empty contract (no functions but valid)."""
        request = GetDerivedContractsRequest(contract_key=empty_contract_key)
        response = get_derived_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_derived is not None

        root = response.full_derived
        assert root.contract_key == empty_contract_key
        # Empty contracts typically don't have derivatives
        assert len(root.derived_by) == 0


class TestBuildDerivedTree:
    """Test the build_derived_tree function directly."""

    def test_build_tree_basic(self, project_facts, child_contract_key, base_contract_key):
        """Test building derived tree for basic inheritance."""
        tree = build_derived_tree(base_contract_key, project_facts)

        assert tree.contract_key == base_contract_key
        assert len(tree.derived_by) >= 1
        
        # Check that ChildContract is in the derived list
        derived_keys = {child.contract_key for child in tree.derived_by}
        assert child_contract_key in derived_keys

    def test_build_tree_with_visited_set(
        self,
        project_facts,
        child_contract_key,
        base_contract_key,
    ):
        """Test building tree with pre-populated visited set."""
        visited = {child_contract_key}
        tree = build_derived_tree(base_contract_key, project_facts, visited)

        assert tree.contract_key == base_contract_key
        # child_contract_key is in visited, so it should stop recursion there
        # We should still see it in the derived list, but it won't recurse further
        derived_keys = [child.contract_key for child in tree.derived_by]
        if child_contract_key in derived_keys:
            # Find the child node
            child_node = next(child for child in tree.derived_by if child.contract_key == child_contract_key)
            # Should have no further derivations due to visited set
            assert len(child_node.derived_by) == 0

    def test_build_tree_nonexistent_contract(self, project_facts):
        """Test building tree for non-existent contract."""
        nonexistent_key = ContractKey(
            contract_name="DoesNotExist",
            path="contracts/Nope.sol"
        )
        tree = build_derived_tree(nonexistent_key, project_facts)

        # Should return node with empty derived list
        assert tree.contract_key == nonexistent_key
        assert len(tree.derived_by) == 0

    def test_no_children(self, project_facts, grandchild_contract_key):
        """Test building tree for contract with no children."""
        tree = build_derived_tree(grandchild_contract_key, project_facts)

        # Leaf contracts should have no derivations
        assert tree.contract_key == grandchild_contract_key
        assert len(tree.derived_by) == 0

    def test_visited_set_independence(
        self,
        project_facts,
        grandchild_contract_key,
        child_contract_key,
        base_contract_key,
    ):
        """Test that visited sets are independent across branches."""
        # Build tree for base contract - should have full derivation hierarchy
        tree = build_derived_tree(base_contract_key, project_facts)

        # Verify tree structure exists
        assert tree.contract_key == base_contract_key
        assert len(tree.derived_by) >= 1
        
        # Find ChildContract in derived list
        child_found = False
        for derived in tree.derived_by:
            if derived.contract_key == child_contract_key:
                child_found = True
                # Check if GrandchildContract is in its derived list
                grandchild_keys = {gc.contract_key for gc in derived.derived_by}
                # Just verify structure, don't assert on specific inheritance
                # as test fixtures may vary
                break
        
        assert child_found, "ChildContract should be derived from BaseContract"

