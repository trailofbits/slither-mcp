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

The server exposes 8 MCP tools for querying contract and function information:

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

### 3. `get_contract_source` - Get contract source code

**Request:**
```json
{
  "contract_key": {"contract_name": "MyContract", "path": "src/MyContract.sol"}
}
```

**Response:**
```json
{
  "success": true,
  "source_code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract MyContract {\n  // contract code\n}",
  "file_path": "src/MyContract.sol"
}
```

**Description:**
Returns the complete source code of the Solidity file containing the specified contract. This is useful for retrieving the full implementation, including all contracts, imports, and comments in the file.

### 4. `get_function_source` - Get function source code

**Request:**
```json
{
  "function_key": {
    "signature": "transfer(address,uint256)",
    "contract_name": "MyContract",
    "path": "src/MyContract.sol"
  }
}
```

**Response:**
```json
{
  "success": true,
  "source_code": "    function transfer(address to, uint256 amount) public returns (bool) {\n        require(to != address(0), \"Invalid address\");\n        balances[msg.sender] -= amount;\n        balances[to] += amount;\n        return true;\n    }\n",
  "file_path": "src/MyContract.sol",
  "line_start": 42,
  "line_end": 47
}
```

**Description:**
Returns the source code for a specific function identified by its FunctionKey. Unlike `get_contract_source` which returns the entire file, this tool returns only the function's implementation along with the line numbers where it's defined. This is useful for focused analysis of individual functions without needing to parse the entire file.

### 5. `list_functions` - List functions with filters

**Request:**
```json
{
  "contract_key": null,  // Optional: specific contract or null for all
  "visibility": ["public", "external"],  // Optional filter
  "has_modifiers": ["view"]  // Optional filter
}
```

### 6. `function_callees` - Get function call relationships

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

### 7. `get_inherited_contracts` - Get contract inheritance

**Request:**
```json
{
  "contract_key": {"contract_name": "MyContract", "path": "src/MyContract.sol"}
}
```

**Response:**
```json
{
  "success": true,
  "contract_key": {"contract_name": "MyContract", "path": "src/MyContract.sol"},
  "full_inheritance": {
    "contract_key": {"contract_name": "MyContract", "path": "src/MyContract.sol"},
    "inherits": [
      {
        "contract_key": {"contract_name": "BaseContract", "path": "src/BaseContract.sol"},
        "inherits": []
      }
    ]
  }
}
```

Returns a recursive tree showing all contracts that the specified contract inherits from (its parents and ancestors).

### 8. `get_derived_contracts` - Get contracts that inherit from this one

**Request:**
```json
{
  "contract_key": {"contract_name": "BaseContract", "path": "src/BaseContract.sol"}
}
```

**Response:**
```json
{
  "success": true,
  "contract_key": {"contract_name": "BaseContract", "path": "src/BaseContract.sol"},
  "full_derived": {
    "contract_key": {"contract_name": "BaseContract", "path": "src/BaseContract.sol"},
    "derived_by": [
      {
        "contract_key": {"contract_name": "DerivedContract", "path": "src/DerivedContract.sol"},
        "derived_by": []
      }
    ]
  }
}
```

Returns a recursive tree showing all contracts that inherit from the specified contract (its children and descendants). This is the inverse of `get_inherited_contracts`.

### 9. `list_function_implementations` - Find function implementations

**Request:**
```json
{
  "function_signature": "myFunction(uint256,address)"
}
```

All tools return responses with a `success` boolean and either data fields or an `error_message`. See the tool docstrings for complete response schemas.

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

