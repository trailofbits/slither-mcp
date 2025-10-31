#!/usr/bin/env python3
"""Slither MCP Server - Main entry point."""

import argparse
import logging
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

from slither_mcp.metrics import (
    disable_metrics_permanently,
    get_metrics_config_path,
    initialize_metrics,
    is_metrics_disabled,
    track_tool_call,
)
from slither_mcp.artifacts import (
    artifacts_exist,
    load_project_facts,
    save_project_facts,
)
from slither_mcp.facts import get_project_facts
from slither_mcp.slither_wrapper import LazySlither
from slither_mcp.types import ProjectFacts
# Import all tools from the tools package
from slither_mcp.tools import (
    # Query tools - for browsing and filtering data
    ListContractsRequest,
    ListContractsResponse,
    list_contracts as list_contracts_impl,
    GetContractRequest,
    GetContractResponse,
    get_contract as get_contract_impl,
    GetContractSourceRequest,
    GetContractSourceResponse,
    get_contract_source as get_contract_source_impl,
    GetFunctionSourceRequest,
    GetFunctionSourceResponse,
    get_function_source as get_function_source_impl,
    ListFunctionsRequest,
    ListFunctionsResponse,
    list_functions as list_functions_impl,
    # Analysis tools - for deep analysis
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    list_function_callees as list_function_callees_impl,
    GetInheritedContractsRequest,
    GetInheritedContractsResponse,
    get_inherited_contracts as get_inherited_contracts_impl,
    GetDerivedContractsRequest,
    GetDerivedContractsResponse,
    get_derived_contracts as get_derived_contracts_impl,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    list_function_implementations as list_function_implementations_impl,
    FunctionCallersRequest,
    FunctionCallersResponse,
    list_function_callers as list_function_callers_impl,
    # Detector tools
    ListDetectorsRequest,
    ListDetectorsResponse,
    list_detectors as list_detectors_impl,
    RunDetectorsRequest,
    RunDetectorsResponse,
    run_detectors as run_detectors_impl,
)






# Global cache to hold project facts for multiple projects
project_facts_cache: dict[str, ProjectFacts] = {}


def get_or_load_project_facts(path: str) -> ProjectFacts:
    """
    Get or load ProjectFacts for a given project path.

    This function implements the caching strategy:
    1. Check if already in memory cache
    2. If not, check for artifacts/project_facts.json
    3. If cache exists, load it
    4. Otherwise, run Slither analysis and cache the results

    Args:
        path: Path to the project directory

    Returns:
        ProjectFacts for the project

    Raises:
        ValueError: If path doesn't exist or isn't a directory
        Exception: If Slither analysis fails
    """
    # Normalize to absolute path
    abs_path = os.path.abspath(path)

    # Check if already cached in memory
    if abs_path in project_facts_cache:
        return project_facts_cache[abs_path]

    # Validate path
    if not os.path.exists(abs_path):
        raise ValueError(f"Path does not exist: {abs_path}")

    if not os.path.isdir(abs_path):
        raise ValueError(f"Path is not a directory: {abs_path}")

    # Set up artifacts directory
    artifacts_dir = Path(abs_path) / "artifacts"

    # Try to load from cache file
    if artifacts_exist(str(artifacts_dir)):
        logging.info(f"Loading cached project facts from {artifacts_dir}/project_facts.json")
        facts = load_project_facts(str(artifacts_dir))
        if facts is not None:
            logging.info(f"Loaded {len(facts.contracts)} contracts from cache")
            project_facts_cache[abs_path] = facts
            return facts
        else:
            logging.warning("Failed to load cache, will re-scan project")

    # Run Slither analysis
    logging.info(f"Analyzing project at: {abs_path}")
    lazy_slither = LazySlither(abs_path)

    # Generate project facts
    logging.info("Generating project facts...")
    facts = get_project_facts(abs_path, lazy_slither)
    logging.info(f"Generated facts for {len(facts.contracts)} contracts")

    # Save to artifacts directory
    save_project_facts(facts, str(artifacts_dir))

    # Cache in memory
    project_facts_cache[abs_path] = facts

    return facts


def main():
    """Main entry point for the MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Slither MCP Server")
    parser.add_argument(
        "--enhanced-error-reporting",
        action="store_true",
        help="Enable Sentry error reporting for comprehensive exception monitoring"
    )
    parser.add_argument(
        "--disable-metrics",
        action="store_true",
        help="Permanently disable metrics and error reporting"
    )
    args = parser.parse_args()
    
    # Check persisted metrics preference
    metrics_disabled = is_metrics_disabled()
    
    # Handle --disable-metrics flag
    if args.disable_metrics:
        disable_metrics_permanently()
        metrics_disabled = True
        print(f"Metrics disabled permanently (created {get_metrics_config_path()})", file=sys.stderr)
    
    # Check if metrics are disabled
    if metrics_disabled:
        if args.enhanced_error_reporting:
            print("ERROR: Cannot use --enhanced-error-reporting when metrics are disabled.", file=sys.stderr)
            print(f"Remove {get_metrics_config_path()} to re-enable metrics.", file=sys.stderr)
            sys.exit(1)
        print(f"Metrics disabled (found {get_metrics_config_path()})", file=sys.stderr)
    else:
        # Initialize metrics
        initialize_metrics(enable_enhanced_error_reporting=args.enhanced_error_reporting)
        print("Metrics enabled", file=sys.stderr)
        
        if args.enhanced_error_reporting:
            print("Enhanced error reporting enabled", file=sys.stderr)
    
    # Configure all logging to use stderr FIRST
    # This is critical for stdio transport - stdout is used for MCP protocol
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(message)s',
        datefmt='%m/%d/%y %H:%M:%S'
    ))
    logging.root.addHandler(stderr_handler)
    logging.root.setLevel(logging.WARNING)

    # Create FastMCP server
    mcp = FastMCP("slither-mcp")

    # Register all analysis tools

    @mcp.tool()
    @track_tool_call("list_contracts")
    def list_contracts(request: ListContractsRequest) -> ListContractsResponse:
        """
        List all contracts with optional filters.

        Supports filtering by contract type (concrete, interface, library, abstract)
        and by path pattern (glob-style matching).
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return list_contracts_impl(request, project_facts)
        except Exception as e:
            return ListContractsResponse(
                success=False,
                contracts=[],
                total_count=0,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("get_contract")
    def get_contract(request: GetContractRequest) -> GetContractResponse:
        """
        Get detailed information about a specific contract.

        Returns complete contract metadata including inheritance, functions,
        and contract type information.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return get_contract_impl(request, project_facts)
        except Exception as e:
            return GetContractResponse(
                success=False,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("get_contract_source")
    def get_contract_source(request: GetContractSourceRequest) -> GetContractSourceResponse:
        """
        Get the full source code of the file where a contract is implemented.

        Returns the complete source code of the Solidity file containing the contract,
        along with the file path.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return get_contract_source_impl(request, project_facts)
        except Exception as e:
            return GetContractSourceResponse(
                success=False,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("get_function_source")
    def get_function_source(request: GetFunctionSourceRequest) -> GetFunctionSourceResponse:
        """
        Get the source code of a specific function.

        Returns the source code for a specific function identified by its FunctionKey,
        along with the file path and line numbers where it's defined.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return get_function_source_impl(request, project_facts)
        except Exception as e:
            return GetFunctionSourceResponse(
                success=False,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("list_functions")
    def list_functions(request: ListFunctionsRequest) -> ListFunctionsResponse:
        """
        List functions with optional filters.

        Can filter by contract, visibility (public/external/internal/private),
        and solidity modifiers (view/pure/payable/virtual/etc).
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return list_functions_impl(request, project_facts)
        except Exception as e:
            return ListFunctionsResponse(
                success=False,
                functions=[],
                total_count=0,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("function_callees")
    def function_callees(request: FunctionCalleesRequest) -> FunctionCalleesResponse:
        """
        Get the internal, external, and library callees for a function.

        This tool resolves a function in a given calling context and returns
        all the functions it calls (internal, external, and library calls).
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return list_function_callees_impl(request, project_facts)
        except Exception as e:
            from slither_mcp.types import QueryContext
            return FunctionCalleesResponse(
                success=False,
                query_context=QueryContext(),
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("get_inherited_contracts")
    def get_inherited_contracts(request: GetInheritedContractsRequest) -> GetInheritedContractsResponse:
        """
        Get the inherited contracts for a contract.

        This tool returns both the directly inherited contracts and the full
        inheritance hierarchy (including transitive inheritance).
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return get_inherited_contracts_impl(request, project_facts)
        except Exception as e:
            return GetInheritedContractsResponse(
                success=False,
                contract_key=request.contract_key,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("get_derived_contracts")
    def get_derived_contracts(request: GetDerivedContractsRequest) -> GetDerivedContractsResponse:
        """
        Get the derived contracts for a contract (contracts that inherit from it).

        This tool returns both the directly derived contracts and the full
        derived hierarchy (including transitive derivation), showing all contracts
        that directly or indirectly inherit from the specified contract.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return get_derived_contracts_impl(request, project_facts)
        except Exception as e:
            return GetDerivedContractsResponse(
                success=False,
                contract_key=request.contract_key,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("list_function_implementations")
    def list_function_implementations(request: ListFunctionImplementationsRequest) -> ListFunctionImplementationsResponse:
        """
        List all contracts that implement a specific function.

        This tool finds all contracts that provide an implementation of a given function
        signature. It's particularly useful for finding implementations of abstract
        functions or interface methods.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return list_function_implementations_impl(request, project_facts)
        except Exception as e:
            return ListFunctionImplementationsResponse(
                success=False,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("function_callers")
    def function_callers(request: FunctionCallersRequest) -> FunctionCallersResponse:
        """
        Get all functions that call the target function, grouped by call type.

        This tool finds all functions in the project that may call the target function
        by checking each function's callees lists. Results are grouped by call type:
        internal, external, and library calls.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return list_function_callers_impl(request, project_facts)
        except Exception as e:
            from slither_mcp.types import QueryContext
            return FunctionCallersResponse(
                success=False,
                query_context=QueryContext(),
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("list_detectors")
    def list_detectors(request: ListDetectorsRequest) -> ListDetectorsResponse:
        """
        List all available Slither detectors with their metadata.

        This tool returns information about all available Slither detectors including
        their names, descriptions, impact levels, and confidence ratings. You can
        optionally filter by name or description using the name_filter parameter.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return list_detectors_impl(request, project_facts)
        except Exception as e:
            return ListDetectorsResponse(
                success=False,
                detectors=[],
                total_count=0,
                error_message=f"Failed to load project: {str(e)}"
            )

    @mcp.tool()
    @track_tool_call("run_detectors")
    def run_detectors(request: RunDetectorsRequest) -> RunDetectorsResponse:
        """
        Retrieve cached Slither detector results with optional filtering.

        This tool returns the results from running Slither detectors on the project.
        Results are cached during initialization and can be filtered by detector name,
        impact level (High, Medium, Low, Informational), and confidence level
        (High, Medium, Low). Each result includes source locations (file path and
        line numbers) for the findings.
        """
        try:
            project_facts = get_or_load_project_facts(request.path)
            return run_detectors_impl(request, project_facts)
        except Exception as e:
            return RunDetectorsResponse(
                success=False,
                results=[],
                total_count=0,
                error_message=f"Failed to load project: {str(e)}"
            )

    # Start the server
    print("Starting Slither MCP server...", file=sys.stderr)
    print("All tools accept a 'path' parameter for project directory", file=sys.stderr)
    print("Projects are cached automatically in <path>/artifacts/", file=sys.stderr)

    print("\nAvailable tools:", file=sys.stderr)
    print("  - list_contracts", file=sys.stderr)
    print("  - get_contract", file=sys.stderr)
    print("  - get_contract_source", file=sys.stderr)
    print("  - get_function_source", file=sys.stderr)
    print("  - list_functions", file=sys.stderr)
    print("  - function_callees", file=sys.stderr)
    print("  - function_callers", file=sys.stderr)
    print("  - get_inherited_contracts", file=sys.stderr)
    print("  - get_derived_contracts", file=sys.stderr)
    print("  - list_function_implementations", file=sys.stderr)
    print("  - list_detectors", file=sys.stderr)
    print("  - run_detectors", file=sys.stderr)

    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()

