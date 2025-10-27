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
import asyncio
from slither_mcp.client import SlitherMCPClient

async def main():
    # Create client
    client = SlitherMCPClient()
    
    # Connect to a project
    await client.connect("/path/to/solidity/project", use_cache=True)
    
    # Use the client...
    
    # Close when done
    await client.close()

asyncio.run(main())
```

### Using as a Context Manager

The recommended way to use the client is with an async context manager:

```python
async def main():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/solidity/project", use_cache=True)
        
        # Use the client...
        # Automatically closes on exit

asyncio.run(main())
```

## Querying Contracts

### List All Contracts

```python
from slither_mcp.client import SlitherMCPClient
from slither_mcp.tools import ListContractsRequest

async def list_all_contracts():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        # List all contracts
        response = await client.list_contracts(
            ListContractsRequest(filter_type="all")
        )
        
        if response.success:
            print(f"Found {response.total_count} contracts:")
            for contract_info in response.contracts:
                print(f"  - {contract_info.key.contract_name}")
                print(f"    Abstract: {contract_info.is_abstract}")
                print(f"    Interface: {contract_info.is_interface}")
```

### Filter Contracts

```python
from slither_mcp.tools import ListContractsRequest

async def filter_contracts():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        # Get only concrete contracts
        response = await client.list_contracts(
            ListContractsRequest(filter_type="concrete")
        )
        
        # Or filter by path pattern
        response = await client.list_contracts(
            ListContractsRequest(
                filter_type="all",
                path_pattern="src/*.sol"
            )
        )
```

### Get Contract Details

```python
from slither_mcp.tools import GetContractRequest
from slither_mcp.types import ContractKey

async def get_contract_details():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        # Get detailed contract information
        response = await client.get_contract(
            GetContractRequest(
                contract_key=ContractKey(
                    contract_name="MyContract",
                    path="src/MyContract.sol"
                ),
                include_functions=True
            )
        )
        
        if response.success and response.contract:
            contract = response.contract
            print(f"Contract: {contract.contract_name}")
            print(f"Abstract: {contract.is_abstract}")
            print(f"Interface: {contract.is_interface}")
            print(f"Declared Functions: {len(contract.functions_declared)}")
            print(f"Inherited Functions: {len(contract.functions_inherited)}")
            
            # Iterate through functions
            for func in contract.functions_declared:
                print(f"  - {func.signature}")
```

## Querying Functions

### List Functions

```python
from slither_mcp.tools import ListFunctionsRequest

async def list_functions():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        # List all functions
        response = await client.list_functions(
            ListFunctionsRequest()
        )
        
        # Filter by contract
        response = await client.list_functions(
            ListFunctionsRequest(
                contract_key=ContractKey(
                    contract_name="MyContract",
                    path="src/MyContract.sol"
                )
            )
        )
        
        # Filter by visibility
        response = await client.list_functions(
            ListFunctionsRequest(
                visibility=["public", "external"]
            )
        )
        
        # Filter by modifiers
        response = await client.list_functions(
            ListFunctionsRequest(
                has_modifiers=["view", "pure"]
            )
        )
        
        if response.success:
            for func_info in response.functions:
                print(f"{func_info.signature} - {func_info.visibility}")
```

## Analysis Tools

### Get Function Callees

```python
from slither_mcp.tools import FunctionCalleesRequest
from slither_mcp.types import ContractKey

async def get_function_callees():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        response = await client.function_callees(
            FunctionCalleesRequest(
                ext_function_signature="MyContract.transfer(address,uint256)",
                calling_context=ContractKey(
                    contract_name="MyContract",
                    path="src/MyContract.sol"
                )
            )
        )
        
        if response.success:
            print("Internal callees:")
            for callee in response.internal_callees:
                print(f"  - {callee}")
            
            print("External callees:")
            for callee in response.external_callees:
                print(f"  - {callee}")
            
            print("Library callees:")
            for callee in response.library_callees:
                print(f"  - {callee}")
```

### Get Inheritance Hierarchy

```python
from slither_mcp.tools import InheritanceHierarchyRequest
from slither_mcp.types import ContractKey

async def get_inheritance():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        response = await client.inheritance_hierarchy(
            InheritanceHierarchyRequest(
                contract_key=ContractKey(
                    contract_name="MyContract",
                    path="src/MyContract.sol"
                )
            )
        )
        
        if response.success and response.hierarchy:
            def print_hierarchy(node, indent=0):
                print("  " * indent + f"- {node.contract_name}")
                for child in node.inherits_from:
                    print_hierarchy(child, indent + 1)
            
            print_hierarchy(response.hierarchy)
```

### Find Function Implementations

```python
from slither_mcp.tools import ListFunctionImplementationsRequest
from slither_mcp.types import ContractKey

async def find_implementations():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        response = await client.list_function_implementations(
            ListFunctionImplementationsRequest(
                contract_key=ContractKey(
                    contract_name="IERC20",
                    path="src/interfaces/IERC20.sol"
                ),
                function_signature="transfer(address,uint256)"
            )
        )
        
        if response.success:
            print(f"Found {len(response.implementations)} implementations:")
            for impl in response.implementations:
                print(f"  - {impl.contract_name} at {impl.path}")
```

## Helper Methods

### Get All Contracts with Full Details

```python
async def get_all_contracts():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        # This helper method fetches all contracts with full details
        contracts = await client.get_all_contracts()
        
        for contract in contracts:
            print(f"Contract: {contract.contract_name}")
            print(f"  Functions: {len(contract.functions_declared)}")
```

### Build ProjectFacts

```python
async def build_project_facts():
    async with SlitherMCPClient() as client:
        await client.connect("/path/to/project", use_cache=True)
        
        # Build a complete ProjectFacts object
        facts = await client.get_project_facts()
        
        print(f"Project: {facts.project_dir}")
        print(f"Contracts: {len(facts.contracts)}")
        
        # Access contracts
        for contract_key, contract_model in facts.contracts.items():
            print(f"  - {contract_key.contract_name}")
```

## Integration with Pydantic-AI Agents

The client includes tool wrappers that make MCP tools compatible with pydantic-ai agents.

### Available Tool Wrappers

All MCP tools have corresponding wrapper creators:

**Query Tools:**
- `create_list_contracts_tool()` - List contracts with filters
- `create_get_contract_tool()` - Get detailed contract information
- `create_list_functions_tool()` - List functions with filters

**Analysis Tools:**
- `create_function_callees_tool()` - Get function call relationships
- `create_inheritance_hierarchy_tool()` - Get contract inheritance hierarchy
- `create_function_implementations_tool()` - Find function implementations

### Basic Agent Setup

```python
from slither_mcp.client import (
    SlitherMCPClient,
    create_list_contracts_tool,
    create_get_contract_tool,
    create_function_callees_tool,
    create_inheritance_hierarchy_tool,
)
from pydantic_ai import Agent

async def use_with_agent():
    # Connect client
    client = SlitherMCPClient()
    await client.connect("/path/to/project", use_cache=True)
    
    # Create tool wrappers (choose the ones you need)
    list_contracts_tool = create_list_contracts_tool(client)
    get_contract_tool = create_get_contract_tool(client)
    callees_tool = create_function_callees_tool(client)
    hierarchy_tool = create_inheritance_hierarchy_tool(client)
    
    # Create agent with tools
    agent = Agent(
        "openai:gpt-4",
        tools=[
            list_contracts_tool,
            get_contract_tool,
            callees_tool,
            hierarchy_tool,
        ],
    )
    
    # Use the agent
    result = await agent.run(
        "What contracts inherit from ERC20 and what functions does transfer call?"
    )
    print(result.data)
    
    # Clean up
    await client.close()
```

### Using All Available Tools

```python
from slither_mcp.client import (
    SlitherMCPClient,
    create_list_contracts_tool,
    create_get_contract_tool,
    create_list_functions_tool,
    create_function_callees_tool,
    create_inheritance_hierarchy_tool,
    create_function_implementations_tool,
)
from pydantic_ai import Agent

async def agent_with_all_tools():
    client = SlitherMCPClient()
    await client.connect("/path/to/project", use_cache=True)
    
    # Create all available tool wrappers
    tools = [
        create_list_contracts_tool(client),
        create_get_contract_tool(client),
        create_list_functions_tool(client),
        create_function_callees_tool(client),
        create_inheritance_hierarchy_tool(client),
        create_function_implementations_tool(client),
    ]
    
    # Create agent with all tools
    agent = Agent("openai:gpt-4", tools=tools)
    
    # The agent now has full access to analyze the Solidity project
    result = await agent.run(
        "Analyze the contract architecture and identify potential security issues"
    )
    print(result.data)
    
    await client.close()
```

## Complete Example

Here's a complete example that demonstrates multiple features:

```python
import asyncio
from slither_mcp.client import SlitherMCPClient
from slither_mcp.tools import (
    ListContractsRequest,
    GetContractRequest,
    ListFunctionsRequest,
    FunctionCalleesRequest,
)

async def analyze_project():
    async with SlitherMCPClient() as client:
        # Connect to project
        await client.connect("/path/to/solidity/project", use_cache=True)
        
        # List all concrete contracts
        contracts_response = await client.list_contracts(
            ListContractsRequest(filter_type="concrete")
        )
        
        if not contracts_response.success:
            print(f"Error: {contracts_response.error_message}")
            return
        
        print(f"Found {contracts_response.total_count} concrete contracts\n")
        
        # Analyze each contract
        for contract_info in contracts_response.contracts[:3]:  # First 3
            print(f"Analyzing {contract_info.key.contract_name}...")
            
            # Get contract details
            contract_response = await client.get_contract(
                GetContractRequest(
                    contract_key=contract_info.key,
                    include_functions=True
                )
            )
            
            if contract_response.success and contract_response.contract:
                contract = contract_response.contract
                print(f"  Functions: {len(contract.functions_declared)}")
                
                # Get callees for public/external functions
                for func in contract.functions_declared:
                    if func.visibility in ["public", "external"]:
                        callees_response = await client.function_callees(
                            FunctionCalleesRequest(
                                ext_function_signature=f"{contract.contract_name}.{func.signature}",
                                calling_context=contract_info.key
                            )
                        )
                        
                        if callees_response.success:
                            total_calls = (
                                len(callees_response.internal_callees) +
                                len(callees_response.external_callees) +
                                len(callees_response.library_callees)
                            )
                            print(f"    {func.signature}: {total_calls} calls")
            
            print()

if __name__ == "__main__":
    asyncio.run(analyze_project())
```

## Error Handling

All client methods return responses with a `success` boolean field. Always check this before accessing data:

```python
response = await client.list_contracts(
    ListContractsRequest(filter_type="all")
)

if response.success:
    # Process response.contracts
    for contract in response.contracts:
        print(contract.key.contract_name)
else:
    # Handle error
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
- `inheritance_hierarchy(request: InheritanceHierarchyRequest) -> InheritanceHierarchyResponse`
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
- `create_inheritance_hierarchy_tool(mcp_client: SlitherMCPClient)`
- `create_function_implementations_tool(mcp_client: SlitherMCPClient)`

All wrappers return async functions that can be used with pydantic-ai agents. For creating additional custom wrappers, see [ADDING_TOOLS.md](ADDING_TOOLS.md#step-5-create-client-tool-wrapper-optional).

