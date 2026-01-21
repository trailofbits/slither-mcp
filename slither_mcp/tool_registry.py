"""Tool registry for MCP server registration.

This module provides a table-driven registry for MCP tools, allowing tool
implementations to be registered with minimal boilerplate.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from fastmcp import FastMCP
from pydantic import BaseModel

from slither_mcp.metrics import track_tool_call
from slither_mcp.tools import (
    AnalyzeEventsRequest,
    AnalyzeEventsResponse,
    AnalyzeLowLevelCallsRequest,
    AnalyzeLowLevelCallsResponse,
    AnalyzeModifiersRequest,
    AnalyzeModifiersResponse,
    AnalyzeStateVariablesRequest,
    AnalyzeStateVariablesResponse,
    ExportCallGraphRequest,
    ExportCallGraphResponse,
    FindDeadCodeRequest,
    FindDeadCodeResponse,
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    FunctionCallersRequest,
    FunctionCallersResponse,
    GetContractDependenciesRequest,
    GetContractDependenciesResponse,
    GetContractRequest,
    GetContractResponse,
    GetContractSourceRequest,
    GetContractSourceResponse,
    GetDerivedContractsRequest,
    GetDerivedContractsResponse,
    GetFunctionSourceRequest,
    GetFunctionSourceResponse,
    GetInheritedContractsRequest,
    GetInheritedContractsResponse,
    GetProjectOverviewRequest,
    GetProjectOverviewResponse,
    ListContractsRequest,
    ListContractsResponse,
    ListDetectorsRequest,
    ListDetectorsResponse,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    ListFunctionsRequest,
    ListFunctionsResponse,
    RunDetectorsRequest,
    RunDetectorsResponse,
    SearchContractsRequest,
    SearchContractsResponse,
    SearchFunctionsRequest,
    SearchFunctionsResponse,
)
from slither_mcp.tools.analyze_events import analyze_events as analyze_events_impl
from slither_mcp.tools.analyze_low_level_calls import (
    analyze_low_level_calls as analyze_low_level_calls_impl,
)
from slither_mcp.tools.analyze_modifiers import analyze_modifiers as analyze_modifiers_impl
from slither_mcp.tools.analyze_state_variables import (
    analyze_state_variables as analyze_state_variables_impl,
)
from slither_mcp.tools.export_call_graph import export_call_graph as export_call_graph_impl
from slither_mcp.tools.find_dead_code import find_dead_code as find_dead_code_impl
from slither_mcp.tools.get_contract import get_contract as get_contract_impl
from slither_mcp.tools.get_contract_dependencies import (
    get_contract_dependencies as get_contract_dependencies_impl,
)
from slither_mcp.tools.get_contract_source import get_contract_source as get_contract_source_impl
from slither_mcp.tools.get_derived_contracts import (
    get_derived_contracts as get_derived_contracts_impl,
)
from slither_mcp.tools.get_function_source import get_function_source as get_function_source_impl
from slither_mcp.tools.get_inherited_contracts import (
    get_inherited_contracts as get_inherited_contracts_impl,
)
from slither_mcp.tools.get_project_overview import get_project_overview as get_project_overview_impl
from slither_mcp.tools.list_contracts import list_contracts as list_contracts_impl
from slither_mcp.tools.list_detectors import list_detectors as list_detectors_impl
from slither_mcp.tools.list_function_callees import (
    list_function_callees as list_function_callees_impl,
)
from slither_mcp.tools.list_function_callers import (
    list_function_callers as list_function_callers_impl,
)
from slither_mcp.tools.list_function_implementations import (
    list_function_implementations as list_function_implementations_impl,
)
from slither_mcp.tools.list_functions import list_functions as list_functions_impl
from slither_mcp.tools.run_detectors import run_detectors as run_detectors_impl
from slither_mcp.tools.search_contracts import search_contracts as search_contracts_impl
from slither_mcp.tools.search_functions import search_functions as search_functions_impl
from slither_mcp.types import ProjectFacts

RequestT = TypeVar("RequestT", bound=BaseModel)
ResponseT = TypeVar("ResponseT", bound=BaseModel)


@dataclass(frozen=True)
class ToolConfig:
    """Configuration for registering an MCP tool."""

    name: str
    impl: Callable[[Any, ProjectFacts], Any]
    request_type: type[BaseModel]
    response_type: type[BaseModel]
    description: str
    error_kwargs: dict[str, Any]
    # Fields to copy from request to error response (e.g., ["contract_key"])
    error_request_fields: tuple[str, ...] = ()


# Tool configurations - one entry per tool
TOOL_CONFIGS: tuple[ToolConfig, ...] = (
    ToolConfig(
        name="list_contracts",
        impl=list_contracts_impl,
        request_type=ListContractsRequest,
        response_type=ListContractsResponse,
        description="""List all contracts in the project. START HERE for project discovery.

WORKFLOW: First tool to call when exploring a new Solidity project.

PARAMETERS:
- path: Project directory path (required)
- filter_type: "all" | "concrete" | "interface" | "library" | "abstract"
- limit/offset: Pagination for large projects

EXAMPLE:
    {"path": "/project", "filter_type": "concrete", "limit": 20}

NEXT STEPS: get_contract, list_functions, get_contract_source""",
        error_kwargs={"contracts": [], "total_count": 0},
    ),
    ToolConfig(
        name="get_contract",
        impl=get_contract_impl,
        request_type=GetContractRequest,
        response_type=GetContractResponse,
        description="""Get detailed metadata about a specific contract.

WORKFLOW: Use after list_contracts or search_contracts to get full details.

PARAMETERS:
- path: Project directory path (required)
- contract_key: {"contract_name": "ERC20", "path": "src/ERC20.sol"}
- include_functions: Set false for metadata only (reduces response size)

EXAMPLE:
    {"path": "/project", "contract_key": {"contract_name": "Token", "path": "src/Token.sol"}}

NEXT STEPS: list_functions, get_inherited_contracts, get_derived_contracts""",
        error_kwargs={},
    ),
    ToolConfig(
        name="get_contract_source",
        impl=get_contract_source_impl,
        request_type=GetContractSourceRequest,
        response_type=GetContractSourceResponse,
        description="""Get source code of a contract's file with optional line limits.

WORKFLOW: Use when you need to read the actual Solidity code.

PARAMETERS:
- path: Project directory path (required)
- contract_key: {"contract_name": "ERC20", "path": "src/ERC20.sol"}
- max_lines: Maximum lines to return (default 500, None for unlimited)
- start_line: Starting line number (1-indexed)

EXAMPLE:
    {"path": "/project", "contract_key": {"contract_name": "Token", "path": "src/Token.sol"}, "max_lines": 100}

NEXT STEPS: get_function_source (for specific function code)""",
        error_kwargs={},
    ),
    ToolConfig(
        name="get_function_source",
        impl=get_function_source_impl,
        request_type=GetFunctionSourceRequest,
        response_type=GetFunctionSourceResponse,
        description="""Get source code of a specific function.

WORKFLOW: Use after list_functions to read a specific function's implementation.

PARAMETERS:
- path: Project directory path (required)
- function_key: {"signature": "transfer(address,uint256)", "contract_name": "ERC20", "path": "src/ERC20.sol"}

EXAMPLE:
    {"path": "/project", "function_key": {"signature": "balanceOf(address)", "contract_name": "Token", "path": "src/Token.sol"}}

NEXT STEPS: function_callees (to see what it calls), function_callers (to see who calls it)""",
        error_kwargs={},
    ),
    ToolConfig(
        name="list_functions",
        impl=list_functions_impl,
        request_type=ListFunctionsRequest,
        response_type=ListFunctionsResponse,
        description="""List functions with optional filters by contract, visibility, or modifiers.

WORKFLOW: Use after identifying a contract to explore its functions.

PARAMETERS:
- path: Project directory path (required)
- contract_key: Filter to specific contract (optional)
- visibility_filter: "public" | "external" | "internal" | "private"
- modifier_filter: "view" | "pure" | "payable" | "virtual" | etc.
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "contract_key": {"contract_name": "Token", "path": "src/Token.sol"}, "visibility_filter": "external"}

NEXT STEPS: get_function_source, function_callees, function_callers""",
        error_kwargs={"functions": [], "total_count": 0},
    ),
    ToolConfig(
        name="function_callees",
        impl=list_function_callees_impl,
        request_type=FunctionCalleesRequest,
        response_type=FunctionCalleesResponse,
        description="""Get all functions called by a specific function (call graph outgoing edges).

WORKFLOW: Use for tracing function dependencies and call flow analysis.

PARAMETERS:
- path: Project directory path (required)
- function_key: {"signature": "transfer(address,uint256)", "contract_name": "ERC20", "path": "src/ERC20.sol"}

EXAMPLE:
    {"path": "/project", "function_key": {"signature": "withdraw()", "contract_name": "Vault", "path": "src/Vault.sol"}}

RETURNS: internal_callees, external_callees, library_callees, has_low_level_calls

NEXT STEPS: function_callers (reverse direction), get_function_source""",
        error_kwargs={},
    ),
    ToolConfig(
        name="get_inherited_contracts",
        impl=get_inherited_contracts_impl,
        request_type=GetInheritedContractsRequest,
        response_type=GetInheritedContractsResponse,
        description="""Get parent contracts in the inheritance hierarchy (upward tree).

WORKFLOW: Use to understand what a contract inherits from.

PARAMETERS:
- path: Project directory path (required)
- contract_key: {"contract_name": "ERC20", "path": "src/ERC20.sol"}
- max_depth: Maximum depth to traverse (default 3, None for unlimited)

EXAMPLE:
    {"path": "/project", "contract_key": {"contract_name": "MyToken", "path": "src/MyToken.sol"}, "max_depth": 5}

RETURNS: Recursive tree of parent contracts. Check 'truncated' if max_depth was hit.

NEXT STEPS: get_derived_contracts (reverse direction), get_contract""",
        error_kwargs={},
        error_request_fields=("contract_key",),
    ),
    ToolConfig(
        name="get_derived_contracts",
        impl=get_derived_contracts_impl,
        request_type=GetDerivedContractsRequest,
        response_type=GetDerivedContractsResponse,
        description="""Get child contracts that inherit from this contract (downward tree).

WORKFLOW: Use to find implementations of interfaces or extensions of base contracts.

PARAMETERS:
- path: Project directory path (required)
- contract_key: {"contract_name": "IERC20", "path": "src/IERC20.sol"}
- max_depth: Maximum depth to traverse (default 3, None for unlimited)

EXAMPLE:
    {"path": "/project", "contract_key": {"contract_name": "BaseToken", "path": "src/BaseToken.sol"}}

RETURNS: Recursive tree of child contracts. Check 'truncated' if max_depth was hit.

NEXT STEPS: get_inherited_contracts (reverse direction), list_function_implementations""",
        error_kwargs={},
        error_request_fields=("contract_key",),
    ),
    ToolConfig(
        name="list_function_implementations",
        impl=list_function_implementations_impl,
        request_type=ListFunctionImplementationsRequest,
        response_type=ListFunctionImplementationsResponse,
        description="""Find all contracts that implement a specific function signature.

WORKFLOW: Use to find concrete implementations of interface/abstract functions.

PARAMETERS:
- path: Project directory path (required)
- contract_key: The interface or abstract contract
- function_signature: e.g., "transfer(address,uint256)"
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "contract_key": {"contract_name": "IERC20", "path": "src/IERC20.sol"}, "function_signature": "transfer(address,uint256)"}

RETURNS: List of ImplementationInfo with contract_key, visibility, modifiers.

NEXT STEPS: get_function_source (to see each implementation)""",
        error_kwargs={},
    ),
    ToolConfig(
        name="function_callers",
        impl=list_function_callers_impl,
        request_type=FunctionCallersRequest,
        response_type=FunctionCallersResponse,
        description="""Get all functions that call a specific function (call graph incoming edges).

WORKFLOW: Use for impact analysis and understanding function usage.

PARAMETERS:
- path: Project directory path (required)
- function_key: {"signature": "transfer(address,uint256)", "contract_name": "ERC20", "path": "src/ERC20.sol"}

EXAMPLE:
    {"path": "/project", "function_key": {"signature": "_mint(address,uint256)", "contract_name": "Token", "path": "src/Token.sol"}}

RETURNS: internal_callers, external_callers, library_callers

NEXT STEPS: function_callees (reverse direction), get_function_source""",
        error_kwargs={},
    ),
    ToolConfig(
        name="list_detectors",
        impl=list_detectors_impl,
        request_type=ListDetectorsRequest,
        response_type=ListDetectorsResponse,
        description="""List all available Slither security detectors.

WORKFLOW: Use to discover what security checks are available before running them.

PARAMETERS:
- path: Project directory path (required)
- name_filter: Filter by name or description (case-insensitive)
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "name_filter": "reentrancy"}

RETURNS: List of detectors with name, description, impact, confidence.

NEXT STEPS: run_detectors (to get actual findings)""",
        error_kwargs={"detectors": [], "total_count": 0},
    ),
    ToolConfig(
        name="run_detectors",
        impl=run_detectors_impl,
        request_type=RunDetectorsRequest,
        response_type=RunDetectorsResponse,
        description="""Get security findings from Slither detectors with optional filtering.

WORKFLOW: Use for security auditing. Filter by impact for critical issues first.

PARAMETERS:
- path: Project directory path (required)
- detector_filter: Filter by detector name
- impact_filter: ["High", "Medium"] - filter by severity
- confidence_filter: ["High", "Medium"] - filter by confidence
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "impact_filter": ["High", "Medium"]}

RETURNS: List of findings with description, source_locations (file + line numbers).

NEXT STEPS: get_function_source (to see vulnerable code)""",
        error_kwargs={"results": [], "total_count": 0},
    ),
    ToolConfig(
        name="search_contracts",
        impl=search_contracts_impl,
        request_type=SearchContractsRequest,
        response_type=SearchContractsResponse,
        description="""Search for contracts by name using regex patterns.

WORKFLOW: Use when you know part of a contract name but not the exact path.

PARAMETERS:
- path: Project directory path (required)
- pattern: Regex pattern to match contract names
- case_sensitive: Default false
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "pattern": "ERC20.*"}

NEXT STEPS: get_contract, list_functions, get_contract_source""",
        error_kwargs={"matches": [], "total_count": 0},
    ),
    ToolConfig(
        name="search_functions",
        impl=search_functions_impl,
        request_type=SearchFunctionsRequest,
        response_type=SearchFunctionsResponse,
        description="""Search for functions by name or signature using regex patterns.

WORKFLOW: Use to find functions across all contracts matching a pattern.

PARAMETERS:
- path: Project directory path (required)
- pattern: Regex pattern to match function names or signatures
- search_signature: If true, searches full signature including params
- case_sensitive: Default false
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "pattern": "transfer.*", "search_signature": true}

NEXT STEPS: get_function_source, function_callees, function_callers""",
        error_kwargs={"matches": [], "total_count": 0},
    ),
    ToolConfig(
        name="get_project_overview",
        impl=get_project_overview_impl,
        request_type=GetProjectOverviewRequest,
        response_type=GetProjectOverviewResponse,
        description="""Get aggregate statistics and overview of the Solidity project.

WORKFLOW: Use as a quick summary before diving into details.

PARAMETERS:
- path: Project directory path (required)

EXAMPLE:
    {"path": "/project"}

RETURNS: contract_counts, function_counts, visibility_distribution,
         complexity_distribution, detector_findings_by_impact, top_detectors

NEXT STEPS: list_contracts, run_detectors""",
        error_kwargs={},
    ),
    ToolConfig(
        name="find_dead_code",
        impl=find_dead_code_impl,
        request_type=FindDeadCodeRequest,
        response_type=FindDeadCodeResponse,
        description="""Find functions with no callers (potential dead code).

WORKFLOW: Use for code cleanup and identifying unused functions.

PARAMETERS:
- path: Project directory path (required)
- contract_key: Optional, limit to specific contract
- exclude_entry_points: If true (default), skip public/external functions
- include_inherited: If true, also check inherited functions
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "exclude_entry_points": true}

RETURNS: List of functions with no internal callers.

NEXT STEPS: get_function_source (to review dead code)""",
        error_kwargs={"dead_functions": [], "total_count": 0},
    ),
    ToolConfig(
        name="export_call_graph",
        impl=export_call_graph_impl,
        request_type=ExportCallGraphRequest,
        response_type=ExportCallGraphResponse,
        description="""Export the function call graph as Mermaid or DOT format.

WORKFLOW: Use for visualization and documentation of function relationships.

PARAMETERS:
- path: Project directory path (required)
- format: "mermaid" (default) or "dot" (GraphViz)
- contract_key: Optional, limit to specific contract
- entry_points_only: If true, only show public/external functions
- include_external: Include external call edges (default true)
- include_library: Include library call edges (default true)
- max_nodes: Maximum nodes to prevent huge graphs (default 100)

EXAMPLE:
    {"path": "/project", "format": "mermaid", "entry_points_only": true}

RETURNS: Graph string in requested format.

NEXT STEPS: Use in documentation or visualization tools""",
        error_kwargs={},
    ),
    ToolConfig(
        name="get_contract_dependencies",
        impl=get_contract_dependencies_impl,
        request_type=GetContractDependenciesRequest,
        response_type=GetContractDependenciesResponse,
        description="""Map contract dependency relationships (inheritance, calls, library usage).

WORKFLOW: Use for understanding contract relationships and impact analysis.

PARAMETERS:
- path: Project directory path (required)
- contract_key: Optional, get dependencies for a specific contract
- include_external_calls: Include external call dependencies (default true)
- include_library_usage: Include library usage dependencies (default true)
- detect_circular: Detect circular dependencies (default true)

EXAMPLE:
    {"path": "/project", "contract_key": {"contract_name": "Token", "path": "src/Token.sol"}}

RETURNS: depends_on (what this contract needs), depended_by (what needs this),
         circular_dependencies (if detected)

NEXT STEPS: get_contract, get_inherited_contracts""",
        error_kwargs={},
    ),
    ToolConfig(
        name="analyze_state_variables",
        impl=analyze_state_variables_impl,
        request_type=AnalyzeStateVariablesRequest,
        response_type=AnalyzeStateVariablesResponse,
        description="""Analyze state variables across the project.

WORKFLOW: Use for storage layout analysis, upgrade safety, and code review.

PARAMETERS:
- path: Project directory path (required)
- contract_key: Optional, limit to specific contract
- visibility_filter: Filter by visibility (public, internal, private)
- include_constants: Include constant variables (default true)
- include_immutables: Include immutable variables (default true)
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "visibility_filter": "public"}

RETURNS: List of state variables with type, visibility, and mutability info.
         Summary with counts by visibility.

NEXT STEPS: get_contract, get_contract_source""",
        error_kwargs={"variables": [], "total_count": 0},
    ),
    ToolConfig(
        name="analyze_events",
        impl=analyze_events_impl,
        request_type=AnalyzeEventsRequest,
        response_type=AnalyzeEventsResponse,
        description="""Analyze events across the project.

WORKFLOW: Use for frontend integration planning, indexer development, and audit.

PARAMETERS:
- path: Project directory path (required)
- contract_key: Optional, limit to specific contract
- name_filter: Filter by event name (case-insensitive substring)
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "name_filter": "Transfer"}

RETURNS: List of events with parameters (name, type, indexed).
         Summary with event counts per contract.

NEXT STEPS: get_contract_source (to see event declarations)""",
        error_kwargs={"events": [], "total_count": 0},
    ),
    ToolConfig(
        name="analyze_modifiers",
        impl=analyze_modifiers_impl,
        request_type=AnalyzeModifiersRequest,
        response_type=AnalyzeModifiersResponse,
        description="""Analyze custom modifiers and their usage across the project.

WORKFLOW: Use for access control analysis, modifier ordering review, and audit.

PARAMETERS:
- path: Project directory path (required)
- contract_key: Optional, limit to specific contract
- name_filter: Filter by modifier name (case-insensitive substring)
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project", "name_filter": "only"}

RETURNS: List of modifiers with usage counts and functions using them.
         Summary with modifiers per contract.

NEXT STEPS: list_functions (to see modifier usage), get_function_source""",
        error_kwargs={"modifiers": [], "total_count": 0},
    ),
    ToolConfig(
        name="analyze_low_level_calls",
        impl=analyze_low_level_calls_impl,
        request_type=AnalyzeLowLevelCallsRequest,
        response_type=AnalyzeLowLevelCallsResponse,
        description="""Find functions that use low-level calls (call, delegatecall, staticcall).

WORKFLOW: Use for security audits, gas optimization, and code review.

PARAMETERS:
- path: Project directory path (required)
- contract_key: Optional, limit to specific contract
- limit/offset: Pagination

EXAMPLE:
    {"path": "/project"}

RETURNS: List of functions with low-level calls.
         Summary with counts per contract.

NEXT STEPS: get_function_source (to review low-level call usage)""",
        error_kwargs={"calls": [], "total_count": 0},
    ),
)


def _make_tool_wrapper(
    tool_name: str,
    impl_func: Callable[[Any, ProjectFacts], ResponseT],
    response_class: type[ResponseT],
    error_kwargs: dict[str, Any],
    error_request_fields: tuple[str, ...],
    get_project_facts: Callable[[str], ProjectFacts],
) -> Callable[[Any], ResponseT]:
    """Create a wrapped tool function with project facts loading and error handling."""

    @track_tool_call(tool_name)
    def wrapper(request: RequestT) -> ResponseT:
        try:
            project_facts = get_project_facts(request.path)
            return impl_func(request, project_facts)
        except Exception as e:
            # Copy specified fields from request to error response
            extra_kwargs = {
                field: getattr(request, field)
                for field in error_request_fields
                if hasattr(request, field)
            }
            return response_class(
                success=False,
                error_message=f"Failed to load project: {e!s}",
                **error_kwargs,
                **extra_kwargs,
            )

    return wrapper


def _register_tool(
    mcp: FastMCP,
    config: ToolConfig,
    get_project_facts: Callable[[str], ProjectFacts],
) -> None:
    """Register a single tool with the MCP server."""
    wrapper = _make_tool_wrapper(
        config.name,
        config.impl,
        config.response_type,
        config.error_kwargs,
        config.error_request_fields,
        get_project_facts,
    )

    # Create a function with proper type annotations for FastMCP
    # FastMCP inspects __annotations__ and __doc__ to build tool schema
    def tool_func(request: Any) -> Any:
        return wrapper(request)

    # Set function metadata that FastMCP uses
    tool_func.__name__ = config.name
    tool_func.__doc__ = config.description
    tool_func.__annotations__ = {
        "request": config.request_type,
        "return": config.response_type,
    }

    mcp.tool()(tool_func)


def register_all_tools(
    mcp: FastMCP,
    get_project_facts: Callable[[str], ProjectFacts],
) -> None:
    """Register all Slither MCP tools with the FastMCP server."""
    for config in TOOL_CONFIGS:
        _register_tool(mcp, config, get_project_facts)


# List of all tool names for reference
TOOL_NAMES = [config.name for config in TOOL_CONFIGS]
