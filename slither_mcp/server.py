#!/usr/bin/env python3
"""Slither MCP Server - Main entry point."""

import argparse
import logging
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

from slither_mcp.artifacts import (
    artifacts_exist,
    load_project_facts,
    save_project_facts,
)
from slither_mcp.facts import get_project_facts
from slither_mcp.slither_wrapper import LazySlither
from slither_mcp.types import ContractKey, FunctionKey, ProjectFacts
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


# Global state to hold project facts
project_facts: ProjectFacts | None = None
project_path: str | None = None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Slither MCP Server - Static analysis server for Solidity contracts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the Solidity project to analyze"
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached artifacts if available instead of re-scanning"
    )
    
    return parser.parse_args()


def initialize_slither(path: str, use_cache: bool) -> ProjectFacts:
    """
    Initialize Slither and generate or load project facts.
    
    Args:
        path: Path to the project to analyze
        use_cache: Whether to use cached artifacts if available
        
    Returns:
        ProjectFacts containing all contract and function metadata
    """
    # Convert to absolute path
    abs_path = os.path.abspath(path)
    
    if not os.path.exists(abs_path):
        print(f"Error: Path '{abs_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Set up artifacts directory
    artifacts_dir = Path(abs_path) / "artifacts"
    
    # Try to load from cache if requested
    if use_cache and artifacts_exist(str(artifacts_dir)):
        print(f"Loading cached project facts from {artifacts_dir}/project_facts.json", file=sys.stderr)
        facts = load_project_facts(str(artifacts_dir))
        if facts is not None:
            print(f"Loaded {len(facts.contracts)} contracts from cache", file=sys.stderr)
            return facts
        else:
            print("Failed to load cache, will re-scan project", file=sys.stderr)
    
    # Run Slither analysis
    print(f"Analyzing project at: {abs_path}", file=sys.stderr)
    lazy_slither = LazySlither(abs_path)
    
    # Generate project facts
    print("Generating project facts...", file=sys.stderr)
    facts = get_project_facts(abs_path, lazy_slither)
    print(f"Generated facts for {len(facts.contracts)} contracts", file=sys.stderr)
    
    # Save to artifacts directory
    save_project_facts(facts, str(artifacts_dir))
    
    return facts


def main():
    """Main entry point for the MCP server."""
    global project_facts, project_path
    
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
    
    # Parse command-line arguments
    args = parse_args()
    
    # Store project path
    project_path = os.path.abspath(args.path)
    
    # Initialize Slither and load/generate facts
    project_facts = initialize_slither(args.path, args.use_cache)
    
    # Create FastMCP server
    mcp = FastMCP("slither-mcp")
    
    # Register Query Tools - for browsing and filtering data
    
    @mcp.tool()
    def list_contracts(filter_type: str = "all") -> ListContractsResponse:
        """
        List all contracts with optional filters.
        
        Supports filtering by contract type (concrete, interface, library, abstract)
        and by path pattern (glob-style matching).
        
        Args:
            filter_type: Type of contracts to list - "all", "concrete", "interface", "library", or "abstract" (default: "all")
        """
        request = ListContractsRequest(filter_type=filter_type)
        return list_contracts_impl(request, project_facts)
    
    @mcp.tool()
    def get_contract(contract_key: dict, include_functions: bool = True) -> GetContractResponse:
        """
        Get detailed information about a specific contract.
        
        Returns complete contract metadata including inheritance, functions,
        and contract type information.
        
        Args:
            contract_key: Dictionary with 'contract_name' and 'path' keys
            include_functions: Whether to include function details (default: True)
        """
        contract_key_obj = ContractKey(**contract_key)
        request = GetContractRequest(contract_key=contract_key_obj, include_functions=include_functions)
        return get_contract_impl(request, project_facts)
    
    @mcp.tool()
    def get_contract_source(contract_key: dict) -> GetContractSourceResponse:
        """
        Get the full source code of the file where a contract is implemented.
        
        Returns the complete source code of the Solidity file containing the contract,
        along with the file path.
        
        Args:
            contract_key: Dictionary with 'contract_name' and 'path' keys
        """
        contract_key_obj = ContractKey(**contract_key)
        request = GetContractSourceRequest(contract_key=contract_key_obj)
        return get_contract_source_impl(request, project_facts)
    
    @mcp.tool()
    def get_function_source(function_key: dict) -> GetFunctionSourceResponse:
        """
        Get the source code of a specific function.
        
        Returns the source code for a specific function identified by its FunctionKey,
        along with the file path and line numbers where it's defined.
        
        Args:
            function_key: Dictionary with 'signature', 'contract_name', and 'path' keys
        """
        function_key_obj = FunctionKey(**function_key)
        request = GetFunctionSourceRequest(function_key=function_key_obj)
        return get_function_source_impl(request, project_facts)
    
    @mcp.tool()
    def list_functions(
        contract_key: dict,
        visibility: list[str] | None = None,
        has_modifiers: list[str] | None = None
    ) -> ListFunctionsResponse:
        """
        List functions with optional filters.
        
        Can filter by contract, visibility (public/external/internal/private),
        and solidity modifiers (view/pure/payable/virtual/etc).
        
        Args:
            contract_key: Dictionary with 'contract_name' and 'path' keys
            visibility: Optional list of visibility filters (e.g., ["public", "external"])
            has_modifiers: Optional list of modifier filters (e.g., ["view", "pure"])
        """
        contract_key_obj = ContractKey(**contract_key)
        request = ListFunctionsRequest(
            contract_key=contract_key_obj,
            visibility=visibility,
            has_modifiers=has_modifiers
        )
        return list_functions_impl(request, project_facts)
    
    # Register Analysis Tools - for deep analysis
    
    @mcp.tool()
    def function_callees(function_key: dict) -> FunctionCalleesResponse:
        """
        Get the internal, external, and library callees for a function.
        
        This tool resolves a function in a given calling context and returns
        all the functions it calls (internal, external, and library calls).
        
        Args:
            function_key: Dictionary with 'signature', 'contract_name', and 'path' keys
        """
        function_key_obj = FunctionKey(**function_key)
        request = FunctionCalleesRequest(function_key=function_key_obj)
        return list_function_callees_impl(request, project_facts)
    
    @mcp.tool()
    def get_inherited_contracts(contract_key: dict) -> GetInheritedContractsResponse:
        """
        Get the inherited contracts for a contract.
        
        This tool returns both the directly inherited contracts and the full
        inheritance hierarchy (including transitive inheritance).
        
        Args:
            contract_key: Dictionary with 'contract_name' and 'path' keys
        """
        contract_key_obj = ContractKey(**contract_key)
        request = GetInheritedContractsRequest(contract_key=contract_key_obj)
        return get_inherited_contracts_impl(request, project_facts)
    
    @mcp.tool()
    def get_derived_contracts(contract_key: dict) -> GetDerivedContractsResponse:
        """
        Get the derived contracts for a contract (contracts that inherit from it).
        
        This tool returns both the directly derived contracts and the full
        derived hierarchy (including transitive derivation), showing all contracts
        that directly or indirectly inherit from the specified contract.
        
        Args:
            contract_key: Dictionary with 'contract_name' and 'path' keys
        """
        # Parse the contract_key dict into a ContractKey model
        contract_key_obj = ContractKey(**contract_key)
        request = GetDerivedContractsRequest(contract_key=contract_key_obj)
        return get_derived_contracts_impl(request, project_facts)
    
    @mcp.tool()
    def list_function_implementations(contract_key: dict, function_signature: str) -> ListFunctionImplementationsResponse:
        """
        List all contracts that implement a specific function.
        
        This tool finds all contracts that provide an implementation of a given function
        signature. It's particularly useful for finding implementations of abstract
        functions or interface methods.
        
        Args:
            contract_key: Dictionary with 'contract_name' and 'path' keys (typically an abstract contract or interface)
            function_signature: The function signature to search for (e.g., "transfer(address,uint256)")
        """
        contract_key_obj = ContractKey(**contract_key)
        request = ListFunctionImplementationsRequest(
            contract_key=contract_key_obj,
            function_signature=function_signature
        )
        return list_function_implementations_impl(request, project_facts)
    
    @mcp.tool()
    def function_callers(function_key: dict) -> FunctionCallersResponse:
        """
        Get all functions that call the target function, grouped by call type.
        
        This tool finds all functions in the project that may call the target function
        by checking each function's callees lists. Results are grouped by call type:
        internal, external, and library calls.
        
        Args:
            function_key: Dictionary with 'signature', 'contract_name', and 'path' keys
        """
        function_key_obj = FunctionKey(**function_key)
        request = FunctionCallersRequest(function_key=function_key_obj)
        return list_function_callers_impl(request, project_facts)
    
    @mcp.tool()
    def list_detectors(name_filter: str | None = None) -> ListDetectorsResponse:
        """
        List all available Slither detectors with their metadata.
        
        This tool returns information about all available Slither detectors including
        their names, descriptions, impact levels, and confidence ratings. You can
        optionally filter by name or description using the name_filter parameter.
        
        Args:
            name_filter: Optional string to filter detectors by name or description
        """
        request = ListDetectorsRequest(name_filter=name_filter)
        return list_detectors_impl(request, project_facts)
    
    @mcp.tool()
    def run_detectors(
        detector_names: list[str] | None = None,
        impact: list[str] | None = None,
        confidence: list[str] | None = None
    ) -> RunDetectorsResponse:
        """
        Retrieve cached Slither detector results with optional filtering.
        
        This tool returns the results from running Slither detectors on the project.
        Results are cached during initialization and can be filtered by detector name,
        impact level (High, Medium, Low, Informational), and confidence level
        (High, Medium, Low). Each result includes source locations (file path and
        line numbers) for the findings.
        
        Args:
            detector_names: Optional list of detector names to filter by
            impact: Optional list of impact levels to filter by (e.g., ["High", "Medium"])
            confidence: Optional list of confidence levels to filter by (e.g., ["High", "Medium"])
        """
        request = RunDetectorsRequest(
            detector_names=detector_names,
            impact=impact,
            confidence=confidence
        )
        return run_detectors_impl(request, project_facts)
    
    # Run the server
    print("Starting Slither MCP server...", file=sys.stderr)
    print(f"Project: {project_path}", file=sys.stderr)
    print(f"Contracts loaded: {len(project_facts.contracts)}", file=sys.stderr)
    print("Tools available:", file=sys.stderr)
    print("  - function_callees", file=sys.stderr)
    print("  - function_callers", file=sys.stderr)
    print("  - get_inherited_contracts", file=sys.stderr)
    print("  - get_derived_contracts", file=sys.stderr)
    print("  - list_function_implementations", file=sys.stderr)
    print("  - list_contracts", file=sys.stderr)
    print("  - get_contract", file=sys.stderr)
    print("  - get_contract_source", file=sys.stderr)
    print("  - get_function_source", file=sys.stderr)
    print("  - list_functions", file=sys.stderr)
    print("  - list_detectors", file=sys.stderr)
    print("  - run_detectors", file=sys.stderr)
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()

