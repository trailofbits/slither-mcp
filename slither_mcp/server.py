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
    ListFunctionsRequest,
    ListFunctionsResponse,
    list_functions as list_functions_impl,
    # Analysis tools - for deep analysis
    FunctionCalleesRequest,
    FunctionCalleesResponse,
    list_function_callees as list_function_callees_impl,
    InheritanceHierarchyRequest,
    InheritanceHierarchyResponse,
    get_inheritance_hierarchy as get_inheritance_hierarchy_impl,
    ListFunctionImplementationsRequest,
    ListFunctionImplementationsResponse,
    list_function_implementations as list_function_implementations_impl,
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
    def list_contracts(request: ListContractsRequest) -> ListContractsResponse:
        """
        List all contracts with optional filters.
        
        Supports filtering by contract type (concrete, interface, library, abstract)
        and by path pattern (glob-style matching).
        """
        return list_contracts_impl(request, project_facts)
    
    @mcp.tool()
    def get_contract(request: GetContractRequest) -> GetContractResponse:
        """
        Get detailed information about a specific contract.
        
        Returns complete contract metadata including inheritance, functions,
        and contract type information.
        """
        return get_contract_impl(request, project_facts)
    
    @mcp.tool()
    def list_functions(request: ListFunctionsRequest) -> ListFunctionsResponse:
        """
        List functions with optional filters.
        
        Can filter by contract, visibility (public/external/internal/private),
        and solidity modifiers (view/pure/payable/virtual/etc).
        """
        return list_functions_impl(request, project_facts)
    
    # Register Analysis Tools - for deep analysis
    
    @mcp.tool()
    def function_callees(request: FunctionCalleesRequest) -> FunctionCalleesResponse:
        """
        Get the internal, external, and library callees for a function.
        
        This tool resolves a function in a given calling context and returns
        all the functions it calls (internal, external, and library calls).
        """
        return list_function_callees_impl(request, project_facts)
    
    @mcp.tool()
    def inheritance_hierarchy(request: InheritanceHierarchyRequest) -> InheritanceHierarchyResponse:
        """
        Get the inheritance hierarchy for a contract.
        
        This tool returns both the directly inherited contracts and the full
        inheritance hierarchy (including transitive inheritance).
        """
        return get_inheritance_hierarchy_impl(request, project_facts)
    
    @mcp.tool()
    def list_function_implementations(request: ListFunctionImplementationsRequest) -> ListFunctionImplementationsResponse:
        """
        List all contracts that implement a specific function.
        
        This tool finds all contracts that provide an implementation of a given function
        signature. It's particularly useful for finding implementations of abstract
        functions or interface methods.
        """
        return list_function_implementations_impl(request, project_facts)
    
    # Run the server
    print("Starting Slither MCP server...", file=sys.stderr)
    print(f"Project: {project_path}", file=sys.stderr)
    print(f"Contracts loaded: {len(project_facts.contracts)}", file=sys.stderr)
    print("Tools available:", file=sys.stderr)
    print("  - function_callees", file=sys.stderr)
    print("  - inheritance_hierarchy", file=sys.stderr)
    print("  - list_function_implementations", file=sys.stderr)
    print("  - list_contracts", file=sys.stderr)
    print("  - get_contract", file=sys.stderr)
    print("  - list_functions", file=sys.stderr)
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()

