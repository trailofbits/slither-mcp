# Migration Guide: SlitherMCPClient Initialization Changes

## Overview

The `SlitherMCPClient` has been updated to simplify usage by requiring a project path at initialization and automatically pre-populating the `path` parameter in all tool calls. Additionally, tool wrapper creation methods have been moved directly into the client class.

## Breaking Changes

### 1. Client Initialization

**Before:**
```python
from slither_mcp.client import SlitherMCPClient

client = SlitherMCPClient()
await client.connect(project_path="/path/to/project")
```

**After:**
```python
from slither_mcp.client import SlitherMCPClient

client = SlitherMCPClient("/path/to/project")
await client.connect()
```

**Change:** The `project_path` is now a **required** parameter in `__init__()` and has been removed from `connect()`.

### 2. Path Auto-Population

**Before:**
```python
# You had to provide path in every request
request = ListContractsRequest(path="/path/to/project", filter_type="all")
response = await client.list_contracts(request)
```

**After:**
```python
# Path is automatically populated from client's stored path
# You can still include path in the request, but it will be overwritten
request = ListContractsRequest(path="", filter_type="all")  # path can be empty
response = await client.list_contracts(request)
```

**Change:** The client automatically sets `request.path = self._project_path` before making any tool call. The path you provide in the request is **ignored** and replaced with the client's stored path.

### 3. Helper Methods

**Before:**
```python
# Helper methods accepted optional path parameter
contracts = await client.get_all_contracts(path="/path/to/project")
facts = await client.get_project_facts(path="/path/to/project")
```

**After:**
```python
# Helper methods no longer accept path parameter
contracts = await client.get_all_contracts()
facts = await client.get_project_facts()
```

**Change:** `get_all_contracts()` and `get_project_facts()` no longer accept a `path` parameter. They always use the client's stored path.

### 4. Tool Wrappers for pydantic-ai

**Before:**
```python
from slither_mcp.client import SlitherMCPClient
from slither_mcp.client.tool_wrappers import create_list_contracts_tool

client = SlitherMCPClient()
await client.connect(project_path="/path/to/project")

# Create tool using standalone function
tool = create_list_contracts_tool(client)
```

**After:**
```python
from slither_mcp.client import SlitherMCPClient

client = SlitherMCPClient("/path/to/project")
await client.connect()

# Create tool using client method
tool = client.create_list_contracts_tool()
```

**Change:** Tool creation methods are now instance methods on `SlitherMCPClient`. The old `tool_wrappers` module functions are deprecated but still work with deprecation warnings for backward compatibility.

## Migration Steps

### Step 1: Update Client Initialization

Find all instances where you create a `SlitherMCPClient`:

```python
# OLD
client = SlitherMCPClient()
await client.connect(project_path="/path/to/project")

# NEW
client = SlitherMCPClient("/path/to/project")
await client.connect()
```

### Step 2: Simplify Request Creation

Update your request creation to not worry about the path:

```python
# OLD - had to pass path every time
request = ListContractsRequest(path=project_path, filter_type="concrete")
request = GetContractRequest(path=project_path, contract_key=key)

# NEW - path is auto-populated, can pass empty string or any value
request = ListContractsRequest(path="", filter_type="concrete")
request = GetContractRequest(path="", contract_key=key)
# Or even simpler, the path will be overwritten anyway:
request = ListContractsRequest(path=client._project_path, filter_type="concrete")
```

### Step 3: Update Helper Method Calls

Remove `path` parameters from helper method calls:

```python
# OLD
contracts = await client.get_all_contracts(path=project_path)
facts = await client.get_project_facts(path=project_path)

# NEW
contracts = await client.get_all_contracts()
facts = await client.get_project_facts()
```

### Step 4: Update Tool Wrapper Creation (if using pydantic-ai)

If you're using tool wrappers for pydantic-ai agents:

```python
# OLD
from slither_mcp.client.tool_wrappers import (
    create_list_contracts_tool,
    create_get_contract_tool,
    # ... other imports
)

client = SlitherMCPClient()
await client.connect(project_path="/path/to/project")

list_contracts_tool = create_list_contracts_tool(client)
get_contract_tool = create_get_contract_tool(client)

# NEW
client = SlitherMCPClient("/path/to/project")
await client.connect()

list_contracts_tool = client.create_list_contracts_tool()
get_contract_tool = client.create_get_contract_tool()
```

## Available Tool Creation Methods

All the following methods are now available on `SlitherMCPClient`:

- `create_list_contracts_tool()`
- `create_get_contract_tool()`
- `create_get_contract_source_tool()`
- `create_get_function_source_tool()`
- `create_list_functions_tool()`
- `create_function_callees_tool()`
- `create_function_callers_tool()`
- `create_get_inherited_contracts_tool()`
- `create_get_derived_contracts_tool()`
- `create_function_implementations_tool()`

Each returns a closure that automatically pre-populates the path parameter.

## Complete Example

### Before (Old Pattern)

```python
from slither_mcp.client import SlitherMCPClient
from slither_mcp.client.tool_wrappers import create_list_contracts_tool
from slither_mcp.tools import ListContractsRequest

async def analyze_project():
    # Initialize without path
    client = SlitherMCPClient()
    
    # Connect with path
    await client.connect(project_path="/path/to/solidity/project")
    
    # Create request with path
    request = ListContractsRequest(
        path="/path/to/solidity/project",
        filter_type="concrete"
    )
    
    # Call tool
    response = await client.list_contracts(request)
    
    # Get all contracts with path
    contracts = await client.get_all_contracts(path="/path/to/solidity/project")
    
    # Create tool wrapper
    tool = create_list_contracts_tool(client)
    
    await client.close()
```

### After (New Pattern)

```python
from slither_mcp.client import SlitherMCPClient
from slither_mcp.tools import ListContractsRequest

async def analyze_project():
    # Initialize with path
    client = SlitherMCPClient("/path/to/solidity/project")
    
    # Connect (no path needed)
    await client.connect()
    
    # Create request (path auto-populated)
    request = ListContractsRequest(path="", filter_type="concrete")
    
    # Call tool (path automatically set)
    response = await client.list_contracts(request)
    
    # Get all contracts (uses stored path)
    contracts = await client.get_all_contracts()
    
    # Create tool wrapper (built-in method)
    tool = client.create_list_contracts_tool()
    
    await client.close()
```

## Backward Compatibility

The old `tool_wrappers` module functions still work but emit `DeprecationWarning`. You can continue using them temporarily, but they will be removed in a future version.

```python
# Still works but deprecated
from slither_mcp.client.tool_wrappers import create_list_contracts_tool

client = SlitherMCPClient("/path/to/project")
await client.connect()

tool = create_list_contracts_tool(client)  # DeprecationWarning
```

## Benefits of the New Pattern

1. **Less Repetition**: No need to pass the project path repeatedly
2. **Cleaner Code**: Fewer parameters to track and manage
3. **Type Safety**: Path is validated once at initialization
4. **Consistency**: All tools automatically use the same project path
5. **Simpler API**: Tool creation methods are discoverable on the client object

## Questions?

If you encounter issues during migration or have questions, please refer to:
- `CLIENT_USAGE.md` - Complete client usage documentation
- `tests/test_mcp_client.py` - Updated test examples

