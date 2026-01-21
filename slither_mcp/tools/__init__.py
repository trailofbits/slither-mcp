"""MCP tools for Slither analysis.

This module provides a unified import point for all MCP tools.
Each tool has its own module with request/response models and implementation.
"""

# Query tools - for browsing and filtering data
# Analysis tools
from slither_mcp.tools.analyze_events import (
    AnalyzeEventsRequest,
    AnalyzeEventsResponse,
    EventInfo,
    analyze_events,
)
from slither_mcp.tools.analyze_low_level_calls import (
    AnalyzeLowLevelCallsRequest,
    AnalyzeLowLevelCallsResponse,
    LowLevelCallInfo,
    analyze_low_level_calls,
)
from slither_mcp.tools.analyze_modifiers import (
    AnalyzeModifiersRequest,
    AnalyzeModifiersResponse,
    ModifierUsage,
    analyze_modifiers,
)
from slither_mcp.tools.analyze_state_variables import (
    AnalyzeStateVariablesRequest,
    AnalyzeStateVariablesResponse,
    StateVariableInfo,
    analyze_state_variables,
)
from slither_mcp.tools.export_call_graph import (
    ExportCallGraphRequest,
    ExportCallGraphResponse,
    export_call_graph,
)
from slither_mcp.tools.find_dead_code import (
    DeadCodeFunction,
    FindDeadCodeRequest,
    FindDeadCodeResponse,
    find_dead_code,
)
from slither_mcp.tools.get_contract import (
    GetContractRequest,
    GetContractResponse,
    get_contract,
)
from slither_mcp.tools.get_contract_dependencies import (
    CircularDependency,
    ContractDependencies,
    ContractDependency,
    GetContractDependenciesRequest,
    GetContractDependenciesResponse,
    get_contract_dependencies,
)
from slither_mcp.tools.get_contract_source import (
    GetContractSourceRequest,
    GetContractSourceResponse,
    get_contract_source,
)
from slither_mcp.tools.get_derived_contracts import (
    DerivedNode,
    GetDerivedContractsRequest,
    GetDerivedContractsResponse,
    get_derived_contracts,
)
from slither_mcp.tools.get_function_source import (
    GetFunctionSourceRequest,
    GetFunctionSourceResponse,
    get_function_source,
)
from slither_mcp.tools.get_inherited_contracts import (
    GetInheritedContractsRequest,
    GetInheritedContractsResponse,
    InheritanceNode,
    get_inherited_contracts,
)
from slither_mcp.tools.get_project_overview import (
    GetProjectOverviewRequest,
    GetProjectOverviewResponse,
    ProjectOverview,
    get_project_overview,
)
from slither_mcp.tools.list_contracts import (
    ContractInfo,
    ListContractsRequest,
    ListContractsResponse,
    list_contracts,
)
from slither_mcp.tools.list_detectors import (
    ListDetectorsRequest,
    ListDetectorsResponse,
    list_detectors,
)

# Analysis tools - for deep analysis
from slither_mcp.tools.list_function_callees import (
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    list_function_callees,
)
from slither_mcp.tools.list_function_callers import (
    FunctionCallers,
    FunctionCallersRequest,
    FunctionCallersResponse,
    list_function_callers,
)
from slither_mcp.tools.list_function_implementations import (
    ImplementationInfo,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    list_function_implementations,
)
from slither_mcp.tools.list_functions import (
    FunctionInfo,
    ListFunctionsRequest,
    ListFunctionsResponse,
    list_functions,
)
from slither_mcp.tools.run_detectors import (
    RunDetectorsRequest,
    RunDetectorsResponse,
    run_detectors,
)
from slither_mcp.tools.search_contracts import (
    SearchContractsRequest,
    SearchContractsResponse,
    search_contracts,
)
from slither_mcp.tools.search_functions import (
    SearchFunctionsRequest,
    SearchFunctionsResponse,
    search_functions,
)

__all__ = [
    # Query tools
    "ContractInfo",
    "ListContractsRequest",
    "ListContractsResponse",
    "list_contracts",
    "GetContractRequest",
    "GetContractResponse",
    "get_contract",
    "GetContractSourceRequest",
    "GetContractSourceResponse",
    "get_contract_source",
    "GetFunctionSourceRequest",
    "GetFunctionSourceResponse",
    "get_function_source",
    "FunctionInfo",
    "ListFunctionsRequest",
    "ListFunctionsResponse",
    "list_functions",
    # Analysis tools
    "FunctionCalleesRequest",
    "FunctionCalleesResponse",
    "list_function_callees",
    "InheritanceNode",
    "GetInheritedContractsRequest",
    "GetInheritedContractsResponse",
    "get_inherited_contracts",
    "DerivedNode",
    "GetDerivedContractsRequest",
    "GetDerivedContractsResponse",
    "get_derived_contracts",
    "ImplementationInfo",
    "ListFunctionImplementationsRequest",
    "ListFunctionImplementationsResponse",
    "list_function_implementations",
    "FunctionCallers",
    "FunctionCallersRequest",
    "FunctionCallersResponse",
    "list_function_callers",
    # Detector tools
    "ListDetectorsRequest",
    "ListDetectorsResponse",
    "list_detectors",
    "RunDetectorsRequest",
    "RunDetectorsResponse",
    "run_detectors",
    # Search tools
    "SearchContractsRequest",
    "SearchContractsResponse",
    "search_contracts",
    "SearchFunctionsRequest",
    "SearchFunctionsResponse",
    "search_functions",
    # Project overview and dead code tools
    "GetProjectOverviewRequest",
    "GetProjectOverviewResponse",
    "ProjectOverview",
    "get_project_overview",
    "DeadCodeFunction",
    "FindDeadCodeRequest",
    "FindDeadCodeResponse",
    "find_dead_code",
    "ExportCallGraphRequest",
    # New analysis tools
    "AnalyzeEventsRequest",
    "AnalyzeEventsResponse",
    "EventInfo",
    "analyze_events",
    "AnalyzeLowLevelCallsRequest",
    "AnalyzeLowLevelCallsResponse",
    "LowLevelCallInfo",
    "analyze_low_level_calls",
    "AnalyzeModifiersRequest",
    "AnalyzeModifiersResponse",
    "ModifierUsage",
    "analyze_modifiers",
    "AnalyzeStateVariablesRequest",
    "AnalyzeStateVariablesResponse",
    "StateVariableInfo",
    "analyze_state_variables",
    "ExportCallGraphResponse",
    "export_call_graph",
    "ContractDependency",
    "ContractDependencies",
    "CircularDependency",
    "GetContractDependenciesRequest",
    "GetContractDependenciesResponse",
    "get_contract_dependencies",
]
