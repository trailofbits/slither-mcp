"""Tool for extracting storage slot layouts from contracts."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import ContractKey, ProjectFacts, StateVariableModel


# Solidity type sizes in bytes (common types)
TYPE_SIZES: dict[str, int] = {
    "bool": 1,
    "uint8": 1,
    "int8": 1,
    "bytes1": 1,
    "uint16": 2,
    "int16": 2,
    "bytes2": 2,
    "uint24": 3,
    "int24": 3,
    "bytes3": 3,
    "uint32": 4,
    "int32": 4,
    "bytes4": 4,
    "uint40": 5,
    "int40": 5,
    "bytes5": 5,
    "uint48": 6,
    "int48": 6,
    "bytes6": 6,
    "uint56": 7,
    "int56": 7,
    "bytes7": 7,
    "uint64": 8,
    "int64": 8,
    "bytes8": 8,
    "uint72": 9,
    "int72": 9,
    "bytes9": 9,
    "uint80": 10,
    "int80": 10,
    "bytes10": 10,
    "uint88": 11,
    "int88": 11,
    "bytes11": 11,
    "uint96": 12,
    "int96": 12,
    "bytes12": 12,
    "uint104": 13,
    "int104": 13,
    "bytes13": 13,
    "uint112": 14,
    "int112": 14,
    "bytes14": 14,
    "uint120": 15,
    "int120": 15,
    "bytes15": 15,
    "uint128": 16,
    "int128": 16,
    "bytes16": 16,
    "uint136": 17,
    "int136": 17,
    "bytes17": 17,
    "uint144": 18,
    "int144": 18,
    "bytes18": 18,
    "uint152": 19,
    "int152": 19,
    "bytes19": 19,
    "uint160": 20,
    "int160": 20,
    "bytes20": 20,
    "address": 20,
    "uint168": 21,
    "int168": 21,
    "bytes21": 21,
    "uint176": 22,
    "int176": 22,
    "bytes22": 22,
    "uint184": 23,
    "int184": 23,
    "bytes23": 23,
    "uint192": 24,
    "int192": 24,
    "bytes24": 24,
    "uint200": 25,
    "int200": 25,
    "bytes25": 25,
    "uint208": 26,
    "int208": 26,
    "bytes26": 26,
    "uint216": 27,
    "int216": 27,
    "bytes27": 27,
    "uint224": 28,
    "int224": 28,
    "bytes28": 28,
    "uint232": 29,
    "int232": 29,
    "bytes29": 29,
    "uint240": 30,
    "int240": 30,
    "bytes30": 30,
    "uint248": 31,
    "int248": 31,
    "bytes31": 31,
    "uint256": 32,
    "int256": 32,
    "bytes32": 32,
    "uint": 32,  # Alias for uint256
    "int": 32,  # Alias for int256
}

SLOT_SIZE = 32  # Storage slots are 32 bytes


class StorageSlotInfo(BaseModel):
    """Information about a storage slot assignment."""

    variable_name: Annotated[str, Field(description="Name of the state variable")]
    slot: Annotated[int, Field(description="Storage slot number (0-indexed)")]
    offset: Annotated[int, Field(description="Byte offset within the slot (0-31)")]
    size: Annotated[int, Field(description="Size of the variable in bytes")]
    type_str: Annotated[str, Field(description="Solidity type of the variable")]
    is_inherited: Annotated[bool, Field(description="Whether variable is inherited")]
    declaring_contract: Annotated[str, Field(description="Contract that declared this variable")]


class GetStorageLayoutRequest(PaginatedRequest):
    """Request to get storage layout for a contract."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[ContractKey, Field(description="Contract to get storage layout for")]
    include_inherited: Annotated[
        bool, Field(description="Include storage from parent contracts (default: true)")
    ] = True


class GetStorageLayoutResponse(BaseModel):
    """Response containing storage layout information."""

    success: bool
    contract_key: Annotated[ContractKey | None, Field(description="The contract analyzed")] = None
    storage_slots: Annotated[
        list[StorageSlotInfo], Field(description="Storage slot assignments")
    ] = []
    total_count: Annotated[int, Field(description="Total number of storage variables")] = 0
    total_slots_used: Annotated[int, Field(description="Total storage slots used")] = 0
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def _get_type_size(type_str: str) -> int:
    """Get the storage size for a Solidity type.

    Args:
        type_str: The type string (e.g., "uint256", "address", "mapping(address => uint256)")

    Returns:
        Size in bytes. Mappings and dynamic arrays return 32 (take full slot).
        Structs and fixed arrays return 32 as an approximation.
    """
    # Clean up type string
    type_str = type_str.strip()

    # Handle contract types as addresses
    if type_str.startswith("contract "):
        return 20

    # Handle interface types as addresses
    if type_str.startswith("interface "):
        return 20

    # Mappings always take a full slot (actual data stored at hash)
    if type_str.startswith("mapping("):
        return 32

    # Dynamic arrays always take a full slot (length stored, data at hash)
    if type_str.endswith("[]"):
        return 32

    # String and bytes (dynamic) always take a full slot
    if type_str in ("string", "bytes"):
        return 32

    # Fixed-size bytes arrays (bytes1 to bytes32) are handled by TYPE_SIZES

    # Structs - approximation, treat as full slot
    if type_str.startswith("struct "):
        return 32

    # Enums are typically uint8 but can be larger
    if type_str.startswith("enum "):
        return 1  # Most enums fit in 1 byte

    # Function types
    if type_str.startswith("function"):
        return 24  # 20 bytes address + 4 bytes selector

    # Fixed-size arrays - compute based on element type and count
    if "[" in type_str and not type_str.endswith("[]"):
        # e.g., "uint256[10]" or "address[5]"
        # These always start a new slot and may span multiple slots
        return 32  # Approximation

    # Check basic types
    if type_str in TYPE_SIZES:
        return TYPE_SIZES[type_str]

    # Default to full slot for unknown types
    return 32


def _requires_new_slot(type_str: str) -> bool:
    """Check if a type must start at a new slot (cannot be packed)."""
    type_str = type_str.strip()

    # Mappings always need their own slot
    if type_str.startswith("mapping("):
        return True

    # Dynamic arrays need their own slot
    if type_str.endswith("[]"):
        return True

    # Dynamic string/bytes need their own slot
    if type_str in ("string", "bytes"):
        return True

    # Structs typically start at new slot
    if type_str.startswith("struct "):
        return True

    # Fixed-size arrays always start at new slot
    if "[" in type_str:
        return True

    return False


def _collect_inherited_variables(
    contract_key: ContractKey,
    project_facts: ProjectFacts,
) -> list[tuple[StateVariableModel, str]]:
    """Collect state variables from inherited contracts in C3 linearization order.

    Returns list of (variable, declaring_contract_name) tuples.
    """
    contract = project_facts.contracts.get(contract_key)
    if not contract:
        return []

    # Build inheritance chain (parents first, then self)
    # Use directly_inherits to walk up the inheritance tree
    inherited_vars: list[tuple[StateVariableModel, str]] = []

    # Process parent contracts recursively (depth-first, leftmost first)
    def collect_from_parents(ck: ContractKey, visited: set[ContractKey]) -> None:
        if ck in visited:
            return
        visited.add(ck)

        c = project_facts.contracts.get(ck)
        if not c:
            return

        # Process parents first (C3 linearization: parents before children)
        for parent_key in c.directly_inherits:
            collect_from_parents(parent_key, visited)

        # Add this contract's variables (skip constants/immutables)
        for var in c.state_variables:
            if not var.is_constant and not var.is_immutable:
                inherited_vars.append((var, c.name))

    visited: set[ContractKey] = set()
    collect_from_parents(contract_key, visited)

    return inherited_vars


def get_storage_layout(
    request: GetStorageLayoutRequest, project_facts: ProjectFacts
) -> GetStorageLayoutResponse:
    """Get storage slot layout for a contract.

    Computes storage slot assignments for state variables, accounting for
    Solidity's packing rules and inheritance order.

    Args:
        request: The storage layout request
        project_facts: The project facts containing contract data

    Returns:
        GetStorageLayoutResponse with storage slot information
    """
    contract = project_facts.contracts.get(request.contract_key)
    if not contract:
        return GetStorageLayoutResponse(
            success=False,
            contract_key=request.contract_key,
            error_message=(
                f"Contract not found: '{request.contract_key.contract_name}' "
                f"at '{request.contract_key.path}'. "
                f"Use search_contracts or list_contracts to find available contracts."
            ),
        )

    # Interfaces have no storage
    if contract.is_interface:
        return GetStorageLayoutResponse(
            success=True,
            contract_key=request.contract_key,
            storage_slots=[],
            total_count=0,
            total_slots_used=0,
            has_more=False,
        )

    # Collect variables in order (inherited first, then declared)
    variables: list[tuple[StateVariableModel, str, bool]] = []

    if request.include_inherited:
        # Get inherited variables (includes declared variables due to recursive walk)
        for var, declaring_contract in _collect_inherited_variables(
            request.contract_key, project_facts
        ):
            is_inherited = declaring_contract != contract.name
            variables.append((var, declaring_contract, is_inherited))
    else:
        # Only declared variables (skip constants/immutables)
        for var in contract.state_variables:
            if not var.is_constant and not var.is_immutable:
                variables.append((var, contract.name, False))

    # Compute storage layout
    storage_slots: list[StorageSlotInfo] = []
    current_slot = 0
    current_offset = 0  # Bytes used in current slot

    for var, declaring_contract, is_inherited in variables:
        size = _get_type_size(var.type_str)

        # Check if we need to start a new slot
        needs_new_slot = _requires_new_slot(var.type_str)

        # If variable requires new slot OR doesn't fit in remaining space
        if needs_new_slot or (current_offset > 0 and current_offset + size > SLOT_SIZE):
            if current_offset > 0:
                current_slot += 1
                current_offset = 0

        slot_info = StorageSlotInfo(
            variable_name=var.name,
            slot=current_slot,
            offset=current_offset,
            size=size,
            type_str=var.type_str,
            is_inherited=is_inherited,
            declaring_contract=declaring_contract,
        )
        storage_slots.append(slot_info)

        # Update position
        current_offset += size
        if current_offset >= SLOT_SIZE:
            current_slot += 1
            current_offset = 0

    # Calculate total slots used
    total_slots_used = current_slot + (1 if current_offset > 0 else 0)

    # Apply pagination
    paginated_slots, total_count, has_more = apply_pagination(
        storage_slots, request.offset, request.limit
    )

    return GetStorageLayoutResponse(
        success=True,
        contract_key=request.contract_key,
        storage_slots=paginated_slots,
        total_count=total_count,
        total_slots_used=total_slots_used,
        has_more=has_more,
    )
