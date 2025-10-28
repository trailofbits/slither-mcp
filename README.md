# Slither MCP Server

A Model Context Protocol (MCP) server that provides static analysis capabilities for Solidity smart contracts using [Slither](https://github.com/crytic/slither).

## Overview

This MCP server wraps Slither static analysis functionality, making it accessible through the Model Context Protocol. It can analyze Solidity projects (Foundry, Hardhat, etc.) and generate comprehensive metadata about contracts, functions, inheritance hierarchies, and more.

## Features

- **Lazy Loading**: Slither analysis is performed only when needed
- **Caching**: Project facts are cached to `artifacts/project_facts.json` for faster subsequent loads
- **MCP Tools**: Query contract and function information through MCP tools
- **Security Analysis**: Run Slither detectors and access results with filtering
- **Comprehensive Analysis**: Extracts detailed information about:
  - Contract metadata (abstract, interface, library flags)
  - Function signatures and modifiers
  - Inheritance hierarchies
  - Function call relationships (internal, external, library calls)
  - Security vulnerabilities and code quality issues
  - Source code locations

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for package management:

```bash
# Install dependencies
uv sync

# Or install in development mode
uv pip install -e .
```

## Usage

### Basic Usage

Analyze a Solidity project (default behavior - always scans):

```bash
uv run slither-mcp /path/to/solidity/project
```

### Using Cache

Load from cached artifacts if available:

```bash
uv run slither-mcp /path/to/solidity/project --use-cache
```

When `--use-cache` is specified and `artifacts/project_facts.json` exists in the target directory, the server will load from cache instead of re-running Slither analysis.

### Command-Line Options

- `path` (required): Path to the Solidity project to analyze
- `--use-cache`: Use cached `project_facts.json` if available (default: always scan)

## MCP Tools

The server exposes 11 MCP tools for querying contract and function information:

### 1. `list_contracts` - List contracts with filters
Filter contracts by type (concrete, abstract, interface, library) or path pattern.

### 2. `get_contract` - Get detailed contract information
Retrieve full contract metadata including functions, inheritance, and flags.

### 3. `get_contract_source` - Get contract source code
Returns the complete source code of the Solidity file containing the specified contract.

### 4. `get_function_source` - Get function source code
Returns the source code for a specific function with line numbers. Useful for focused analysis.

### 5. `list_functions` - List functions with filters
Filter functions by contract, visibility, or modifiers.

### 6. `function_callees` - Get function call relationships
Returns internal, external, and library callees for a function, including low-level call detection.

### 7. `get_inherited_contracts` - Get contract inheritance
Returns a recursive tree of all contracts that a contract inherits from (parents and ancestors).

### 8. `get_derived_contracts` - Get contracts that inherit from this one
Returns a recursive tree of all contracts that inherit from a contract (children and descendants).

### 9. `list_function_implementations` - Find function implementations
Find all implementations of a function signature across contracts.

### 10. `list_detectors` - List available Slither detectors
Returns metadata about Slither detectors including names, descriptions, impact levels, and confidence ratings. Supports filtering by name or description.

### 11. `run_detectors` - Get detector results with filtering
Returns cached detector results. Filter by detector names, impact level (High, Medium, Low, Informational), or confidence level (High, Medium, Low).

All tools return responses with a `success` boolean and either data fields or an `error_message`. See individual tool implementations in `slither_mcp/tools/` for detailed schemas and usage.

## Client Usage

The `slither-mcp` package includes a typed Python client (`SlitherMCPClient`) for programmatically interacting with the Slither MCP server. This is useful for building tools, scripts, or agents that need to query Solidity projects.

The client provides:
- Type-safe methods for all MCP tools
- Automatic serialization/deserialization of Pydantic models
- Helper methods for common patterns
- Tool wrappers for pydantic-ai agent integration

For detailed usage examples and documentation, see [CLIENT_USAGE.md](CLIENT_USAGE.md).

## Architecture

The server is organized into several modules:

### Core Modules
- **`types.py`**: Core type definitions (ContractKey, FunctionModel, ProjectFacts, etc.)
- **`slither_wrapper.py`**: Lazy-loading wrapper for Slither with build utilities
- **`facts.py`**: Project facts generation from Slither analysis
- **`callees.py`**: Function callees extraction
- **`artifacts.py`**: Artifact caching and loading

### Tool Modules (`tools/` directory)
Each tool has its own module with request/response models and implementation:

**Query Tools** (browsing and filtering):
- **`list_contracts.py`**: List contracts with optional filters
- **`get_contract.py`**: Get detailed contract information
- **`list_functions.py`**: List functions with optional filters

**Analysis Tools** (deep analysis):
- **`list_function_callees.py`**: Get function call relationships
- **`get_inherited_contracts.py`**: Get contract inheritance hierarchies (parents)
- **`get_derived_contracts.py`**: Get contracts that inherit from a given contract (children)
- **`list_function_implementations.py`**: Find all implementations of a function

**Detector Tools** (security and quality analysis):
- **`list_detectors.py`**: List available Slither detectors with metadata
- **`run_detectors.py`**: Retrieve cached detector results with filtering

- **`__init__.py`**: Facade that re-exports all tools for convenience

### Server
- **`server.py`**: FastMCP server entry point that registers all tools

### Client Modules (`client/` directory)
Client utilities for programmatic interaction with the MCP server:

- **`mcp_client.py`**: Typed client wrapper (`SlitherMCPClient`) for connecting to and querying the MCP server
- **`tool_wrappers.py`**: Tool wrapper functions for pydantic-ai agent integration
- **`__init__.py`**: Exports client classes and wrappers

## Artifacts

The server generates and caches artifacts in the target project's `artifacts/` directory:

- `artifacts/project_facts.json`: Complete project metadata including all contracts and functions

The artifact format includes type metadata for proper deserialization. See `slither_mcp/artifacts.py` for serialization details.

## Requirements

- Python 3.11+
- Solidity compiler setup (Foundry, Hardhat, or similar)
- Slither and its dependencies

## Development

### Running Tests

```bash
uv run pytest
```

### Project Structure

```
slither-mcp/
├── slither_mcp/
│   ├── __init__.py
│   ├── server.py          # Main MCP server entry point
│   ├── types.py           # Type definitions
│   ├── slither_wrapper.py # Slither lazy loading
│   ├── facts.py           # Facts generation
│   ├── callees.py         # Callees extraction
│   ├── artifacts.py       # Artifact management
│   ├── tools/             # MCP tool implementations
│   │   ├── __init__.py              # Facade re-exporting all tools
│   │   ├── list_contracts.py        # Query tool
│   │   ├── get_contract.py          # Query tool
│   │   ├── list_functions.py        # Query tool
│   │   ├── list_function_callees.py # Analysis tool
│   │   ├── get_inherited_contracts.py  # Analysis tool
│   │   ├── get_derived_contracts.py    # Analysis tool
│   │   └── list_function_implementations.py  # Analysis tool
│   └── client/            # Client utilities
│       ├── __init__.py              # Client exports
│       ├── mcp_client.py            # Typed MCP client
│       └── tool_wrappers.py         # Pydantic-ai tool wrappers
├── tests/
├── pyproject.toml
├── README.md
├── CLIENT_USAGE.md        # Client usage guide
└── ADDING_TOOLS.md        # Tool development guide
```

## Roadmap

Future iterations will add:

- Additional MCP tools for specialized queries
- MCP resources for accessing source code and metadata
- More fact generators for specialized analysis
- Integration with other analysis tools

## License

[Add license information]

## Contributing

[Add contributing guidelines]

