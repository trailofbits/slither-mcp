# Slither MCP Server

A Model Context Protocol (MCP) server that provides static analysis capabilities for Solidity smart contracts using [Slither](https://github.com/crytic/slither).

## Overview

This MCP server wraps Slither static analysis functionality, making it accessible through the Model Context Protocol. It can analyze Solidity projects (Foundry, Hardhat, etc.) and generate comprehensive metadata about contracts, functions, inheritance hierarchies, and more.

## Features

- **Lazy Loading**: Slither analysis is performed only when needed
- **Caching**: Project facts are cached to `artifacts/project_facts.json` for faster subsequent loads
- **MCP Tools**: Query contract and function information through MCP tools
- **Comprehensive Analysis**: Extracts detailed information about:
  - Contract metadata (abstract, interface, library flags)
  - Function signatures and modifiers
  - Inheritance hierarchies
  - Function call relationships (internal, external, library calls)
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

The server exposes 7 MCP tools for querying contract and function information:

### 1. `list_contracts` - List contracts with filters

**Request:**
```json
{
  "filter_type": "concrete",  // "all" | "concrete" | "interface" | "library" | "abstract"
  "path_pattern": "src/*.sol"  // Optional glob pattern
}
```

### 2. `get_contract` - Get detailed contract information

**Request:**
```json
{
  "contract_key": {"contract_name": "MyContract", "path": "src/MyContract.sol"},
  "include_functions": true
}
```

### 3. `list_functions` - List functions with filters

**Request:**
```json
{
  "contract_key": null,  // Optional: specific contract or null for all
  "visibility": ["public", "external"],  // Optional filter
  "has_modifiers": ["view"]  // Optional filter
}
```

### 4. `function_callees` - Get function call relationships

**Request:**
```json
{
  "ext_function_signature": "ContractName.functionName(uint256,address)",
  "calling_context": {
    "contract_name": "CallerContract",
    "path": "src/CallerContract.sol"
  }
}
```

**Response:**
```json
{
  "success": true,
  "query_context": {
    "searched_calling_context": "CallerContract@src!CallerContract.sol",
    "searched_function": "ContractName.functionName(uint256,address)",
    "searched_contract": "ContractName"
  },
  "callees": {
    "internal_callees": ["ContractName.internalFunc()"],
    "external_callees": ["OtherContract.externalFunc(uint256)"],
    "library_callees": ["LibraryName.libraryFunc(bytes)"],
    "has_low_level_calls": false
  }
}
```

### 5. `inheritance_hierarchy` - Get contract inheritance

**Request:**
```json
{
  "contract_key": {"contract_name": "MyContract", "path": "src/MyContract.sol"}
}
```

All tools return responses with a `success` boolean and either data fields or an `error_message`. See the tool docstrings for complete response schemas.

## Architecture

The server is organized into several modules:

### Core Modules
- **`types.py`**: Core type definitions (ContractKey, FunctionModel, ProjectFacts, etc.)
- **`slither_wrapper.py`**: Lazy-loading wrapper for Slither with build utilities
- **`facts.py`**: Project facts generation from Slither analysis
- **`callees.py`**: Function callees extraction
- **`artifacts.py`**: Artifact caching and loading

### Tool Modules
- **`query_tools.py`**: Query tools for browsing and filtering data (list_contracts, get_contract, list_functions)
- **`analysis_tools.py`**: Analysis tools for deep analysis (function_callees, inheritance_hierarchy)
- **`tools.py`**: Facade that re-exports all tools for convenience

### Server
- **`server.py`**: FastMCP server entry point that registers all tools

## Artifacts

The server generates and caches artifacts in the target project's `artifacts/` directory:

- `artifacts/project_facts.json`: Complete project metadata including all contracts and functions

The artifact format includes type metadata for proper deserialization:

```json
{
  "_pydantic_type": {
    "is_list": false,
    "model_name": "ProjectFacts"
  },
  "data": {
    "contracts": { ... },
    "project_dir": "/path/to/project"
  }
}
```

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
│   ├── query_tools.py     # Query tools (data browsing/filtering)
│   ├── analysis_tools.py  # Analysis tools (deep analysis)
│   └── tools.py           # Facade re-exporting all tools
├── pyproject.toml
└── README.md
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

