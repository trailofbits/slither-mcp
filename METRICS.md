# Metrics and Error Reporting

This document explains how Slither MCP collects metrics data, what information is gathered, and how to control these features.

## Overview

Slither MCP includes opt-out metrics to help improve reliability by letting us know how often LLMs use each tool and their successful call rate. Metrics are **enabled by default** but can be permanently disabled.

## What We Collect

### Basic Metrics (Default)

When metrics are enabled, Slither MCP collects:

- **Tool call events**: Which MCP tools are invoked (e.g., `list_contracts`, `get_function_source`)
- **Success/failure status**: Whether each tool call succeeded or failed

## What We DON'T Collect

Slither MCP is designed with privacy in mind and its metrics do not collect:

- Tool parameters or arguments
- Contract names, addresses, or source code
- Project paths or directory structures
- Function names or signatures
- Server hostname or machine name
- Command-line arguments (sys.argv)
- Any sensitive or project-specific information

**Only tool names and success/failure status** are transmitted.

### Privacy Protections

Our `before_send` hook explicitly strips out:
- `server_name` - Your machine's hostname
- `sys.argv` - Command-line arguments that might contain paths or flags

## Precisely What Metrics Collects

When metrics are enabled, the following Sentry events are transmitted for each tool call:

### 1. Tool Call Event
- **Event type**: `capture_message`
- **Message**: `"tool_call_{tool_name}"` (e.g., `"tool_call_list_contracts"`)
- **Level**: `info`
- **Data transmitted**:
  - `tool_name`: The name of the MCP tool (e.g., "list_contracts", "get_function_source")
  - No parameters, no arguments, no request data

### 2. Tool Success/Failure Event
- **Event type**: `capture_message`
- **Message**: `"tool_success_{tool_name}"` or `"tool_failure_{tool_name}"` (e.g., `"tool_success_list_contracts"`)
- **Level**: `info`
- **Data transmitted**:
  - `tool_name`: The name of the MCP tool
  - Success/failure boolean (encoded in the message)
  - No error details, no parameters, no results

### 3. Tool Exception Event (only if an exception occurs)
- **Event type**: `capture_message`
- **Message**: `"tool_exception_{tool_name}"` (e.g., `"tool_exception_list_contracts"`)
- **Level**: `error`
- **Data transmitted**:
  - `tool_name`: The name of the MCP tool
  - No exception details (unless `--enhanced-error-reporting` is enabled)
  - No stack trace, no parameters, no context


## How to Disable Metrics

### Permanent Opt-Out

To permanently disable all metrics and error reporting:

```bash
uv run slither-mcp --disable-metrics
```

This creates a marker file at `~/.slither-mcp/metrics_disabled` that persists across sessions. You only need to run this command once.

### Verification

When you start the server after disabling metrics, you'll see the following in stderr:

```
Metrics disabled (found /Users/your-username/.slither-mcp/metrics_disabled)
```

## Enhanced Error Reporting

THIS IS NOT METRICS AND IS A TOTALLY DIFFERENT THING. THIS IS NOT ENABLED BY DEFAULT. **DO NOT USE THIS UNLESS YOU ARE ASKED**. When an error occurs, this flag will transmit full stack traces, parameters, environment variables, etc. to ToB's Sentry endpoint. 

### Enabling Enhanced Reporting

```bash
uv run slither-mcp --enhanced-error-reporting
```

## Data Transmission

All metrics data is transmitted to [Sentry](https://sentry.io), a third-party error tracking service. Sentry's privacy policy can be found at https://sentry.io/privacy/.

The data is sent to:
```
https://o4510280629420032.ingest.us.sentry.io
```

## Why Metrics?

Metrics help us:

1. **Identify reliability issues**: Track which tools fail most often
2. **Prioritize improvements**: Focus on the most-used features
3. **Understand adoption**: See which tools are most valuable

We're committed to transparency and user privacy. If you have concerns or questions about metrics, please open an issue on GitHub.



