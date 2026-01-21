"""Tests for get_inherited_contracts tool."""

from slither_mcp.tools.get_inherited_contracts import (
    GetInheritedContractsRequest,
    build_inheritance_tree,
    get_inherited_contracts,
)
from slither_mcp.types import ContractKey


class TestGetInheritedContractsHappyPath:
    """Test happy path scenarios for get_inherited_contracts."""

    def test_simple_inheritance(
        self, test_path, project_facts, child_contract_key, base_contract_key
    ):
        """Test getting inherited contracts for simple single inheritance."""
        request = GetInheritedContractsRequest(path=test_path, contract_key=child_contract_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.contract_key == child_contract_key
        assert response.full_inheritance is not None

        # Check root node
        root = response.full_inheritance
        assert root.contract_key == child_contract_key
        assert len(root.inherits) == 1

        # Check parent node
        parent = root.inherits[0]
        assert parent.contract_key == base_contract_key
        assert len(parent.inherits) == 0

    def test_deep_inheritance(
        self,
        test_path,
        project_facts,
        grandchild_contract_key,
        child_contract_key,
        base_contract_key,
    ):
        """Test getting inherited contracts with multiple levels."""
        request = GetInheritedContractsRequest(path=test_path, contract_key=grandchild_contract_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_inheritance is not None

        # Check root (GrandchildContract)
        root = response.full_inheritance
        assert root.contract_key == grandchild_contract_key
        assert len(root.inherits) == 1

        # Check middle level (ChildContract)
        middle = root.inherits[0]
        assert middle.contract_key == child_contract_key
        assert len(middle.inherits) == 1

        # Check top level (BaseContract)
        top = middle.inherits[0]
        assert top.contract_key == base_contract_key
        assert len(top.inherits) == 0

    def test_multiple_inheritance(
        self,
        test_path,
        project_facts,
        multi_inherit_contract_key,
        base_contract_key,
        interface_a_key,
    ):
        """Test getting inherited contracts for multiple inheritance."""
        request = GetInheritedContractsRequest(
            path=test_path, contract_key=multi_inherit_contract_key
        )
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_inheritance is not None

        # Check root node
        root = response.full_inheritance
        assert root.contract_key == multi_inherit_contract_key
        assert len(root.inherits) == 2

        # Check that both parents are present
        parent_keys = {parent.contract_key for parent in root.inherits}
        assert base_contract_key in parent_keys
        assert interface_a_key in parent_keys

        # Check that parents have no further inheritance
        for parent in root.inherits:
            assert len(parent.inherits) == 0

    def test_no_inheritance(self, test_path, project_facts, standalone_contract_key):
        """Test getting inherited contracts for a contract with no parents."""
        request = GetInheritedContractsRequest(path=test_path, contract_key=standalone_contract_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_inheritance is not None

        # Should have root node with no parents
        root = response.full_inheritance
        assert root.contract_key == standalone_contract_key
        assert len(root.inherits) == 0

    def test_interface_inheritance(self, test_path, project_facts, interface_a_key):
        """Test getting inherited contracts for an interface."""
        request = GetInheritedContractsRequest(path=test_path, contract_key=interface_a_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_inheritance is not None

        root = response.full_inheritance
        assert root.contract_key == interface_a_key
        assert len(root.inherits) == 0

    def test_library_inheritance(self, test_path, project_facts, library_b_key):
        """Test getting inherited contracts for a library."""
        request = GetInheritedContractsRequest(path=test_path, contract_key=library_b_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_inheritance is not None

        root = response.full_inheritance
        assert root.contract_key == library_b_key
        assert len(root.inherits) == 0

    def test_abstract_contract_inheritance(self, test_path, project_facts, base_contract_key):
        """Test getting inherited contracts for an abstract contract."""
        request = GetInheritedContractsRequest(path=test_path, contract_key=base_contract_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_inheritance is not None

        root = response.full_inheritance
        assert root.contract_key == base_contract_key
        assert len(root.inherits) == 0


class TestGetInheritedContractsErrorCases:
    """Test error cases for get_inherited_contracts."""

    def test_contract_not_found(self, test_path, project_facts):
        """Test getting inherited contracts for a non-existent contract."""
        nonexistent_key = ContractKey(contract_name="NonExistent", path="contracts/NonExistent.sol")
        request = GetInheritedContractsRequest(path=test_path, contract_key=nonexistent_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "NonExistent" in response.error_message
        assert "not found" in response.error_message.lower()
        assert response.contract_key == nonexistent_key
        assert response.full_inheritance is None

    def test_contract_not_found_empty_project(self, test_path, empty_project_facts):
        """Test getting inherited contracts in an empty project."""
        some_key = ContractKey(contract_name="SomeContract", path="contracts/Some.sol")
        request = GetInheritedContractsRequest(path=test_path, contract_key=some_key)
        response = get_inherited_contracts(request, empty_project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert response.full_inheritance is None


class TestGetInheritedContractsEdgeCases:
    """Test edge cases for get_inherited_contracts."""

    def test_circular_dependency_prevention(self, test_path, project_facts):
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
        request = GetInheritedContractsRequest(path=test_path, contract_key=contract_a_key)
        response = get_inherited_contracts(request, circular_project)

        assert response.success is True
        assert response.full_inheritance is not None
        # The tree should be built but not recurse infinitely

    def test_self_referencing_contract(self, test_path, project_facts):
        """Test contract that lists itself in inheritance (edge case)."""
        from slither_mcp.types import ContractModel, ProjectFacts

        self_ref_key = ContractKey(contract_name="SelfRef", path="contracts/SelfRef.sol")

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

        request = GetInheritedContractsRequest(path=test_path, contract_key=self_ref_key)
        response = get_inherited_contracts(request, self_ref_project)

        assert response.success is True
        # Should handle self-reference without infinite recursion
        assert response.full_inheritance is not None
        assert response.full_inheritance.contract_key == self_ref_key

    def test_missing_parent_contract(self, test_path, project_facts):
        """Test contract that inherits from non-existent parent."""
        from slither_mcp.types import ContractModel, ProjectFacts

        orphan_key = ContractKey(contract_name="Orphan", path="contracts/Orphan.sol")
        missing_parent_key = ContractKey(
            contract_name="MissingParent", path="contracts/Missing.sol"
        )

        # Contract with reference to non-existent parent
        orphan_contract = ContractModel(
            name="Orphan",
            key=orphan_key,
            path="contracts/Orphan.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[missing_parent_key],
            scopes=[orphan_key, missing_parent_key],
            functions_declared={},
            functions_inherited={},
        )

        orphan_project = ProjectFacts(
            contracts={orphan_key: orphan_contract},
            project_dir="/test/orphan",
        )

        request = GetInheritedContractsRequest(path=test_path, contract_key=orphan_key)
        response = get_inherited_contracts(request, orphan_project)

        assert response.success is True
        # Should still build the tree, with missing parent as leaf
        assert response.full_inheritance is not None
        assert len(response.full_inheritance.inherits) == 1
        # Missing parent should have empty inherits list
        assert len(response.full_inheritance.inherits[0].inherits) == 0

    def test_empty_contract_with_inheritance(self, test_path, project_facts, empty_contract_key):
        """Test getting inheritance for empty contract (no functions but valid)."""
        request = GetInheritedContractsRequest(path=test_path, contract_key=empty_contract_key)
        response = get_inherited_contracts(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.full_inheritance is not None

        root = response.full_inheritance
        assert root.contract_key == empty_contract_key
        assert len(root.inherits) == 0


class TestBuildInheritanceTree:
    """Test the build_inheritance_tree function directly."""

    def test_build_tree_basic(
        self, test_path, project_facts, child_contract_key, base_contract_key
    ):
        """Test building inheritance tree for basic inheritance."""
        tree = build_inheritance_tree(child_contract_key, project_facts)

        assert tree.contract_key == child_contract_key
        assert len(tree.inherits) == 1
        assert tree.inherits[0].contract_key == base_contract_key

    def test_build_tree_with_visited_set(
        self,
        project_facts,
        grandchild_contract_key,
        child_contract_key,
    ):
        """Test building tree with pre-populated visited set."""
        visited = {child_contract_key}
        tree = build_inheritance_tree(grandchild_contract_key, project_facts, visited)

        assert tree.contract_key == grandchild_contract_key
        # child_contract_key is in visited, so it should stop recursion there
        assert len(tree.inherits) == 1
        assert tree.inherits[0].contract_key == child_contract_key
        assert len(tree.inherits[0].inherits) == 0  # Stopped by visited set

    def test_build_tree_nonexistent_contract(self, test_path, project_facts):
        """Test building tree for non-existent contract."""
        nonexistent_key = ContractKey(contract_name="DoesNotExist", path="contracts/Nope.sol")
        tree = build_inheritance_tree(nonexistent_key, project_facts)

        # Should return node with empty inherits
        assert tree.contract_key == nonexistent_key
        assert len(tree.inherits) == 0

    def test_visited_set_independence(
        self,
        project_facts,
        grandchild_contract_key,
        child_contract_key,
        base_contract_key,
    ):
        """Test that visited sets are independent across branches."""
        # Build tree for grandchild - should have full hierarchy
        tree = build_inheritance_tree(grandchild_contract_key, project_facts)

        # Verify full depth is preserved
        assert tree.contract_key == grandchild_contract_key
        assert len(tree.inherits) == 1
        assert tree.inherits[0].contract_key == child_contract_key
        assert len(tree.inherits[0].inherits) == 1
        assert tree.inherits[0].inherits[0].contract_key == base_contract_key
