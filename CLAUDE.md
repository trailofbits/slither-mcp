# Claude Development Guide for Slither MCP Server

This document provides context and guidance for AI assistants working with the Slither MCP Server codebase.

## Project Overview

**Slither MCP Server** is a Model Context Protocol (MCP) server that provides static analysis capabilities for Solidity smart contracts using [Slither](https://github.com/crytic/slither). It exposes Slither's powerful analysis capabilities through standardized MCP tools, making it easy to query contract metadata, inheritance hierarchies, function call relationships, and security vulnerabilities.

### Key Technologies
- **Python 3.11+**: Primary language
- **FastMCP**: MCP server framework (built on top of the MCP SDK)
- **Pydantic**: Type validation and serialization
- **Slither**: Solidity static analysis framework 
- **UV**: Package management and build tool
- **Pytest**: Testing framework

## Core Concepts

### 1. Project Facts
The `ProjectFacts` object (defined in `types.py`) is the central data structure containing all extracted information about a Solidity project:
- `contracts`: Dict mapping `ContractKey` to `ContractModel` (contract metadata)
- `detector_results`: Dict mapping detector name to list of `DetectorResult` findings
- `available_detectors`: List of `DetectorMetadata` for all available Slither detectors
- `project_dir`: String path to the project root directory

This object is generated once from Slither analysis and cached to `artifacts/project_facts.json`.

### 2. Lazy Loading & Caching
- Slither analysis is expensive (can take minutes on large projects)
- The server uses lazy loading: Slither runs only when needed
- Results are cached to `artifacts/project_facts.json` in the target project directory
- Use `--use-cache` flag to load from cache instead of re-analyzing

### 3. Tool Structure
Each MCP tool follows a consistent pattern:
```python
# In slither_mcp/tools/tool_name.py

from slither_mcp.types import JSONStringTolerantModel

class ToolNameRequest(JSONStringTolerantModel):
    """Request parameters with validation"""
    path: str  # All tools require path to Solidity project
    param1: str
    param2: int | None = None

class ToolNameResponse(BaseModel):
    """Response with success flag and optional error"""
    success: bool
    data: SomeType | None = None
    error_message: str | None = None

def tool_name_function(
    request: ToolNameRequest,
    project_facts: ProjectFacts
) -> ToolNameResponse:
    """Implementation that queries ProjectFacts"""
    try:
        # Query logic here
        return ToolNameResponse(success=True, data=result)
    except Exception as e:
        return ToolNameResponse(success=False, error_message=str(e))
```

### 4. Key Types (in `types.py`)

**Base Classes:**
- `JSONStringTolerantModel`: Base model that handles JSON string deserialization for MCP compatibility. Some MCP clients send nested objects as JSON strings; this base class auto-parses them before validation.

**Identifiers:**
- `ContractKey`: Unique identifier for a contract (contract_name + path)
- `FunctionKey`: Unique identifier for a function (function_name + signature + contract_name + path)

**Models:**
- `ContractModel`: Complete contract metadata (functions, inheritance, flags)
- `FunctionModel`: Function metadata (signature, visibility, modifiers, callees)
- `FunctionCallees`: Function call relationships (internal, external, library callees, low-level calls)
- `ProjectFacts`: Top-level data structure containing all contracts and detector results
- `QueryContext`: Context for query operations (searched function, contract, calling context)

**Security/Detection Types:**
- `DetectorMetadata`: Metadata about a Slither detector (name, description, impact, confidence)
- `DetectorResult`: Result from running a detector (detector name, check, impact, confidence, description, locations)
- `SourceLocation`: Location in source code where a finding occurs (file_path, start_line, end_line)

**Inheritance Types (defined in tool files):**
- `InheritanceNode`: Recursive tree node for parent contracts (in `get_inherited_contracts.py`)
- `DerivedNode`: Recursive tree node for child contracts (in `get_derived_contracts.py`)

## Architecture

### Directory Structure
```
slither_mcp/
├── __init__.py              # Package exports
├── server.py                # FastMCP server entry point, tool registration
├── types.py                 # Core type definitions (ContractKey, FunctionModel, etc.)
├── metrics.py               # Metrics configuration and persistence
├── slither_wrapper.py       # Lazy-loading Slither wrapper
├── facts.py                 # ProjectFacts generation from Slither
├── callees.py               # Function callees extraction logic
├── artifacts.py             # Caching/loading artifacts
├── tools/                   # MCP tool implementations
│   ├── __init__.py          # Exports all tools
│   ├── list_contracts.py    # Query: List/filter contracts
│   ├── get_contract.py      # Query: Get contract details
│   ├── get_contract_source.py    # Query: Get contract source code
│   ├── get_function_source.py    # Query: Get function source code
│   ├── list_functions.py    # Query: List/filter functions
│   ├── list_function_callees.py  # Analysis: Function call relationships
│   ├── list_function_callers.py  # Analysis: Function callers
│   ├── get_inherited_contracts.py  # Analysis: Get parent contracts
│   ├── get_derived_contracts.py    # Analysis: Get child contracts
│   ├── list_function_implementations.py  # Analysis: Find implementations
│   ├── list_detectors.py    # Security: List available detectors
│   └── run_detectors.py     # Security: Get detector results
└── client/                  # Client library for programmatic use
    ├── __init__.py          # Client exports
    ├── mcp_client.py        # Typed MCP client wrapper
    └── tool_wrappers.py     # Pydantic-ai agent tool wrappers

tests/
├── conftest.py              # Pytest fixtures (project_facts, etc.)
├── test_*.py                # Test files mirroring tool structure
└── test_detector_integration.py  # Integration tests
```

### Data Flow
1. **Server Start**: `server.py` initializes FastMCP server, registers tools
2. **First Tool Call**: Triggers lazy loading in `slither_wrapper.py`
3. **Slither Analysis**: Runs Slither on target project (or loads from cache)
4. **Facts Generation**: `facts.py` extracts data from Slither into `ProjectFacts`
5. **Tool Execution**: Each tool queries `ProjectFacts` and returns typed response
6. **Caching**: `artifacts.py` saves `ProjectFacts` to JSON for future use

## Development Workflow

### Adding a New Tool

Follow the checklist in `ADDING_TOOLS.md`

### Running Tests
```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_list_contracts.py

# With verbose output
uv run pytest -v

# With coverage
uv run pytest --cov=slither_mcp
```

### Testing Fixtures (in `tests/conftest.py`)
- `project_facts`: Sample ProjectFacts with realistic contracts/functions
- `empty_project_facts`: Empty ProjectFacts for edge case testing
- Use these fixtures in test functions to avoid redundant setup

## Common Patterns

### 1. Error Handling
Always return `success=False` with descriptive `error_message`:
```python
try:
    # Logic here
    return Response(success=True, data=result)
except ValueError as e:
    return Response(success=False, error_message=f"Invalid input: {e}")
except Exception as e:
    return Response(success=False, error_message=str(e))
```

### 2. Filtering Contracts/Functions
Use list comprehensions with conditional logic:
```python
# Filter by type
contracts = [
    c for c in project_facts.contracts.values()
    if filter_type == "all" or 
       (filter_type == "concrete" and not c.is_abstract and not c.is_interface)
]

# Filter by path pattern
if path_pattern:
    contracts = [c for c in contracts if path_pattern in c.contract_key.path]
```

### 3. Accessing Slither Data
The `ProjectFacts` object provides pre-extracted data. Avoid accessing raw Slither objects in tools:
```python
# Good: Use ProjectFacts
contract = project_facts.contracts.get(contract_key)

# Avoid: Don't access Slither directly in tools
# slither_obj = ... (this should only happen in facts.py)
```

### 4. Contract/Function Keys
Always use `ContractKey` and `FunctionKey` for lookups:
```python
from slither_mcp.types import ContractKey

contract_key = ContractKey(contract_name="MyContract", path="src/MyContract.sol")
contract = project_facts.contracts.get(contract_key)
```

### 5. Type Hints
Use strict type hints everywhere:
```python
def my_function(
    param: str,
    optional: int | None = None
) -> MyResponse:
    """Docstring here"""
    ...
```

### 6. Using JSONStringTolerantModel
All request models should inherit from `JSONStringTolerantModel` instead of `BaseModel` to handle MCP client quirks:
```python
from slither_mcp.types import JSONStringTolerantModel

class MyToolRequest(JSONStringTolerantModel):
    """This will auto-parse JSON strings from MCP clients"""
    path: str
    contract_key: ContractKey  # Can be sent as dict or JSON string
```

## Metrics System

### Overview

Slither MCP includes a metrics system to track tool usage and errors. Metrics are **enabled by default** and can be permanently disabled (opt-out).

### Key Components

**`server.py` integration**:
- Checks metrics status on startup
- Initializes Sentry SDK if metrics enabled
- Tracks tool calls, successes, failures, and exceptions
- Blocks `--enhanced-error-reporting` if metrics disabled

## Testing Guidelines

### Test Structure
```python
def test_happy_path(project_facts: ProjectFacts):
    """Test successful operation"""
    request = ToolRequest(param="value")
    response = tool_function(request, project_facts)
    assert response.success
    assert response.data is not None
    # Assert on specific data fields

def test_invalid_input(project_facts: ProjectFacts):
    """Test error handling"""
    request = ToolRequest(param="invalid")
    response = tool_function(request, project_facts)
    assert not response.success
    assert response.error_message is not None
```

### What to Test
- **Happy path**: Valid inputs, expected outputs
- **Edge cases**: Empty strings, None values, missing data
- **Error handling**: Invalid inputs, non-existent contracts/functions
- **Filters**: Test all filter combinations
- **Integration**: Test tool chains (see `test_detector_integration.py`)

## Common Pitfalls

### 1. Don't Forget the Success Flag
Always check and set the `success` boolean in responses.

### 2. Consistent Key Usage
Use `ContractKey` and `FunctionKey` consistently. Don't use raw strings for lookups.

### 3. Cache Invalidation
Remember that cached `project_facts.json` may be stale. When testing, delete cache or use `--use-cache=false`.

### 4. Slither Quirks
- Slither may not detect all functions (e.g., auto-generated getters)
- Some contracts may have circular inheritance
- Internal/external function distinction can be subtle

### 5. Path Handling
- Paths in `ContractKey` are relative to the project root
- Always use forward slashes, even on Windows
- Normalize paths when comparing

## Client Usage

The package includes a typed Python client (`SlitherMCPClient`) for programmatic access:

```python
from slither_mcp.client import SlitherMCPClient

async with SlitherMCPClient() as client:
    await client.connect("/path/to/project", use_cache=True)
    
    # Use typed methods
    response = await client.list_contracts(ListContractsRequest(filter_type="concrete"))
    
    # Helper methods
    contracts = await client.get_all_contracts()
    facts = await client.get_project_facts()
```

**Tool Wrappers**: The `client/tool_wrappers.py` module provides wrappers for integrating Slither MCP tools with pydantic-ai agents. These wrappers expose the same type-safe interfaces as the direct client methods.

See `CLIENT_USAGE.md` for complete examples and API reference.

## Debugging Tips

### 1. Inspect Cached Facts
```bash
# View cached facts
cat artifacts/project_facts.json | jq .

# Pretty-print specific contract
cat artifacts/project_facts.json | jq '.contracts[] | select(.contract_key.contract_name=="MyContract")'
```

### 2. Test Slither Directly
```bash
# Run Slither to see raw output
slither /path/to/project --json -

# Run specific detector
slither /path/to/project --detect reentrancy-eth
```

### 3. Enable Verbose Logging
Add logging to tool implementations for debugging:
```python
import logging
logger = logging.getLogger(__name__)

def my_tool(request, project_facts):
    logger.info(f"Processing request: {request}")
    # ...
```

## Style Guidelines

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase` (e.g., `ContractModel`, `ListContractsRequest`)
- **Functions**: `snake_case` (e.g., `list_contracts_function`)
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

### Docstrings
Follow Google style:
```python
def function_name(param1: str, param2: int) -> ReturnType:
    """Brief one-line summary.
    
    Longer description if needed. Explain what the function does,
    not how it does it.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input
    """
```

### Imports
Order imports as:
1. Standard library
2. Third-party packages (fastmcp, pydantic, slither)
3. Local imports (slither_mcp.types, etc.)

## Important Files Reference

| File | Purpose |
|------|---------|
| `server.py` | Main entry point, tool registration, metrics integration |
| `types.py` | Core type definitions (read this first!) |
| `metrics.py` | Metrics configuration and persistence |
| `facts.py` | Converts Slither objects to ProjectFacts |
| `slither_wrapper.py` | Lazy-loads Slither, handles caching |
| `artifacts.py` | Serialization/deserialization of ProjectFacts |
| `callees.py` | Extracts function call relationships |
| `tools/__init__.py` | Tool exports (facade pattern) |
| `client/mcp_client.py` | Typed client for programmatic use |
| `tests/conftest.py` | Pytest fixtures and test utilities |

## Resources

- **Slither Documentation**: https://github.com/crytic/slither
- **MCP Specification**: https://modelcontextprotocol.io
- **FastMCP**: https://github.com/jlowin/fastmcp
- **Pydantic**: https://docs.pydantic.dev/

## Quick Reference Commands

```bash
# Run server
uv run slither-mcp

# Run tests. You SHOULD run this before considering any coding task completed.
uv run pytest

# Run specific test
uv run pytest tests/test_list_contracts.py -v

# Install dependencies
uv sync

# Install in dev mode
uv pip install -e .
```

## When Working on This Codebase

1. **Read types.py first** - Understand `ProjectFacts`, `ContractKey`, `FunctionKey`
2. **Check existing tools** - Follow established patterns
3. **Use fixtures** - Don't create test data from scratch
4. **Test thoroughly** - Happy path + edge cases + error handling
5. **Update documentation** - Keep README, this file, and docstrings in sync
6. **Run tests before committing** - `uv run pytest`

## Notes for Claude

- This is a **read-heavy** system: All data is extracted once, tools query the cache
- **Performance matters**: Large projects can have 1000+ contracts
- **Type safety is critical**: Use Pydantic models everywhere
- **Error messages should be helpful**: Users may not understand Slither internals
- **Tests are the spec**: When in doubt, check the test files
- **Slither is the source of truth**: If Slither doesn't detect it, we can't report it

This codebase values **clarity over cleverness**. Keep implementations simple and well-documented.

