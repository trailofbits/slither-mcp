"""Tool for mapping contract dependency relationships."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.types import ContractKey, JSONStringTolerantModel, ProjectFacts


class ContractDependency(BaseModel):
    """A contract that another contract depends on."""

    contract_key: ContractKey
    relationship: Annotated[
        str, Field(description="Type of dependency: 'inherits', 'calls', or 'uses_library'")
    ]


class CircularDependency(BaseModel):
    """A circular dependency detected in the contract graph."""

    cycle: Annotated[list[ContractKey], Field(description="Contracts forming the cycle")]


class ContractDependencies(BaseModel):
    """Dependencies for a single contract."""

    contract_key: ContractKey
    depends_on: Annotated[
        list[ContractDependency],
        Field(description="Contracts this contract depends on"),
    ]
    depended_by: Annotated[
        list[ContractDependency],
        Field(description="Contracts that depend on this contract"),
    ]


class GetContractDependenciesRequest(JSONStringTolerantModel):
    """Request to get contract dependencies."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Optional: get dependencies for a specific contract"),
    ] = None
    include_external_calls: Annotated[
        bool,
        Field(description="If true, include external call dependencies"),
    ] = True
    include_library_usage: Annotated[
        bool,
        Field(description="If true, include library usage dependencies"),
    ] = True
    detect_circular: Annotated[
        bool,
        Field(description="If true, detect and report circular dependencies"),
    ] = True


class GetContractDependenciesResponse(BaseModel):
    """Response containing contract dependencies."""

    success: bool
    dependencies: list[ContractDependencies] | None = None
    circular_dependencies: list[CircularDependency] | None = None
    error_message: str | None = None


def _detect_cycles(graph: dict[ContractKey, set[ContractKey]]) -> list[list[ContractKey]]:
    """
    Detect cycles in a directed graph using DFS.

    Args:
        graph: Adjacency list representation of the dependency graph

    Returns:
        List of cycles (each cycle is a list of ContractKeys)
    """
    cycles: list[list[ContractKey]] = []
    visited: set[ContractKey] = set()
    rec_stack: set[ContractKey] = set()
    path: list[ContractKey] = []

    def dfs(node: ContractKey) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def get_contract_dependencies(
    request: GetContractDependenciesRequest, project_facts: ProjectFacts
) -> GetContractDependenciesResponse:
    """
    Map contract dependency relationships.

    Identifies which contracts depend on which others through:
    - Inheritance relationships
    - External function calls
    - Library usage

    Args:
        request: Request with filtering options
        project_facts: The project facts containing all contract data

    Returns:
        GetContractDependenciesResponse with dependency information
    """
    try:
        # Build dependency maps
        depends_on: dict[ContractKey, list[ContractDependency]] = {}
        depended_by: dict[ContractKey, list[ContractDependency]] = {}

        # Initialize all contracts
        for contract_key in project_facts.contracts:
            depends_on[contract_key] = []
            depended_by[contract_key] = []

        # Build dependency graph for cycle detection
        dependency_graph: dict[ContractKey, set[ContractKey]] = {
            key: set() for key in project_facts.contracts
        }

        # Collect inheritance dependencies
        for contract_key, contract_model in project_facts.contracts.items():
            for parent_key in contract_model.directly_inherits:
                depends_on[contract_key].append(
                    ContractDependency(contract_key=parent_key, relationship="inherits")
                )
                if parent_key in depended_by:
                    depended_by[parent_key].append(
                        ContractDependency(contract_key=contract_key, relationship="inherits")
                    )
                dependency_graph[contract_key].add(parent_key)

        # Collect external call and library dependencies
        if request.include_external_calls or request.include_library_usage:
            for contract_key, contract_model in project_facts.contracts.items():
                external_targets: set[str] = set()
                library_targets: set[str] = set()

                for func in contract_model.functions_declared.values():
                    # External calls
                    if request.include_external_calls:
                        for callee in func.callees.external_callees:
                            target_contract = callee.split(".")[0]
                            external_targets.add(target_contract)

                    # Library calls
                    if request.include_library_usage:
                        for callee in func.callees.library_callees:
                            target_contract = callee.split(".")[0]
                            library_targets.add(target_contract)

                # Resolve contract names to ContractKeys
                for target_name in external_targets:
                    # Find the contract key for this name
                    for other_key in project_facts.contracts:
                        if other_key.contract_name == target_name and other_key != contract_key:
                            # Avoid duplicate dependencies
                            existing = [
                                d for d in depends_on[contract_key] if d.contract_key == other_key
                            ]
                            if not existing:
                                depends_on[contract_key].append(
                                    ContractDependency(contract_key=other_key, relationship="calls")
                                )
                                depended_by[other_key].append(
                                    ContractDependency(
                                        contract_key=contract_key, relationship="calls"
                                    )
                                )
                                dependency_graph[contract_key].add(other_key)
                            break

                for target_name in library_targets:
                    for other_key in project_facts.contracts:
                        if other_key.contract_name == target_name and other_key != contract_key:
                            existing = [
                                d for d in depends_on[contract_key] if d.contract_key == other_key
                            ]
                            if not existing:
                                depends_on[contract_key].append(
                                    ContractDependency(
                                        contract_key=other_key, relationship="uses_library"
                                    )
                                )
                                depended_by[other_key].append(
                                    ContractDependency(
                                        contract_key=contract_key, relationship="uses_library"
                                    )
                                )
                                dependency_graph[contract_key].add(other_key)
                            break

        # Build response
        if request.contract_key:
            # Single contract requested
            if request.contract_key not in project_facts.contracts:
                return GetContractDependenciesResponse(
                    success=False,
                    error_message=f"Contract not found: '{request.contract_key.contract_name}' "
                    f"at '{request.contract_key.path}'",
                )

            dependencies = [
                ContractDependencies(
                    contract_key=request.contract_key,
                    depends_on=depends_on[request.contract_key],
                    depended_by=depended_by[request.contract_key],
                )
            ]
        else:
            # All contracts
            dependencies = [
                ContractDependencies(
                    contract_key=key,
                    depends_on=depends_on[key],
                    depended_by=depended_by[key],
                )
                for key in project_facts.contracts
            ]

        # Detect circular dependencies if requested
        circular_dependencies = None
        if request.detect_circular:
            cycles = _detect_cycles(dependency_graph)
            if cycles:
                circular_dependencies = [CircularDependency(cycle=cycle) for cycle in cycles]

        return GetContractDependenciesResponse(
            success=True,
            dependencies=dependencies,
            circular_dependencies=circular_dependencies,
        )

    except Exception as e:
        return GetContractDependenciesResponse(
            success=False,
            error_message=f"Failed to get contract dependencies: {e}",
        )
