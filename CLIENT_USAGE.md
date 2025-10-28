# Slither MCP Client Usage Guide

This guide demonstrates how to use the `SlitherMCPClient` to programmatically interact with the Slither MCP server from Python code.

## Overview

The `SlitherMCPClient` provides a typed interface for querying Solidity projects through the Slither MCP server. It handles:
- Connection management via stdio
- Automatic serialization/deserialization of Pydantic models
- Type-safe access to all MCP tools
- Integration with pydantic-ai agents

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
    await client.connect("/path/to/solidity/project", use_cache=True)
    # Use the client...
```

The client automatically closes on exit when used as a context manager.

## Querying Contracts

```python
from slither_mcp.tools import ListContractsRequest, GetContractRequest
from slither_mcp.types import ContractKey

# List contracts with filters
response = await client.list_contracts(
    ListContractsRequest(filter_type="concrete", path_pattern="src/*.sol")
)

# Get contract details
response = await client.get_contract(
    GetContractRequest(
        contract_key=ContractKey(contract_name="MyContract", path="src/MyContract.sol"),
        include_functions=True
    )
)
```

## Querying Functions

```python
from slither_mcp.tools import ListFunctionsRequest

# List all functions, or filter by contract, visibility, or modifiers
response = await client.list_functions(
    ListFunctionsRequest(
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
        ext_function_signature="MyContract.transfer(address,uint256)",
        calling_context=ContractKey(contract_name="MyContract", path="src/MyContract.sol")
    )
)

# Get inheritance hierarchy (parents)
response = await client.get_inherited_contracts(
    GetInheritedContractsRequest(
        contract_key=ContractKey(contract_name="MyContract", path="src/MyContract.sol")
    )
)

# Get derived contracts (children)
response = await client.get_derived_contracts(
    GetDerivedContractsRequest(
        contract_key=ContractKey(contract_name="BaseContract", path="src/BaseContract.sol")
    )
)

# Find function implementations
response = await client.list_function_implementations(
    ListFunctionImplementationsRequest(
        contract_key=ContractKey(contract_name="IERC20", path="src/interfaces/IERC20.sol"),
        function_signature="transfer(address,uint256)"
    )
)
```

## Helper Methods

```python
# Get all contracts with full details
contracts = await client.get_all_contracts()

# Build a complete ProjectFacts object
facts = await client.get_project_facts()
```

## Integration with Pydantic-AI Agents

The client includes tool wrappers that make MCP tools compatible with pydantic-ai agents.

### Available Tool Wrappers

**Query Tools:**
- `create_list_contracts_tool()`, `create_get_contract_tool()`, `create_list_functions_tool()`

**Analysis Tools:**
- `create_function_callees_tool()`, `create_get_inherited_contracts_tool()`, `create_get_derived_contracts_tool()`, `create_function_implementations_tool()`

### Basic Agent Setup

```python
from slither_mcp.client import SlitherMCPClient, create_list_contracts_tool, create_get_contract_tool
from pydantic_ai import Agent

client = SlitherMCPClient()
await client.connect("/path/to/project", use_cache=True)

# Create tool wrappers
tools = [create_list_contracts_tool(client), create_get_contract_tool(client)]

# Create agent with tools
agent = Agent("openai:gpt-4", tools=tools)
result = await agent.run("What concrete contracts exist in this project?")
```

## Complete Example

See test files in `tests/` for complete working examples using the client API.

## Error Handling

All client methods return responses with a `success` boolean field:

```python
response = await client.list_contracts(ListContractsRequest(filter_type="all"))
if response.success:
    # Process response data
else:
    print(f"Error: {response.error_message}")
```

## API Reference

### SlitherMCPClient

#### Connection Methods
- `connect(project_path: str, use_cache: bool = True) -> None` - Connect to MCP server
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
- `get_all_contracts() -> list[ContractModel]`
- `get_project_facts() -> ProjectFacts`

### Tool Wrappers

Available wrapper functions in `slither_mcp.client`:

**Query Tool Wrappers:**
- `create_list_contracts_tool(mcp_client: SlitherMCPClient)`
- `create_get_contract_tool(mcp_client: SlitherMCPClient)`
- `create_list_functions_tool(mcp_client: SlitherMCPClient)`

**Analysis Tool Wrappers:**
- `create_function_callees_tool(mcp_client: SlitherMCPClient)`
- `create_get_inherited_contracts_tool(mcp_client: SlitherMCPClient)`
- `create_get_derived_contracts_tool(mcp_client: SlitherMCPClient)`
- `create_function_implementations_tool(mcp_client: SlitherMCPClient)`

All wrappers return async functions that can be used with pydantic-ai agents. For creating additional custom wrappers, see [ADDING_TOOLS.md](ADDING_TOOLS.md#step-5-create-client-tool-wrapper-optional).

