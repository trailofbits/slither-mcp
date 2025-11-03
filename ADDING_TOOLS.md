# Adding New Tools to Slither MCP Server

This guide walks you through adding new MCP tools to the Slither MCP server. Follow these steps to ensure consistency with the existing codebase.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Testing](#testing)
5. [Documentation](#documentation)
6. [Examples](#examples)

## Overview

The Slither MCP server uses a modular architecture where each tool is defined in its own module with:
- Request and Response models (using Pydantic)
- Implementation function that takes the request and `ProjectFacts`
- Registration in the server and tool exports

## Architecture

### Directory Structure

```
slither_mcp/
├── tools/
│   ├── __init__.py              # Exports all tools
│   ├── list_contracts.py        # Example tool
│   ├── get_contract.py          # Example tool
│   └── list_function_callees.py # Example tool
├── server.py                     # FastMCP server - registers tools
├── types.py                      # Core type definitions
└── facts.py                      # Project facts generation
```

### Key Files

- **`slither_mcp/tools/your_tool.py`**: Your tool implementation
- **`slither_mcp/tools/__init__.py`**: Export your tool for imports
- **`slither_mcp/server.py`**: Register your tool with FastMCP
- **`tests/test_your_tool.py`**: Test suite for your tool
- **`README.md`**: Document your tool's usage

## Step-by-Step Guide

### Step 1: Create the Tool Module

Create a new file in `slither_mcp/tools/` named after your tool (e.g., `get_function_complexity.py`).

**Structure:**
- Define `YourToolRequest(JSONStringTolerantModel)` with request parameters
- Define `YourToolResponse(BaseModel)` with `success: bool`, data fields, and `error_message: str | None`
- Implement `your_tool_function(request, project_facts) -> YourToolResponse`

See existing tools in `slither_mcp/tools/` for examples.

### Step 2: Export from `tools/__init__.py`

Add imports and exports for your tool's request/response models and function to `slither_mcp/tools/__init__.py`.

### Step 3: Register in `server.py`

Add your tool to `slither_mcp/server.py`:

1. Import your tool's request/response models and implementation function
2. Register with `@mcp.tool()` decorator, calling your implementation with `project_facts`
3. Add tool name to the startup banner

See existing tool registrations in `server.py` for the pattern.

### Step 4: Write Tests

Create `tests/test_your_tool.py` with:
- Happy path tests using the `project_facts` fixture
- Edge case tests (invalid inputs, empty projects, etc.)
- Assertions on `success` flag and `error_message`

See existing test files in `tests/` for patterns and fixtures.

### Step 5: Add Tool Creation Method to Client (Optional)

For pydantic-ai integration, add a `create_your_tool_name_tool()` method to `SlitherMCPClient` in `slither_mcp/client/mcp_client.py`:

1. The method should return an async function that wraps `await self.your_tool_name(request)`
2. Set `__name__` and `__doc__` on the returned function for introspection
3. Follow the pattern of existing `create_*_tool()` methods in the class

See existing tool creation methods in `mcp_client.py` for examples.

### Step 6: Update Main README

Add a brief entry to the "MCP Tools" section in `README.md` describing what your tool does.

## Testing

Run tests with: `uv run pytest tests/test_your_tool.py`

Use fixtures from `tests/conftest.py`:
- `project_facts`: Sample contracts for testing
- `empty_project_facts`: For edge case testing

## Documentation

Follow docstring conventions:
- Module: Brief description
- Models: "Request to..." / "Response containing..."
- Functions: Summary, detailed description, Args, Returns

Use type hints consistently. See existing tools for patterns.

## Examples

See existing tool implementations in `slither_mcp/tools/` for complete examples:
- `list_contracts.py` - Simple query tool with filters
- `get_contract.py` - Detailed information retrieval
- `list_function_callees.py` - Complex analysis tool

## Common Patterns

- **Error Handling**: Return `success=False` with descriptive `error_message`
- **Filtering**: Use list comprehensions
- **Optional Parameters**: Use Pydantic defaults
- **Accessing ProjectFacts**: 
  - `project_facts.contracts` - dict of all contracts
  - `project_facts.functions_to_contract` - function-to-contract mapping

## Checklist

Before submitting your new tool, ensure:

- [ ] Tool module created in `slither_mcp/tools/`
- [ ] Request and Response models defined with Pydantic
- [ ] Tool function implemented with proper type hints
- [ ] Tool exported in `slither_mcp/tools/__init__.py`
- [ ] Tool imported in `slither_mcp/server.py`
- [ ] Tool registered with `@mcp.tool()` decorator
- [ ] Tool added to startup banner in `server.py`
- [ ] Test file created in `tests/`
- [ ] Happy path tests written
- [ ] Edge case tests written
- [ ] Integration tests written (see `tests/test_detector_integration.py`)
- [ ] All tests passing (`uv run pytest`)
- [ ] Client tool creation method added (optional, `create_*_tool()` in `slither_mcp/client/mcp_client.py`)
- [ ] Main README.md updated with tool documentation
- [ ] Docstrings complete and accurate

## Additional Resources

### Key Types

See `slither_mcp/types.py`:
- `ContractKey`, `FunctionKey` - Identifiers
- `ContractModel`, `FunctionModel` - Metadata
- `ProjectFacts` - Root data object

## Getting Help

For reference:
1. Existing tool implementations in `slither_mcp/tools/`
2. Test files for usage examples
3. `slither_mcp/types.py` for data structures
4. [Slither documentation](https://github.com/crytic/slither) for analysis capabilities

