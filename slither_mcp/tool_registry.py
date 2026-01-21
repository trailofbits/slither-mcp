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
    GetStorageLayoutRequest,
    GetStorageLayoutResponse,
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
from slither_mcp.tools.get_storage_layout import get_storage_layout as get_storage_layout_impl
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
        description=(
            "Lists all contracts in a Solidity project with optional filtering by type and path. "
            "Use this when discovering contracts in an unfamiliar codebase, filtering out test/library "
            "dependencies, or finding specific contract types like interfaces or abstracts. Returns "
            "contract metadata including name, path, type flags (is_abstract, is_interface, is_library), "
            "and direct inheritance list. Does not include function details; use get_contract for full "
            "contract data. Supports pagination via offset/limit parameters."
        ),
        error_kwargs={"contracts": [], "total_count": 0},
    ),
    ToolConfig(
        name="get_contract",
        impl=get_contract_impl,
        request_type=GetContractRequest,
        response_type=GetContractResponse,
        description=(
            "Gets detailed metadata for a specific contract including inheritance hierarchy, declared "
            "and inherited functions, state variables, and events. Use this when you need complete "
            "information about a contract after finding it with list_contracts or search_contracts. "
            "Returns the full ContractModel with all relationships. For source code, use "
            "get_contract_source instead."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="get_contract_source",
        impl=get_contract_source_impl,
        request_type=GetContractSourceRequest,
        response_type=GetContractSourceResponse,
        description=(
            "Retrieves the source code of a contract from the original Solidity file. Use this when "
            "you need to read the actual implementation after finding a contract with list_contracts. "
            "Returns the source code as a string with optional line range filtering via start_line "
            "and max_lines parameters. Only returns the contract's portion of the file; for the full "
            "file, read it directly."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="get_function_source",
        impl=get_function_source_impl,
        request_type=GetFunctionSourceRequest,
        response_type=GetFunctionSourceResponse,
        description=(
            "Retrieves the source code of a specific function. Use this when you need to read the "
            "implementation details after finding a function with list_functions or search_functions. "
            "Returns the function body with line numbers. Requires the function's contract_key and "
            "full signature to uniquely identify the function."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="list_functions",
        impl=list_functions_impl,
        request_type=ListFunctionsRequest,
        response_type=ListFunctionsResponse,
        description=(
            "Lists functions across the project or filtered by contract, visibility, and modifier "
            "usage. Use this when searching for functions with specific characteristics like external "
            "entry points, functions with modifiers, or private helpers. Returns function signatures, "
            "visibility, modifiers, arguments, and return types. Does not include function source code; "
            "use get_function_source for that. Supports pagination and sorting."
        ),
        error_kwargs={"functions": [], "total_count": 0},
    ),
    ToolConfig(
        name="get_function_callees",
        impl=list_function_callees_impl,
        request_type=FunctionCalleesRequest,
        response_type=FunctionCalleesResponse,
        description=(
            "Gets all functions called by a specific function (outgoing edges in the call graph). "
            "Use this when tracing what a function does internally, finding dependencies, or "
            "understanding control flow. Returns categorized callees: internal (same contract), "
            "external (other contracts), and library calls, plus a flag for low-level calls "
            "(call/delegatecall). Does not recurse; call repeatedly to trace deeper."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="get_inherited_contracts",
        impl=get_inherited_contracts_impl,
        request_type=GetInheritedContractsRequest,
        response_type=GetInheritedContractsResponse,
        description=(
            "Gets the inheritance tree of parent contracts (upward traversal). Use this when "
            "understanding what a contract inherits, finding the source of inherited functions, or "
            "analyzing the inheritance hierarchy. Returns a recursive tree structure with parent "
            "contracts and their parents. Set max_depth to limit traversal depth; returns truncated "
            "flag if depth exceeded."
        ),
        error_kwargs={},
        error_request_fields=("contract_key",),
    ),
    ToolConfig(
        name="get_derived_contracts",
        impl=get_derived_contracts_impl,
        request_type=GetDerivedContractsRequest,
        response_type=GetDerivedContractsResponse,
        description=(
            "Gets all contracts that inherit from a specific contract (downward traversal). Use this "
            "when finding all implementations of a base contract, understanding the impact of changes "
            "to a parent, or discovering contract variants. Returns a recursive tree of child "
            "contracts. Set max_depth to limit; returns truncated flag if exceeded."
        ),
        error_kwargs={},
        error_request_fields=("contract_key",),
    ),
    ToolConfig(
        name="list_function_implementations",
        impl=list_function_implementations_impl,
        request_type=ListFunctionImplementationsRequest,
        response_type=ListFunctionImplementationsResponse,
        description=(
            "Finds all contracts that implement a specific function signature. Use this when looking "
            "for overrides of a virtual function, finding all implementations of an interface method, "
            "or understanding polymorphism in the codebase. Returns contracts with their implementation "
            "details. Matches by signature string. Supports pagination."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="get_function_callers",
        impl=list_function_callers_impl,
        request_type=FunctionCallersRequest,
        response_type=FunctionCallersResponse,
        description=(
            "Gets all functions that call a specific function (incoming edges in the call graph). "
            "Use this when finding entry points to a function, understanding usage patterns, or "
            "assessing impact of changes. Returns categorized callers: internal, external, and "
            "library. Useful for dead code detection and refactoring impact analysis."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="list_detectors",
        impl=list_detectors_impl,
        request_type=ListDetectorsRequest,
        response_type=ListDetectorsResponse,
        description=(
            "Lists all available Slither security detectors with their metadata. Use this to discover "
            "what security checks are available before running analysis, or to filter detectors by "
            "name. Returns detector name, description, impact level (High/Medium/Low/Informational), "
            "and confidence level. Does not run detection; use run_detectors for that."
        ),
        error_kwargs={"detectors": [], "total_count": 0},
    ),
    ToolConfig(
        name="run_detectors",
        impl=run_detectors_impl,
        request_type=RunDetectorsRequest,
        response_type=RunDetectorsResponse,
        description=(
            "Gets security findings from Slither's static analysis. Use this to find vulnerabilities, "
            "code quality issues, or informational findings in the project. Can filter by specific "
            "detectors, impact level, confidence, or exclude paths like tests. Returns findings with "
            "descriptions and source locations. Results are cached from initial analysis."
        ),
        error_kwargs={"results": [], "total_count": 0},
    ),
    ToolConfig(
        name="search_contracts",
        impl=search_contracts_impl,
        request_type=SearchContractsRequest,
        response_type=SearchContractsResponse,
        description=(
            "Searches for contracts by name using regex pattern matching. Use this when you know part "
            "of a contract name but not its exact path or when looking for contracts following a "
            "naming convention. Returns matching contracts with full metadata. Case-insensitive by "
            "default; set case_sensitive=true for exact matching. Supports pagination."
        ),
        error_kwargs={"matches": [], "total_count": 0},
    ),
    ToolConfig(
        name="search_functions",
        impl=search_functions_impl,
        request_type=SearchFunctionsRequest,
        response_type=SearchFunctionsResponse,
        description=(
            "Searches for functions by name or signature using regex pattern matching. Use this when "
            "looking for functions across the codebase by name pattern or parameter types. Can search "
            "function names only or full signatures including parameters. Returns matching functions "
            "with full metadata. Supports pagination."
        ),
        error_kwargs={"matches": [], "total_count": 0},
    ),
    ToolConfig(
        name="get_project_overview",
        impl=get_project_overview_impl,
        request_type=GetProjectOverviewRequest,
        response_type=GetProjectOverviewResponse,
        description=(
            "Gets aggregate statistics about the entire project including contract counts by type, "
            "function counts by visibility, and security findings by impact level. Use this as a "
            "starting point when exploring an unfamiliar codebase or generating project summaries. "
            "Returns counts and distributions, not detailed data. Use list_contracts and run_detectors "
            "for details."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="find_dead_code",
        impl=find_dead_code_impl,
        request_type=FindDeadCodeRequest,
        response_type=FindDeadCodeResponse,
        description=(
            "Finds functions with no callers (potential dead code). Use this during code cleanup, "
            "auditing for unused code, or understanding code coverage. Can exclude known entry points "
            "(external/public functions), test framework functions, and inherited functions. Returns "
            "uncalled functions with their metadata. Some functions may be called dynamically and not "
            "detected. Supports pagination."
        ),
        error_kwargs={"dead_functions": [], "total_count": 0},
    ),
    ToolConfig(
        name="export_call_graph",
        impl=export_call_graph_impl,
        request_type=ExportCallGraphRequest,
        response_type=ExportCallGraphResponse,
        description=(
            "Exports the project's function call graph in Mermaid or DOT visualization format. Use "
            "this when you need a visual representation of function relationships or for documentation. "
            "Can filter to specific contracts or entry points only. Returns a string in the requested "
            "format suitable for rendering. May be large for big projects; use max_nodes to limit."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="get_contract_dependencies",
        impl=get_contract_dependencies_impl,
        request_type=GetContractDependenciesRequest,
        response_type=GetContractDependenciesResponse,
        description=(
            "Maps all dependencies for a specific contract including inheritance, external calls, and "
            "library usage. Use this when understanding what a contract depends on, finding coupling "
            "issues, or detecting circular dependencies. Returns categorized dependencies with optional "
            "circular dependency detection."
        ),
        error_kwargs={},
    ),
    ToolConfig(
        name="analyze_state_variables",
        impl=analyze_state_variables_impl,
        request_type=AnalyzeStateVariablesRequest,
        response_type=AnalyzeStateVariablesResponse,
        description=(
            "Analyzes state variables across the project or for a specific contract. Use this when "
            "auditing storage layout, finding public state, or understanding contract data. Can filter "
            "by visibility, include/exclude constants and immutables. Returns variable details including "
            "type, visibility, and declaration location. For storage slot layout, use get_storage_layout. "
            "Supports pagination."
        ),
        error_kwargs={"variables": [], "total_count": 0},
    ),
    ToolConfig(
        name="get_storage_layout",
        impl=get_storage_layout_impl,
        request_type=GetStorageLayoutRequest,
        response_type=GetStorageLayoutResponse,
        description=(
            "Computes the storage slot layout for a contract showing slot numbers, byte offsets, and "
            "variable sizes. Use this for upgrade safety analysis, storage collision detection, or "
            "understanding how variables are packed. Returns ordered slot assignments following "
            "Solidity's packing rules. Excludes constants and immutables (not in storage). Can include "
            "or exclude inherited storage. Supports pagination."
        ),
        error_kwargs={"storage_slots": [], "total_count": 0, "total_slots_used": 0},
        error_request_fields=("contract_key",),
    ),
    ToolConfig(
        name="analyze_events",
        impl=analyze_events_impl,
        request_type=AnalyzeEventsRequest,
        response_type=AnalyzeEventsResponse,
        description=(
            "Analyzes event definitions across the project or for a specific contract. Use this when "
            "understanding what events a contract emits, finding indexed parameters, or auditing "
            "logging. Returns event names, parameters with types and indexed flags, and source "
            "locations. Does not find event emissions; search source code for that. Supports pagination."
        ),
        error_kwargs={"events": [], "total_count": 0},
    ),
    ToolConfig(
        name="analyze_modifiers",
        impl=analyze_modifiers_impl,
        request_type=AnalyzeModifiersRequest,
        response_type=AnalyzeModifiersResponse,
        description=(
            "Analyzes custom modifier definitions and their usage across functions. Use this when "
            "auditing access control patterns, finding modifier implementations, or understanding "
            "function guards. Returns modifier definitions with their source and a list of functions "
            "that use each modifier. Supports pagination."
        ),
        error_kwargs={"modifiers": [], "total_count": 0},
    ),
    ToolConfig(
        name="analyze_low_level_calls",
        impl=analyze_low_level_calls_impl,
        request_type=AnalyzeLowLevelCallsRequest,
        response_type=AnalyzeLowLevelCallsResponse,
        description=(
            "Finds all functions using low-level calls (call, delegatecall, staticcall, or assembly). "
            "Use this for security auditing since low-level calls bypass Solidity's type safety and "
            "can introduce vulnerabilities. Returns functions grouped by call type with source "
            "locations. Critical for reentrancy and proxy pattern analysis. Supports pagination."
        ),
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
    def wrapper(request: Any) -> ResponseT:
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
