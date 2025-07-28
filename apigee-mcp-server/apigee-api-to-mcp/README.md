# Apigee MCP Server (SSE & HTTP Streaming)

This repository contains both Server-Sent Events (SSE) and HTTP streaming implementations of the Model Context Protocol (MCP) server that generates tools from OpenAPI specifications.

## Available Implementations

### 1. SSE Implementation (`main_sse.py`)
- **Transport**: Server-Sent Events (SSE) for real-time communication
- **Use Case**: Real-time streaming with persistent connections
- **Endpoints**: `GET /sse`, `POST /messages/`

### 2. HTTP Implementation (`main_http.py`)
- **Transport**: HTTP JSON-RPC with streaming support
- **Use Case**: Traditional request-response with streaming capabilities
- **Endpoints**: `GET /mcp/health`, `POST /mcp/`

## Setup

### 1. Environment Variables

You need to set up environment variables for the server configuration. You can do this in two ways:

#### Option A: Create a .env file (Recommended)

Create a `.env` file in the same directory as the main scripts with the following content:

```bash
# Required: Path to the OpenAPI specification file
OPENAPI_SPEC_PATH=resources/hipster-openapi.yaml

# Required: Base URL for the proxy API
APIGEE_PROXY_BASE_URL=https://bap-amer-west-demo1.cs.apigee.net

# Optional: Server host (default: 0.0.0.0)
# HOST=0.0.0.0

# Optional: Server port (default: 8080)
# PORT=8080
```

#### Option B: Set environment variables in your shell

```bash
export OPENAPI_SPEC_PATH=resources/hipster-openapi.yaml
export APIGEE_PROXY_BASE_URL=https://bap-amer-west-demo1.cs.apigee.net
```

### 2. OpenAPI Specification File

The server expects an OpenAPI specification file (YAML format) that defines your API endpoints. The file should be placed in the `resources/` directory or specified via the `OPENAPI_SPEC_PATH` environment variable.

Example OpenAPI spec structure:
```yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
paths:
  /products:
    get:
      operationId: GetProducts
      summary: Get all products
      responses:
        '200':
          description: Successful operation
  /products/{productId}:
    get:
      operationId: GetProductDetails
      summary: Get product by ID
      parameters:
        - name: productId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful operation
```

## Running the Servers

### SSE Server (Real-time Streaming)

#### Using the start script (Recommended)
```bash
./start_sse.sh
```

#### Running directly with Python
```bash
python main_sse.py
```

#### With custom arguments
```bash
python main_sse.py --openapi-spec resources/my-api.yaml --base-url https://api.example.com
```

### HTTP Server (Traditional Request-Response)

#### Using the start script (Recommended)
```bash
./start_http.sh
```

#### Running directly with Python
```bash
python main_http.py
```

#### With custom arguments
```bash
python main_http.py --openapi-spec resources/my-api.yaml --base-url https://api.example.com
```

## Available Endpoints

### SSE Server Endpoints
- `GET /sse` - SSE connection endpoint for real-time MCP communication
- `POST /messages/` - Send MCP messages to the SSE connection

### HTTP Server Endpoints
- `GET /mcp/health` - Health check
- `POST /mcp/` - MCP JSON-RPC endpoint

## MCP Methods Supported

Both implementations support the following MCP methods:

- `initialize` - Initialize the MCP connection
- `tools/list` - List available tools generated from OpenAPI spec
- `tools/call` - Execute a tool with arguments
- `resources/list` - List available resources (returns empty)
- `prompts/list` - List available prompts (returns empty)

### Example MCP tools/call request:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "GetProducts",
    "arguments": {}
  }
}
```

## Communication Methods

### SSE Communication (Real-time)

The SSE implementation uses Server-Sent Events for real-time communication:

1. **Connection**: Connect to the `/sse` endpoint to establish an SSE connection
2. **Message Sending**: Send MCP messages via POST requests to `/messages/`
3. **Real-time Updates**: Receive real-time responses through the SSE stream
4. **Request Context**: Headers and query parameters from the initial SSE connection are preserved and available to tools

#### SSE Connection Flow

1. Establish SSE connection to `GET /sse`
2. Send MCP messages via `POST /messages/` with JSON-RPC format
3. Receive real-time responses through the SSE stream
4. The connection maintains state and context throughout the session

### HTTP Communication (Traditional)

The HTTP implementation uses standard JSON-RPC over HTTP:

1. **Request-Response**: Send JSON-RPC requests to `POST /mcp/`
2. **Streaming Support**: Responses can be streamed for long-running operations
3. **Health Monitoring**: Use `GET /mcp/health` for health checks
4. **Request Context**: Headers and query parameters are preserved for tool execution

#### HTTP Request Flow

1. Send JSON-RPC request to `POST /mcp/`
2. Receive JSON-RPC response
3. For streaming operations, responses are chunked and streamed
4. Use health endpoint for monitoring server status

## Tool Generation

Both servers automatically generate MCP tools from your OpenAPI specification:

1. Each operation in the OpenAPI spec becomes a tool
2. The `operationId` field is used as the tool name
3. Path parameters and query parameters become tool arguments
4. The tool description comes from the `summary` field
5. Request context (headers, query params) is preserved and available to tools

## Choosing Between Implementations

### Use SSE Implementation When:
- You need real-time, persistent connections
- Your client supports Server-Sent Events
- You want to maintain connection state
- You're building real-time applications

### Use HTTP Implementation When:
- You prefer traditional request-response patterns
- Your client doesn't support SSE
- You need simple HTTP integration
- You want standard JSON-RPC over HTTP

## Troubleshooting

### OpenAPI Spec File Not Found

If you see "OpenAPI spec file not found" error:

1. Make sure your OpenAPI spec file exists at the path specified in `OPENAPI_SPEC_PATH`
2. Check that the file is in valid YAML format
3. Verify the file path is correct relative to the script directory

### Environment Variables Not Loading

If you see "Not set" for environment variables, make sure:

1. Your `.env` file exists in the same directory as the main scripts
2. The `.env` file has the correct format (no spaces around `=`)
3. You're running the script from the correct directory

### SSE Connection Issues

If you have trouble with SSE connections:

1. Ensure your client supports SSE (Server-Sent Events)
2. Check that the `/sse` endpoint is accessible
3. Verify that messages are being sent to `/messages/` endpoint
4. Check browser console or server logs for connection errors

### HTTP Connection Issues

If you have trouble with HTTP connections:

1. Verify the server is running on the correct port
2. Check that `POST /mcp/` endpoint is accessible
3. Ensure requests are in valid JSON-RPC format
4. Check server logs for error messages

### Tool Generation Issues

If tools are not being generated:

1. Check that your OpenAPI spec has valid `operationId` fields
2. Ensure the `paths` section is properly formatted
3. Verify that the base URL is correct and accessible 