# Apigee MCP Gateway

This project implements a Model Context Protocol(MCP) Gateway using Apigee for Streamalble and Server-Sent Events (SSE) MCP servers.

## Project Overview


1. FastAPI SSE MCP Service
2. FastMCP Streaming Service
3. Apigee Proxy

## Prerequisites

- Python 3.8 or higher
- `uv` package manager (recommended) or `pip`
- Google Cloud SDK (for Apigee integration)

## Installation

1. Clone the repository
2. Create and activate a Python virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
apigee-mcp-gateway/
├── fastapi-sse-mcp/        # SSE-based MCP sample implementation
├── fastmcp-streaming/      # Streaming service sample implementation
├── requirements.txt        # Project dependencies
├── start_sse.sh           # Script to start SSE service
└── start_streaming.sh     # Script to start streaming service
```

## Running the Services

You can deploy these services in a VM so that Apigee can consume these services.

### SSE Service

To start the SSE service:

```bash
./start_sse.sh
```

This will start the FastAPI SSE service with hot-reload enabled.

### Streaming Service

To start the streaming service:

```bash
./start_streaming.sh
```

This will start the FastMCP streaming service on port 8080 with debug logging enabled.

## Deploy Apigee

### Uplaod the bundle mcp-gateway-demo.zip to upload the Apigee bundle.
### Update the URL in TargetServer for mcp and default. 


## Dependencies

The project uses the following main dependencies:

- `mcp` and `mcp[cli]`: Multi-Cloud Platform core and CLI tools
- `anthropic`: For AI/ML capabilities
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `aiohttp`: Async HTTP client/server
- `google-adk`: Google API Development Kit
- `fastmcp`: FastMCP implementation
- `gunicorn`: Production WSGI server

## Features

- Real-time streaming using Server-Sent Events (SSE)
- FastAPI-based REST API endpoints
- Multi-cloud platform integration
- Debug logging support
- Hot-reload for development

## Development

The services are configured for development with hot-reload enabled. For production deployment, consider:

1. Disabling hot-reload
2. Using gunicorn as the production server
3. Setting appropriate logging levels
4. Configuring proper security measures

## License

[Add appropriate license information]

## Contributing

[Add contribution guidelines if applicable]
