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

**Template:**

```python
"""Tool for [brief description]."""

from typing import Optional
from pydantic import BaseModel

from slither_mcp.types import (
    ContractKey,
    FunctionKey,
    ProjectFacts,
    # Import other types as needed
)


class YourToolRequest(BaseModel):
    """Request to [describe what your tool does]."""
    # Define your request parameters
    contract_key: ContractKey
    some_filter: Optional[str] = None


class YourToolResponse(BaseModel):
    """Response containing [describe response data]."""
    success: bool
    # Define your response fields
    result_data: dict | None = None
    error_message: str | None = None


def your_tool_function(
    request: YourToolRequest,
    project_facts: ProjectFacts
) -> YourToolResponse:
    """
    [Detailed description of what this tool does.]
    
    Args:
        request: The tool request with parameters
        project_facts: The project facts containing contract data
        
    Returns:
        YourToolResponse with results or error
    """
    try:
        # Your implementation logic here
        # Access project_facts.contracts, project_facts.functions_to_contract, etc.
        
        return YourToolResponse(
            success=True,
            result_data={"key": "value"}
        )
    except Exception as e:
        return YourToolResponse(
            success=False,
            error_message=str(e)
        )
```

### Step 2: Export from `tools/__init__.py`

Add your tool to `slither_mcp/tools/__init__.py`:

```python
# Add to imports section (organized by category)
from slither_mcp.tools.your_tool import (
    YourToolRequest,
    YourToolResponse,
    your_tool_function,
)

# Add to __all__ list
__all__ = [
    # ... existing exports ...
    "YourToolRequest",
    "YourToolResponse",
    "your_tool_function",
]
```

### Step 3: Register in `server.py`

Add your tool to `slither_mcp/server.py`:

#### 3a. Import your tool

```python
# Add to the imports section (line ~21-42)
from slither_mcp.tools import (
    # ... existing imports ...
    YourToolRequest,
    YourToolResponse,
    your_tool_function as your_tool_impl,
)
```

#### 3b. Register with FastMCP

Add the tool registration (around line ~147-209):

```python
@mcp.tool()
def your_tool_name(request: YourToolRequest) -> YourToolResponse:
    """
    [Brief description for the MCP interface]
    
    [More detailed description of what this tool does,
    what parameters it accepts, and what it returns.]
    """
    return your_tool_impl(request, project_facts)
```

#### 3c. Add to startup banner

Update the startup message (around line ~214-221):

```python
print("Tools available:", file=sys.stderr)
# ... existing tools ...
print("  - your_tool_name", file=sys.stderr)
```

### Step 4: Write Tests

Create `tests/test_your_tool.py`:

**Template:**

```python
"""Tests for your_tool."""

import pytest
from slither_mcp.tools.your_tool import (
    YourToolRequest,
    your_tool_function,
)
from slither_mcp.types import ContractKey


class TestYourToolHappyPath:
    """Test happy path scenarios for your_tool."""

    def test_basic_functionality(self, project_facts):
        """Test basic tool functionality."""
        request = YourToolRequest(
            contract_key=ContractKey(
                contract_name="BaseContract",
                path="test/BaseContract.sol"
            )
        )
        response = your_tool_function(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        # Add specific assertions for your tool's behavior

    def test_with_filters(self, project_facts):
        """Test tool with various filter parameters."""
        # Test different parameter combinations
        pass


class TestYourToolEdgeCases:
    """Test edge cases for your_tool."""

    def test_empty_project(self, empty_project_facts):
        """Test tool with empty project."""
        request = YourToolRequest(
            contract_key=ContractKey(
                contract_name="NonExistent",
                path="test/NonExistent.sol"
            )
        )
        response = your_tool_function(request, empty_project_facts)

        # Should handle gracefully
        assert response.success is False
        assert response.error_message is not None

    def test_invalid_contract(self, project_facts):
        """Test tool with invalid contract reference."""
        # Test error handling
        pass
```

**Testing Best Practices:**

1. Use the `project_facts` fixture (defined in `tests/conftest.py`)
2. Test both happy paths and edge cases
3. Organize tests into classes by scenario type
4. Use descriptive test names
5. Assert on both `success` flag and `error_message`
6. Test filter combinations thoroughly

### Step 5: Create Client Tool Wrapper (Optional)

If your tool should be available to pydantic-ai agents or other client-side frameworks, create a wrapper function in `slither_mcp/client/tool_wrappers.py`.

**Why Create a Wrapper:**
- Provides a clean function signature for pydantic-ai introspection
- Makes the tool name more natural (e.g., `function_callees` vs `mcp_client.function_callees`)
- Allows the tool to be used directly with agent frameworks

**Template:**

```python
def create_your_tool_wrapper(mcp_client: SlitherMCPClient):
    """
    Create a your_tool wrapper from the MCP client.
    
    Returns a wrapper function that calls mcp_client.your_tool() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def your_tool_name(request: YourToolRequest) -> YourToolResponse:
        """[Brief description of what this tool does]."""
        return await mcp_client.your_tool_name(request)
    
    return your_tool_name
```

**Steps:**

1. Add the wrapper function to `slither_mcp/client/tool_wrappers.py`
2. Import the request/response types at the top of the file
3. Add the function name to the `__all__` list
4. Export from `slither_mcp/client/__init__.py`

**Example:**

Here's how `create_function_callees_tool` is implemented:

```python
def create_function_callees_tool(mcp_client: SlitherMCPClient):
    """
    Create a function callees tool from the MCP client.
    
    Returns a wrapper function that calls mcp_client.function_callees() with
    proper naming for pydantic-ai introspection.
    
    Args:
        mcp_client: Connected SlitherMCPClient instance
        
    Returns:
        A tool function that can be used with pydantic-ai Agent
    """
    async def function_callees(request: FunctionCalleesRequest) -> FunctionCalleesResponse:
        """Get the internal, external, and library callees for a function."""
        return await mcp_client.function_callees(request)
    
    return function_callees
```

**Usage:**

```python
from slither_mcp.client import SlitherMCPClient, create_your_tool_wrapper
from pydantic_ai import Agent

client = SlitherMCPClient()
await client.connect("/path/to/project")

your_tool = create_your_tool_wrapper(client)

agent = Agent("openai:gpt-4", tools=[your_tool])
```

### Step 6: Update Main README

Add documentation to `README.md` in the "MCP Tools" section:

```markdown
### N. `your_tool_name` - Brief description

**Request:**
```json
{
  "contract_key": {"contract_name": "MyContract", "path": "src/MyContract.sol"},
  "some_filter": "optional_value"
}
```

**Response:**
```json
{
  "success": true,
  "result_data": {
    "key": "value"
  }
}
```

**Description:**
Detailed explanation of what this tool does, when to use it, and any important notes.
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests for your specific tool
uv run pytest tests/test_your_tool.py

# Run with verbose output
uv run pytest -v tests/test_your_tool.py

# Run a specific test
uv run pytest tests/test_your_tool.py::TestYourToolHappyPath::test_basic_functionality
```

### Test Fixtures

The test suite provides several useful fixtures (defined in `tests/conftest.py`):

- **`project_facts`**: A `ProjectFacts` object with sample contracts for testing
- **`empty_project_facts`**: An empty `ProjectFacts` for edge case testing

## Documentation

### Docstring Standards

Follow these conventions for consistency:

1. **Module docstrings**: Brief description of the tool's purpose
2. **Request model**: "Request to [action description]"
3. **Response model**: "Response containing [data description]"
4. **Function docstrings**: 
   - One-line summary
   - Detailed description
   - Args section with parameter descriptions
   - Returns section with return value description

### Type Hints

- Always use type hints for function parameters and return values
- Use `Optional[Type]` for optional parameters
- Use `Type | None` for nullable return values (Python 3.10+ syntax)
- Import types from `slither_mcp.types` when available

## Examples

### Example 1: Simple Query Tool

Here's a simplified version of `list_contracts`:

```python
"""Tool for listing contracts with optional filters."""

from typing import Literal, Optional
from pydantic import BaseModel

from slither_mcp.types import ContractKey, ProjectFacts


class ContractInfo(BaseModel):
    """Basic contract information."""
    key: ContractKey
    is_abstract: bool


class ListContractsRequest(BaseModel):
    """Request to list contracts with optional filters."""
    filter_type: Optional[Literal["all", "concrete", "abstract"]] = "all"


class ListContractsResponse(BaseModel):
    """Response containing list of contracts."""
    success: bool
    contracts: list[ContractInfo]
    total_count: int
    error_message: str | None = None


def list_contracts(
    request: ListContractsRequest,
    project_facts: ProjectFacts
) -> ListContractsResponse:
    """
    List all contracts with optional filters.
    
    Args:
        request: The list contracts request with filters
        project_facts: The project facts containing contract data
        
    Returns:
        ListContractsResponse with filtered contract list
    """
    contracts = []
    
    for key, model in project_facts.contracts.items():
        # Apply filters
        if request.filter_type == "concrete" and model.is_abstract:
            continue
        elif request.filter_type == "abstract" and not model.is_abstract:
            continue
        
        contracts.append(ContractInfo(
            key=key,
            is_abstract=model.is_abstract
        ))
    
    return ListContractsResponse(
        success=True,
        contracts=contracts,
        total_count=len(contracts)
    )
```

### Example 2: Analysis Tool

Here's a simplified version of an analysis tool:

```python
"""Tool for analyzing function complexity."""

from pydantic import BaseModel

from slither_mcp.types import FunctionKey, ProjectFacts


class ComplexityRequest(BaseModel):
    """Request to analyze function complexity."""
    function_key: FunctionKey


class ComplexityResponse(BaseModel):
    """Response with complexity metrics."""
    success: bool
    cyclomatic_complexity: int | None = None
    cognitive_complexity: int | None = None
    error_message: str | None = None


def get_function_complexity(
    request: ComplexityRequest,
    project_facts: ProjectFacts
) -> ComplexityResponse:
    """
    Calculate complexity metrics for a function.
    
    Args:
        request: The complexity request
        project_facts: The project facts
        
    Returns:
        ComplexityResponse with metrics or error
    """
    # Find the function in project_facts
    contract_key = request.function_key.contract_key()
    contract = project_facts.contracts.get(contract_key)
    
    if not contract:
        return ComplexityResponse(
            success=False,
            error_message=f"Contract not found: {contract_key}"
        )
    
    # Look up function and calculate metrics
    # ... complexity calculation logic ...
    
    return ComplexityResponse(
        success=True,
        cyclomatic_complexity=5,
        cognitive_complexity=3
    )
```

## Common Patterns

### Pattern 1: Error Handling

Always provide helpful error messages:

```python
if not contract:
    return YourToolResponse(
        success=False,
        error_message=f"Contract not found: {request.contract_key.contract_name}"
    )
```

### Pattern 2: Filtering Data

Use list comprehensions for simple filters:

```python
filtered = [
    item for item in collection
    if meets_criteria(item, request.filter)
]
```

### Pattern 3: Optional Parameters

Use Pydantic defaults for optional parameters:

```python
class YourRequest(BaseModel):
    required_param: str
    optional_param: Optional[str] = None
    optional_with_default: int = 10
```

### Pattern 4: Accessing ProjectFacts

```python
# Access all contracts
for contract_key, contract_model in project_facts.contracts.items():
    # Process contract
    pass

# Look up specific contract
contract = project_facts.contracts.get(contract_key)

# Access function-to-contract mapping
contract_key = project_facts.functions_to_contract.get(function_key)
```

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
- [ ] All tests passing (`uv run pytest`)
- [ ] Client tool wrapper created (optional, in `slither_mcp/client/tool_wrappers.py`)
- [ ] Main README.md updated with tool documentation
- [ ] Docstrings complete and accurate

## Additional Resources

### Key Type Definitions

Familiarize yourself with these core types in `slither_mcp/types.py`:

- **`ContractKey`**: Identifies a contract by name and path
- **`FunctionKey`**: Identifies a function by signature, contract, and path
- **`ContractModel`**: Complete contract metadata
- **`FunctionModel`**: Complete function metadata
- **`ProjectFacts`**: Root object containing all project data

### ProjectFacts Structure

```python
class ProjectFacts(BaseModel):
    contracts: dict[ContractKey, ContractModel]
    functions_to_contract: dict[FunctionKey, ContractKey]
    project_dir: str
```

### Useful Slither Properties

When working with the Slither wrapper, you can access:

- Contract properties: `is_abstract`, `is_interface`, `is_library`, `is_fully_implemented`
- Function properties: `visibility`, `view`, `pure`, `payable`, `virtual`, `is_constructor`
- Relationships: `inheritance`, `functions_declared`, `functions_inherited`

## Getting Help

If you have questions:

1. Look at existing tool implementations for patterns
2. Check the test files for usage examples
3. Review `slither_mcp/types.py` for available data structures
4. Consult the Slither documentation for underlying analysis capabilities

## Tips for Success

1. **Start Simple**: Begin with a basic implementation, then add features
2. **Test Early**: Write tests as you develop, not after
3. **Follow Patterns**: Match the style and structure of existing tools
4. **Document Well**: Clear docstrings help users and maintainers
5. **Handle Errors**: Always provide meaningful error messages
6. **Think About Performance**: Consider caching if your tool is expensive
7. **Validate Inputs**: Use Pydantic validators for complex validation logic

Happy tool building! 🛠️

