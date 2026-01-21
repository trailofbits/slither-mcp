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
from slither_mcp.metrics import (
    disable_metrics_permanently,
    get_metrics_config_path,
    initialize_metrics,
    is_metrics_disabled,
)
from slither_mcp.slither_wrapper import LazySlither
from slither_mcp.tool_registry import TOOL_NAMES, register_all_tools
from slither_mcp.types import (
    CacheCorruptionError,
    ProjectFacts,
    SlitherAnalysisError,
)

# Global cache to hold project facts for multiple projects
project_facts_cache: dict[str, ProjectFacts] = {}


def get_or_load_project_facts(path: str) -> ProjectFacts:
    """
    Get or load ProjectFacts for a given project path.

    This function implements the caching strategy:
    1. Check if already in memory cache
    2. If not, check for artifacts/project_facts.json
    3. If cache exists and valid, load it
    4. Otherwise, run Slither analysis and cache the results

    Args:
        path: Path to the project directory

    Returns:
        ProjectFacts for the project

    Raises:
        ValueError: If path doesn't exist or isn't a directory
        SlitherAnalysisError: If Slither analysis fails
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
        try:
            facts = load_project_facts(str(artifacts_dir))
            logging.info(f"Loaded {len(facts.contracts)} contracts from cache")
            project_facts_cache[abs_path] = facts
            return facts
        except FileNotFoundError:
            logging.warning("Cache file not found, will re-scan project")
        except CacheCorruptionError as e:
            logging.warning(f"Cache validation failed: {e}. Will re-scan project")

    # Run Slither analysis with error handling
    logging.info(f"Analyzing project at: {abs_path}")

    try:
        lazy_slither = LazySlither(abs_path)

        # Generate project facts
        logging.info("Generating project facts...")
        facts = get_project_facts(abs_path, lazy_slither)
        logging.info(f"Generated facts for {len(facts.contracts)} contracts")
    except FileNotFoundError as e:
        raise SlitherAnalysisError(
            f"Missing dependency for project compilation: {e}. "
            f"Ensure foundry (forge) or npm dependencies are installed."
        ) from e
    except MemoryError as e:
        raise SlitherAnalysisError(
            f"Insufficient memory to analyze project: {e}. "
            f"The project may be too large. Try analyzing a subset of contracts."
        ) from e
    except PermissionError as e:
        raise SlitherAnalysisError(
            f"Permission denied during analysis: {e}. "
            f"Check file permissions for the project directory."
        ) from e
    except Exception as e:
        # Check for common compilation errors
        error_str = str(e).lower()
        if "compilation" in error_str or "solc" in error_str:
            raise SlitherAnalysisError(
                f"Solidity compilation failed: {e}. "
                f"Ensure the project compiles successfully with 'forge build' or 'npx hardhat compile'."
            ) from e
        elif "slither" in error_str:
            raise SlitherAnalysisError(f"Slither analysis failed: {e}") from e
        else:
            raise SlitherAnalysisError(f"Unexpected error during analysis: {e}") from e

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
        help="Enable Sentry error reporting for comprehensive exception monitoring",
    )
    parser.add_argument(
        "--disable-metrics",
        action="store_true",
        help="Permanently disable metrics and error reporting",
    )
    args = parser.parse_args()

    # Check persisted metrics preference
    metrics_disabled = is_metrics_disabled()

    # Handle --disable-metrics flag
    if args.disable_metrics:
        disable_metrics_permanently()
        metrics_disabled = True
        print(
            f"Metrics disabled permanently (created {get_metrics_config_path()})", file=sys.stderr
        )

    # Check if metrics are disabled
    if metrics_disabled:
        if args.enhanced_error_reporting:
            print(
                "ERROR: Cannot use --enhanced-error-reporting when metrics are disabled.",
                file=sys.stderr,
            )
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
    stderr_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s", datefmt="%m/%d/%y %H:%M:%S")
    )
    logging.root.addHandler(stderr_handler)
    logging.root.setLevel(logging.WARNING)

    # Create FastMCP server
    mcp = FastMCP("slither-mcp")

    # Register all tools
    register_all_tools(mcp, get_or_load_project_facts)

    # Register usage guide prompt
    @mcp.prompt("slither_guide")
    def slither_guide() -> str:
        """Get guidance on using Slither MCP tools effectively."""
        return """# Slither MCP Tool Guide

## Tool Categories

### Discovery (Start Here)
- list_contracts - List all contracts (filter by type: concrete/interface/library/abstract)
- search_contracts - Find contracts by name pattern (regex)
- search_functions - Find functions by name/signature pattern (regex)

### Details
- get_contract - Full contract metadata (inheritance, functions, flags)
- get_contract_source - Read source file (with optional line limits)
- get_function_source - Read specific function source code

### Analysis
- list_functions - List functions with visibility/modifier filters
- function_callees - What does this function call? (outgoing call graph)
- function_callers - What calls this function? (incoming call graph)
- get_inherited_contracts - Parent contracts (upward inheritance tree)
- get_derived_contracts - Child contracts (downward inheritance tree)
- list_function_implementations - Find concrete implementations of interface/abstract functions

### Security
- list_detectors - Available Slither security checks
- run_detectors - Get findings (filter by impact: High/Medium/Low/Informational)

## Parameter Formats

ContractKey: {"contract_name": "ERC20", "path": "src/ERC20.sol"}
FunctionKey: {"signature": "transfer(address,uint256)", "contract_name": "ERC20", "path": "src/ERC20.sol"}

## Recommended Workflows

### Exploring a New Project
1. list_contracts with filter_type="concrete" to see main contracts
2. get_contract for interesting contracts
3. list_functions to explore contract functions
4. get_function_source to read implementations

### Security Audit
1. run_detectors with impact_filter=["High", "Medium"] for critical findings
2. get_function_source to review flagged code
3. function_callees to trace vulnerable call paths

### Understanding Inheritance
1. search_contracts to find the base contract/interface
2. get_inherited_contracts to see what it inherits from
3. get_derived_contracts to find implementations
4. list_function_implementations for specific function implementations

## Tips
- Use pagination (limit/offset) for large projects
- Use include_functions=false in get_contract for metadata only
- Filter run_detectors by impact=["High","Medium"] for critical findings first
- Use max_depth in tree tools to limit response size
- Check 'truncated' flag in tree responses to know if results were limited
"""

    # Start the server
    print("Starting Slither MCP server...", file=sys.stderr)
    print("All tools accept a 'path' parameter for project directory", file=sys.stderr)
    print("Projects are cached automatically in <path>/artifacts/", file=sys.stderr)

    print("\nAvailable tools:", file=sys.stderr)
    for tool_name in TOOL_NAMES:
        print(f"  - {tool_name}", file=sys.stderr)

    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
