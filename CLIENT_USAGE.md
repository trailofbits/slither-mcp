# Slither MCP Client Usage Guide

This guide demonstrates how to use the `SlitherMCPClient` to programmatically interact with the Slither MCP server from Python code.

## Overview

The `SlitherMCPClient` provides a typed interface for querying Solidity projects through the Slither MCP server. It handles:
- Connection management via stdio
- Automatic serialization/deserialization of Pydantic models
- Type-safe access to all MCP tools
- Integration with pydantic-ai agents
- Multi-project support with automatic caching

### Architecture

The server supports analyzing multiple projects in a single session. Each tool call requires a `path` parameter specifying the project directory. The server automatically:
1. Loads cached results from `<path>/artifacts/project_facts.json` if available
2. Runs Slither analysis and caches results if no cache exists
3. Keeps analyzed projects in memory for fast subsequent queries

This architecture allows seamless switching between multiple projects without restarting the server.

## Installation

The client is included when you install `slither-mcp`:

```bash
uv pip install slither-mcp
```

## Basic Usage

### Connecting to the Server

```python
from slither_mcp.client import SlitherMCPClient

async with SlitherMCPClient() as client:
    await client.connect()
    # Use the client...
```

The client automatically closes on exit when used as a context manager. All tool methods require a `path` parameter specifying the project directory to analyze.

### Caching Behavior

Projects are automatically cached by the server:
- First analysis of a project runs Slither and saves results to `<path>/artifacts/project_facts.json`
- Subsequent calls with the same path load from cache instantly
- Multiple projects can be analyzed in a single session by passing different paths
- To force re-analysis, delete the `artifacts/` directory in the project

## Querying Contracts

```python
from slither_mcp.tools import ListContractsRequest, GetContractRequest
from slither_mcp.types import ContractKey

PROJECT_PATH = "/path/to/solidity/project"

# List contracts with filters
response = await client.list_contracts(
    ListContractsRequest(
        path=PROJECT_PATH,
        filter_type="concrete"
    )
)

# Get contract details
response = await client.get_contract(
    GetContractRequest(
        path=PROJECT_PATH,
        contract_key=ContractKey(contract_name="MyContract", path="src/MyContract.sol"),
        include_functions=True
    )
)
```

Note: All tool requests now require a `path` parameter specifying the project directory.

## Querying Functions

```python
from slither_mcp.tools import ListFunctionsRequest

# List all functions, or filter by contract, visibility, or modifiers
response = await client.list_functions(
    ListFunctionsRequest(
        path=PROJECT_PATH,
        contract_key=ContractKey(contract_name="MyContract", path="src/MyContract.sol"),
        visibility=["public", "external"],
        has_modifiers=["view"]
    )
)
```

## Analysis Tools

```python
from slither_mcp.tools import (
    FunctionCalleesRequest,
    GetInheritedContractsRequest,
    GetDerivedContractsRequest,
    ListFunctionImplementationsRequest,
)

# Get function call relationships
response = await client.function_callees(
    FunctionCalleesRequest(
        path=PROJECT_PATH,
        function_key=FunctionKey(
            signature="transfer(address,uint256)",
            contract_name="MyContract",
            path="src/MyContract.sol"
        )
    )
)

# Get inheritance hierarchy (parents)
response = await client.get_inherited_contracts(
    GetInheritedContractsRequest(
        path=PROJECT_PATH,
        contract_key=ContractKey(contract_name="MyContract", path="src/MyContract.sol")
    )
)

# Get derived contracts (children)
response = await client.get_derived_contracts(
    GetDerivedContractsRequest(
        path=PROJECT_PATH,
        contract_key=ContractKey(contract_name="BaseContract", path="src/BaseContract.sol")
    )
)

# Find function implementations
response = await client.list_function_implementations(
    ListFunctionImplementationsRequest(
        path=PROJECT_PATH,
        contract_key=ContractKey(contract_name="IERC20", path="src/interfaces/IERC20.sol"),
        function_signature="transfer(address,uint256)"
    )
)
```

## Helper Methods

```python
# Get all contracts with full details for a specific project
contracts = await client.get_all_contracts(PROJECT_PATH)

# Build a complete ProjectFacts object for a specific project
facts = await client.get_project_facts(PROJECT_PATH)
```

These helper methods are convenience wrappers that call the appropriate tools and return the data in a simplified format.

## Integration with Pydantic-AI Agents

The `SlitherMCPClient` includes `create_*_tool()` methods that make MCP tools compatible with pydantic-ai agents.

### Available Tool Creation Methods

**Query Tools:**
- `create_list_contracts_tool()`, `create_get_contract_tool()`, `create_list_functions_tool()`

**Analysis Tools:**
- `create_function_callees_tool()`, `create_get_inherited_contracts_tool()`, `create_get_derived_contracts_tool()`, `create_function_implementations_tool()`

### Basic Agent Setup

```python
from slither_mcp.client import SlitherMCPClient
from pydantic_ai import Agent

client = SlitherMCPClient()
await client.connect()

# Create tools from client methods
tools = [client.create_list_contracts_tool(), client.create_get_contract_tool()]

# Create agent with tools
agent = Agent("openai:gpt-4", tools=tools)

# When using the agent, the tools will need to be provided with a project path
result = await agent.run("What concrete contracts exist in /path/to/project?")
```

**Note:** Tool creation methods still require the `path` parameter in requests. When using with agents, ensure the agent's prompts or system messages include the project path context.

## Complete Example

See test files in `tests/` for complete working examples using the client API.

## Error Handling

All client methods return responses with a `success` boolean field:

```python
response = await client.list_contracts(
    ListContractsRequest(
        path="/path/to/project",
        filter_type="all"
    )
)
if response.success:
    # Process response data
else:
    print(f"Error: {response.error_message}")
```

## API Reference

### SlitherMCPClient

#### Connection Methods
- `connect() -> None` - Connect to MCP server via stdio
- `close() -> None` - Close the connection

#### Query Tools
- `list_contracts(request: ListContractsRequest) -> ListContractsResponse`
- `get_contract(request: GetContractRequest) -> GetContractResponse`
- `list_functions(request: ListFunctionsRequest) -> ListFunctionsResponse`

#### Analysis Tools
- `function_callees(request: FunctionCalleesRequest) -> FunctionCalleesResponse`
- `get_inherited_contracts(request: GetInheritedContractsRequest) -> GetInheritedContractsResponse`
- `get_derived_contracts(request: GetDerivedContractsRequest) -> GetDerivedContractsResponse`
- `list_function_implementations(request: ListFunctionImplementationsRequest) -> ListFunctionImplementationsResponse`

#### Helper Methods
- `get_all_contracts(project_path: str) -> list[ContractModel]` - Get all contracts for a project
- `get_project_facts(project_path: str) -> ProjectFacts` - Get complete project facts for a project

### Tool Creation Methods

Tool creation methods available on `SlitherMCPClient`:

**Query Tool Creators:**
- `create_list_contracts_tool()` - Creates a tool for listing contracts
- `create_get_contract_tool()` - Creates a tool for getting contract details
- `create_list_functions_tool()` - Creates a tool for listing functions

**Analysis Tool Creators:**
- `create_function_callees_tool()` - Creates a tool for finding function callees
- `create_get_inherited_contracts_tool()` - Creates a tool for getting inherited contracts
- `create_get_derived_contracts_tool()` - Creates a tool for getting derived contracts
- `create_function_implementations_tool()` - Creates a tool for finding function implementations

All methods return async functions that can be used with pydantic-ai agents. For creating additional tool creators, see [ADDING_TOOLS.md](ADDING_TOOLS.md#step-5-add-tool-creation-method-to-client-optional).

