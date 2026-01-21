"""Tests for export_call_graph tool."""

import pytest

from slither_mcp.tools.export_call_graph import (
    ExportCallGraphRequest,
    export_call_graph,
)
from slither_mcp.types import (
    ContractKey,
    ContractModel,
    FunctionCallees,
    FunctionModel,
    ProjectFacts,
)


@pytest.fixture
def call_graph_project_facts():
    """Project with call relationships for testing call graph export."""
    contract_a_key = ContractKey(contract_name="ContractA", path="contracts/A.sol")
    contract_b_key = ContractKey(contract_name="ContractB", path="contracts/B.sol")
    library_key = ContractKey(contract_name="MathLib", path="contracts/MathLib.sol")

    empty_callees = FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )

    # ContractA.main() calls ContractA.helper() internally and ContractB.process() externally
    main_callees = FunctionCallees(
        internal_callees=["ContractA.helper()"],
        external_callees=["ContractB.process()"],
        library_callees=["MathLib.add(uint256,uint256)"],
        has_low_level_calls=False,
    )

    contract_a = ContractModel(
        name="ContractA",
        key=contract_a_key,
        path="contracts/A.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_a_key],
        functions_declared={
            "main()": FunctionModel(
                signature="main()",
                implementation_contract=contract_a_key,
                solidity_modifiers=["public"],
                visibility="public",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/A.sol",
                line_start=5,
                line_end=15,
                callees=main_callees,
            ),
            "helper()": FunctionModel(
                signature="helper()",
                implementation_contract=contract_a_key,
                solidity_modifiers=["internal"],
                visibility="internal",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/A.sol",
                line_start=17,
                line_end=20,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    contract_b = ContractModel(
        name="ContractB",
        key=contract_b_key,
        path="contracts/B.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[contract_b_key],
        functions_declared={
            "process()": FunctionModel(
                signature="process()",
                implementation_contract=contract_b_key,
                solidity_modifiers=["external"],
                visibility="external",
                function_modifiers=[],
                arguments=[],
                returns=[],
                path="contracts/B.sol",
                line_start=5,
                line_end=10,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    library = ContractModel(
        name="MathLib",
        key=library_key,
        path="contracts/MathLib.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=True,
        directly_inherits=[],
        scopes=[library_key],
        functions_declared={
            "add(uint256,uint256)": FunctionModel(
                signature="add(uint256,uint256)",
                implementation_contract=library_key,
                solidity_modifiers=["internal", "pure"],
                visibility="internal",
                function_modifiers=[],
                arguments=["uint256", "uint256"],
                returns=["uint256"],
                path="contracts/MathLib.sol",
                line_start=5,
                line_end=8,
                callees=empty_callees,
            ),
        },
        functions_inherited={},
    )

    return ProjectFacts(
        contracts={
            contract_a_key: contract_a,
            contract_b_key: contract_b,
            library_key: library,
        },
        project_dir="/test/project",
    )


def test_export_call_graph_mermaid_format(call_graph_project_facts: ProjectFacts, test_path: str):
    """Test export in Mermaid format."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid")
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.format == "mermaid"
    assert response.graph is not None
    assert response.error_message is None

    # Check Mermaid syntax
    assert "graph TD" in response.graph
    # Check nodes are present
    assert "main" in response.graph
    assert "helper" in response.graph


def test_export_call_graph_dot_format(call_graph_project_facts: ProjectFacts, test_path: str):
    """Test export in DOT format."""
    request = ExportCallGraphRequest(path=test_path, format="dot")
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.format == "dot"
    assert response.graph is not None

    # Check DOT syntax
    assert "digraph CallGraph" in response.graph
    assert "rankdir=TB" in response.graph


def test_export_call_graph_node_and_edge_counts(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test node and edge count in response."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid")
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.node_count > 0
    assert response.edge_count > 0


def test_export_call_graph_filter_by_contract(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test filtering graph to a single contract."""
    contract_a_key = ContractKey(contract_name="ContractA", path="contracts/A.sol")
    request = ExportCallGraphRequest(path=test_path, format="mermaid", contract_key=contract_a_key)
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    # Should only include functions from ContractA as source nodes
    # But callees might be from other contracts


def test_export_call_graph_entry_points_only(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test filtering to entry points only."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid", entry_points_only=True)
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    # Internal functions should not be source nodes when entry_points_only is True


def test_export_call_graph_exclude_external_calls(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test excluding external call edges."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid", include_external=False)
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.graph is not None
    # Dashed arrows (external calls) should not be in graph
    assert "-.->" not in response.graph


def test_export_call_graph_exclude_library_calls(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test excluding library call edges."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid", include_library=False)
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.graph is not None
    # Bold arrows (library calls) should not be in graph
    assert "==>" not in response.graph


def test_export_call_graph_include_both_external_and_library(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test including both external and library calls."""
    request = ExportCallGraphRequest(
        path=test_path,
        format="mermaid",
        include_external=True,
        include_library=True,
    )
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.graph is not None
    # Should have different edge types
    # Internal: -->
    # External: -.->
    # Library: ==>
    assert "-->" in response.graph  # internal calls
    assert "-.->" in response.graph  # external calls
    assert "==>" in response.graph  # library calls


def test_export_call_graph_max_nodes_truncation(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test graph truncation with max_nodes."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid", max_nodes=2)
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.node_count <= 2
    assert response.truncated is True


def test_export_call_graph_no_truncation_when_under_limit(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test no truncation when node count is under limit."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid", max_nodes=100)
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.truncated is False


def test_export_call_graph_contract_not_found(
    call_graph_project_facts: ProjectFacts, test_path: str
):
    """Test error when contract not found."""
    non_existent_key = ContractKey(contract_name="NonExistent", path="contracts/None.sol")
    request = ExportCallGraphRequest(
        path=test_path, format="mermaid", contract_key=non_existent_key
    )
    response = export_call_graph(request, call_graph_project_facts)

    assert not response.success
    assert response.error_message is not None
    assert "not found" in response.error_message.lower()


def test_export_call_graph_empty_project(empty_project_facts: ProjectFacts, test_path: str):
    """Test call graph export with empty project."""
    request = ExportCallGraphRequest(path=test_path, format="mermaid")
    response = export_call_graph(request, empty_project_facts)

    assert response.success
    assert response.node_count == 0
    assert response.edge_count == 0


def test_export_call_graph_dot_edge_styles(call_graph_project_facts: ProjectFacts, test_path: str):
    """Test DOT format edge styles."""
    request = ExportCallGraphRequest(
        path=test_path,
        format="dot",
        include_external=True,
        include_library=True,
    )
    response = export_call_graph(request, call_graph_project_facts)

    assert response.success
    assert response.graph is not None
    # DOT styles
    assert "[style=dashed]" in response.graph  # external calls
    assert "[style=bold]" in response.graph  # library calls
