"""Tool for exporting the call graph as Mermaid or DOT format."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from slither_mcp.constants import DEFAULT_MAX_NODES
from slither_mcp.types import ContractKey, JSONStringTolerantModel, ProjectFacts


class ExportCallGraphRequest(JSONStringTolerantModel):
    """Request to export the call graph."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    format: Annotated[
        Literal["mermaid", "dot"],
        Field(description="Output format: 'mermaid' for Mermaid.js or 'dot' for GraphViz DOT"),
    ] = "mermaid"
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Optional: limit graph to functions in a specific contract"),
    ] = None
    entry_points_only: Annotated[
        bool,
        Field(description="If true, only show public/external functions as entry nodes"),
    ] = False
    include_external: Annotated[
        bool,
        Field(description="If true, include external call edges"),
    ] = True
    include_library: Annotated[
        bool,
        Field(description="If true, include library call edges"),
    ] = True
    max_nodes: Annotated[
        int,
        Field(description="Maximum number of nodes to include (prevents huge graphs)"),
    ] = DEFAULT_MAX_NODES
    label_format: Annotated[
        Literal["short", "full"],
        Field(
            description="Node label format: 'short' for Contract.func (default), "
            "'full' for Contract.func(args)"
        ),
    ] = "short"


class ExportCallGraphResponse(BaseModel):
    """Response containing the call graph."""

    success: bool
    graph: Annotated[str | None, Field(description="The call graph in the requested format")] = None
    format: str | None = None
    node_count: int = 0
    edge_count: int = 0
    truncated: Annotated[
        bool, Field(description="True if graph was truncated due to max_nodes limit")
    ] = False
    error_message: str | None = None


def _sanitize_node_id(name: str) -> str:
    """Sanitize a name for use as a node ID in graph formats.

    Replaces characters that cause parsing issues in Mermaid and DOT formats
    with underscores, including dots, parentheses, commas, spaces, and hyphens.

    Args:
        name: The original name (e.g., 'Contract.function(uint256)')

    Returns:
        A sanitized identifier safe for use in graph node IDs
        (e.g., 'Contract_function_uint256_')
    """
    return (
        name.replace(".", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace(",", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )


def _format_function_label(
    contract_name: str, signature: str, label_format: Literal["short", "full"] = "short"
) -> str:
    """Format a function label for display in graph visualizations.

    Creates a human-readable label by combining the contract name with
    the function name. The format can be either 'short' (just the name)
    or 'full' (including parameter types).

    Args:
        contract_name: Name of the contract containing the function
        signature: Full function signature (e.g., 'transfer(address,uint256)')
        label_format: 'short' for Contract.func, 'full' for Contract.func(args)

    Returns:
        A display label like 'MyContract.transfer' or 'MyContract.transfer(address,uint256)'
    """
    if label_format == "full":
        return f"{contract_name}.{signature}"
    else:
        func_name = signature.split("(")[0]
        return f"{contract_name}.{func_name}"


def export_call_graph(
    request: ExportCallGraphRequest, project_facts: ProjectFacts
) -> ExportCallGraphResponse:
    """
    Export the call graph as Mermaid or DOT format.

    Creates a directed graph where nodes are functions and edges represent
    function calls. Can be limited to a specific contract and filtered to
    show only entry points.

    Args:
        request: Request with format and filtering options
        project_facts: The project facts containing all contract data

    Returns:
        ExportCallGraphResponse with the graph string
    """
    try:
        # Collect nodes and edges
        nodes: set[str] = set()  # node IDs
        node_labels: dict[str, str] = {}  # node ID -> display label
        edges: list[tuple[str, str, str]] = []  # (from_id, to_id, edge_type)

        # Determine which contracts to process
        if request.contract_key:
            contract_model = project_facts.contracts.get(request.contract_key)
            if not contract_model:
                return ExportCallGraphResponse(
                    success=False,
                    error_message=f"Contract not found: '{request.contract_key.contract_name}' "
                    f"at '{request.contract_key.path}'",
                )
            contracts_to_process = [(request.contract_key, contract_model)]
        else:
            contracts_to_process = list(project_facts.contracts.items())

        # Build graph from functions
        for contract_key, contract_model in contracts_to_process:
            for sig, func in contract_model.functions_declared.items():
                # Check entry_points_only filter
                if request.entry_points_only:
                    if func.visibility.lower() not in ("public", "external"):
                        continue

                # Create node for this function
                node_id = _sanitize_node_id(f"{contract_key.contract_name}_{sig}")
                label = _format_function_label(
                    contract_key.contract_name, sig, request.label_format
                )

                nodes.add(node_id)
                node_labels[node_id] = label

                # Add edges for internal callees
                for callee in func.callees.internal_callees:
                    callee_id = _sanitize_node_id(callee.replace(".", "_"))
                    edges.append((node_id, callee_id, "internal"))
                    # Add callee as node if not already present
                    if callee_id not in node_labels:
                        if request.label_format == "full":
                            callee_label = callee
                        else:
                            callee_label = callee.split("(")[0] if "(" in callee else callee
                        node_labels[callee_id] = callee_label

                # Add edges for external callees if requested
                if request.include_external:
                    for callee in func.callees.external_callees:
                        callee_id = _sanitize_node_id(callee.replace(".", "_"))
                        edges.append((node_id, callee_id, "external"))
                        if callee_id not in node_labels:
                            if request.label_format == "full":
                                callee_label = callee
                            else:
                                callee_label = callee.split("(")[0] if "(" in callee else callee
                            node_labels[callee_id] = callee_label

                # Add edges for library callees if requested
                if request.include_library:
                    for callee in func.callees.library_callees:
                        callee_id = _sanitize_node_id(callee.replace(".", "_"))
                        edges.append((node_id, callee_id, "library"))
                        if callee_id not in node_labels:
                            if request.label_format == "full":
                                callee_label = callee
                            else:
                                callee_label = callee.split("(")[0] if "(" in callee else callee
                            node_labels[callee_id] = callee_label

        # Add all callee nodes
        for node_id in node_labels:
            nodes.add(node_id)

        # Check for truncation
        truncated = len(nodes) > request.max_nodes
        if truncated:
            # Calculate node degrees (in + out edges) to prioritize connected nodes
            node_degrees: dict[str, int] = dict.fromkeys(nodes, 0)
            for from_node, to_node, _ in edges:
                if from_node in node_degrees:
                    node_degrees[from_node] += 1
                if to_node in node_degrees:
                    node_degrees[to_node] += 1

            # Keep top nodes by degree to preserve graph connectivity
            sorted_nodes = sorted(nodes, key=lambda n: node_degrees.get(n, 0), reverse=True)
            kept_nodes = set(sorted_nodes[: request.max_nodes])

            # Filter edges to only include kept nodes
            edges = [(f, t, et) for f, t, et in edges if f in kept_nodes and t in kept_nodes]
            nodes = kept_nodes

        # Generate output in requested format
        if request.format == "mermaid":
            graph = _generate_mermaid(nodes, node_labels, edges)
        else:  # dot
            graph = _generate_dot(nodes, node_labels, edges)

        return ExportCallGraphResponse(
            success=True,
            graph=graph,
            format=request.format,
            node_count=len(nodes),
            edge_count=len(edges),
            truncated=truncated,
        )

    except Exception as e:
        return ExportCallGraphResponse(
            success=False,
            error_message=f"Failed to export call graph: {e}",
        )


def _generate_mermaid(
    nodes: set[str], node_labels: dict[str, str], edges: list[tuple[str, str, str]]
) -> str:
    """Generate Mermaid.js graph format."""
    lines = ["graph TD"]

    # Add nodes with labels
    for node_id in nodes:
        label = node_labels.get(node_id, node_id)
        lines.append(f'    {node_id}["{label}"]')

    # Add edges with styling based on type
    for from_id, to_id, edge_type in edges:
        if from_id in nodes and to_id in nodes:
            if edge_type == "internal":
                lines.append(f"    {from_id} --> {to_id}")
            elif edge_type == "external":
                lines.append(f"    {from_id} -.-> {to_id}")
            else:  # library
                lines.append(f"    {from_id} ==> {to_id}")

    return "\n".join(lines)


def _generate_dot(
    nodes: set[str], node_labels: dict[str, str], edges: list[tuple[str, str, str]]
) -> str:
    """Generate GraphViz DOT format."""
    lines = ["digraph CallGraph {", "    rankdir=TB;", "    node [shape=box];"]

    # Add nodes with labels
    for node_id in nodes:
        label = node_labels.get(node_id, node_id)
        lines.append(f'    {node_id} [label="{label}"];')

    # Add edges with styling based on type
    for from_id, to_id, edge_type in edges:
        if from_id in nodes and to_id in nodes:
            if edge_type == "internal":
                lines.append(f"    {from_id} -> {to_id};")
            elif edge_type == "external":
                lines.append(f"    {from_id} -> {to_id} [style=dashed];")
            else:  # library
                lines.append(f"    {from_id} -> {to_id} [style=bold];")

    lines.append("}")
    return "\n".join(lines)
