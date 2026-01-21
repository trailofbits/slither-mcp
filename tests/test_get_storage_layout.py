"""Tests for get_storage_layout tool."""

from slither_mcp.tools.get_storage_layout import (
    GetStorageLayoutRequest,
    get_storage_layout,
)
from slither_mcp.types import ContractKey, ProjectFacts


def test_get_storage_layout_basic(project_facts: ProjectFacts, test_path: str):
    """Test basic storage layout extraction for a contract with state variables."""
    child_key = ContractKey(contract_name="ChildContract", path="contracts/Child.sol")
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=child_key,
        include_inherited=False,
    )
    response = get_storage_layout(request, project_facts)

    assert response.success
    assert response.contract_key == child_key
    # ChildContract has balance (uint256) and deployTime (uint256 immutable)
    # Immutables are excluded from storage layout
    assert response.total_count == 1
    assert len(response.storage_slots) == 1
    # Check the variable
    slot = response.storage_slots[0]
    assert slot.variable_name == "balance"
    assert slot.type_str == "uint256"
    assert slot.slot == 0
    assert slot.offset == 0
    assert slot.size == 32
    assert not slot.is_inherited
    assert slot.declaring_contract == "ChildContract"


def test_get_storage_layout_with_inheritance(project_facts: ProjectFacts, test_path: str):
    """Test storage layout includes inherited variables in correct order."""
    child_key = ContractKey(contract_name="ChildContract", path="contracts/Child.sol")
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=child_key,
        include_inherited=True,
    )
    response = get_storage_layout(request, project_facts)

    assert response.success
    # BaseContract has owner (address), VERSION (constant - excluded)
    # ChildContract has balance (uint256), deployTime (immutable - excluded)
    # Expected: owner (address, 20 bytes), balance (uint256, 32 bytes)
    assert response.total_count == 2

    # First should be inherited owner from BaseContract
    owner_slot = response.storage_slots[0]
    assert owner_slot.variable_name == "owner"
    assert owner_slot.type_str == "address"
    assert owner_slot.slot == 0
    assert owner_slot.offset == 0
    assert owner_slot.size == 20
    assert owner_slot.is_inherited
    assert owner_slot.declaring_contract == "BaseContract"

    # Second should be balance from ChildContract
    balance_slot = response.storage_slots[1]
    assert balance_slot.variable_name == "balance"
    assert balance_slot.type_str == "uint256"
    assert balance_slot.slot == 1  # New slot because uint256 doesn't fit after address
    assert balance_slot.offset == 0
    assert balance_slot.size == 32
    assert not balance_slot.is_inherited
    assert balance_slot.declaring_contract == "ChildContract"


def test_get_storage_layout_interface(
    project_facts: ProjectFacts, test_path: str, interface_a_key: ContractKey
):
    """Test storage layout for an interface returns empty (interfaces have no storage)."""
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=interface_a_key,
    )
    response = get_storage_layout(request, project_facts)

    assert response.success
    assert response.contract_key == interface_a_key
    assert response.total_count == 0
    assert response.total_slots_used == 0
    assert len(response.storage_slots) == 0


def test_get_storage_layout_contract_not_found(
    project_facts: ProjectFacts, test_path: str
):
    """Test error handling for non-existent contract."""
    nonexistent_key = ContractKey(
        contract_name="NonExistent", path="contracts/NonExistent.sol"
    )
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=nonexistent_key,
    )
    response = get_storage_layout(request, project_facts)

    assert not response.success
    assert response.contract_key == nonexistent_key
    assert response.error_message is not None
    assert "Contract not found" in response.error_message


def test_get_storage_layout_pagination(project_facts: ProjectFacts, test_path: str):
    """Test pagination of storage layout results."""
    child_key = ContractKey(contract_name="ChildContract", path="contracts/Child.sol")
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=child_key,
        include_inherited=True,
        limit=1,
        offset=0,
    )
    response = get_storage_layout(request, project_facts)

    assert response.success
    assert len(response.storage_slots) == 1
    assert response.total_count == 2
    assert response.has_more is True

    # Get second page
    request2 = GetStorageLayoutRequest(
        path=test_path,
        contract_key=child_key,
        include_inherited=True,
        limit=1,
        offset=1,
    )
    response2 = get_storage_layout(request2, project_facts)

    assert response2.success
    assert len(response2.storage_slots) == 1
    assert response2.total_count == 2
    assert response2.has_more is False


def test_get_storage_layout_total_slots_used(project_facts: ProjectFacts, test_path: str):
    """Test that total_slots_used is calculated correctly."""
    child_key = ContractKey(contract_name="ChildContract", path="contracts/Child.sol")
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=child_key,
        include_inherited=True,
    )
    response = get_storage_layout(request, project_facts)

    assert response.success
    # owner (address, 20 bytes) in slot 0
    # balance (uint256, 32 bytes) in slot 1
    # Total: 2 slots
    assert response.total_slots_used == 2


def test_get_storage_layout_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test storage layout with empty project facts."""
    child_key = ContractKey(contract_name="ChildContract", path="contracts/Child.sol")
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=child_key,
    )
    response = get_storage_layout(request, empty_project_facts)

    assert not response.success
    assert "Contract not found" in response.error_message


def test_get_storage_layout_base_contract(
    project_facts: ProjectFacts, test_path: str, base_contract_key: ContractKey
):
    """Test storage layout for base contract (no inherited variables)."""
    request = GetStorageLayoutRequest(
        path=test_path,
        contract_key=base_contract_key,
        include_inherited=True,
    )
    response = get_storage_layout(request, project_facts)

    assert response.success
    # BaseContract has owner (address) and VERSION (constant - excluded)
    assert response.total_count == 1
    slot = response.storage_slots[0]
    assert slot.variable_name == "owner"
    assert slot.type_str == "address"
    assert slot.slot == 0
    assert slot.offset == 0
    # Should not be marked as inherited since it's declared in this contract
    assert not slot.is_inherited
    assert slot.declaring_contract == "BaseContract"
