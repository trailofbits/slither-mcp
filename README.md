# Slither MCP Server

[![Tests](https://github.com/trailofbits/slither-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/trailofbits/slither-mcp/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
<!-- [![PyPI version](https://badge.fury.io/py/slither-mcp.svg)](https://badge.fury.io/py/slither-mcp) -->

A Model Context Protocol (MCP) server that provides static analysis capabilities for Solidity smart contracts using [Slither](https://github.com/crytic/slither).

## Overview

This MCP server wraps Slither static analysis functionality, making it accessible through the Model Context Protocol. It can analyze Solidity projects (Foundry, Hardhat, etc.) and generate comprehensive metadata about contracts, functions, inheritance hierarchies, and more.

You can also use Slither MCP as an easy-to-use Slither API for other use cases.

## Features

- **Caching**: Slither runs are cached to `{$PROJECT_PATH}/artifacts/project_facts.json` for faster subsequent loads
- **MCP Tools**: Query contract and function information through MCP tools
- **Security Analysis**: Run Slither detectors and access results with filtering
- **Comprehensive Analysis**: Extracts detailed information about:
  - Contract metadata (abstract, interface, library flags)
  - Function signatures and modifiers
  - Inheritance hierarchies
  - Function call relationships (internal, external, library calls)
  - Security vulnerabilities and code quality issues
  - Source code locations

While this is a v1.0 release, we anticipate API changes as we receive more feedback.

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

Start the Slither MCP server:

```bash
uv run slither-mcp
```

All tools accept a `path` parameter that specifies which Solidity project to analyze. Projects are automatically cached in `<path>/artifacts/project_facts.json` for faster subsequent queries.



### Use in Claude Code

```bash
claude mcp add --transport stdio --scope user slither -- uvx --from git+https://github.com/trailofbits/slither-mcp slither-mcp
```

### Use in Cursor

Make sure uvx is on your Cursor path using `sudo ln -s ~/.local/bin/uvx /usr/local/bin/uvx`

In your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "slither-mcp": {
      "command": "uvx --from git+https://github.com/trailofbits/slither-mcp slither-mcp",
    }
  }
}
```

## Metrics and Privacy

Slither MCP includes opt-out metrics to help improve reliability by letting us know how often LLMs use each tool and their successful call rate. Metrics are **enabled by default** but can be permanently disabled.

### What We Collect

- Tool call events (which tools are used)
- Success/failure status

**We do not collect**: tool call parameters, contract details, function names, or any project-specific information.

### Disabling Metrics

To permanently opt out:

```bash
uv run slither-mcp --disable-metrics
```

**For complete details**, see [METRICS.md](METRICS.md).

## MCP Tools

The server exposes tools for querying contract and function information. **All tools accept a `path` parameter** that specifies the Solidity project directory to analyze.

### Query Tools

### 1. `list_contracts` - List contracts with filters
Requires: `path` (project directory)
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

### 7. `function_callers` - Get functions that call a target function
Returns all functions that call the specified target function, grouped by call type (internal, external, library). This is the inverse of `function_callees`.

### 8. `get_inherited_contracts` - Get contract inheritance
Returns a recursive tree of all contracts that a contract inherits from (parents and ancestors).

### 9. `get_derived_contracts` - Get contracts that inherit from this one
Returns a recursive tree of all contracts that inherit from a contract (children and descendants).

### 10. `list_function_implementations` - Find function implementations
Find all implementations of a function signature across contracts.

### 11. `list_detectors` - List available Slither detectors
Returns metadata about Slither detectors including names, descriptions, impact levels, and confidence ratings. Supports filtering by name or description.

### 12. `run_detectors` - Get detector results with filtering
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


## Requirements

- Python 3.11+
- Solidity compiler setup (Foundry, Hardhat, or similar)
- Slither and its dependencies

## Development

### Running Tests

```bash
uv run pytest
```