# Apigee MCP Demo

This repository demonstrates the integration of Apigee API Gateway with Model Context Protocol (MCP) servers, showcasing both HTTP and Server-Sent Events (SSE) streaming capabilities. The project provides a complete solution for building AI-powered applications with enterprise-grade API management.

## Project Overview

This demo consists of three main components that work together to create a comprehensive MCP ecosystem:

1. **MCP Server** - Converts Apigee APIs into MCP tools
2. **MCP Gateway** - Provides streaming capabilities with Apigee as the gateway
3. **Frontend Demo** - Web-based chat interface for testing

## Project Structure

### 📁 `apigee-mcp-server/`
**MCP Server Implementation**

This folder contains the core MCP server that bridges Apigee APIs with AI models by converting API endpoints into MCP tools.

#### Subfolders:
- **`apigee-api-to-mcp/`** - Main MCP server implementation
  - `main_http.py` - HTTP-based MCP server
  - `main_sse.py` - Server-Sent Events MCP server
  - `openapi_generator.py` - Generates MCP tools from OpenAPI specifications
  - `start_http.sh` / `start_sse.sh` - Startup scripts
  - `resources/` - Configuration files and OpenAPI specs
  - `venv/` - Python virtual environment

- **`experiment/`** - Experimental implementations
  - `api_to_tools_http.py` - HTTP-based API-to-tools conversion
  - `api_to_tools_sse.py` - SSE-based API-to-tools conversion
  - `local_start.sh` - Local development startup script

**Key Features:**
- Converts Apigee API proxies into MCP tools
- Supports both HTTP and SSE transport protocols
- Automatic tool generation from OpenAPI specifications
- Integration with Google Cloud credentials
- Real-time API proxy control

### 📁 `apigee-mcp-gateway/`
**MCP Gateway with Apigee Integration**

This folder implements a complete MCP gateway solution using Apigee as the API gateway, providing enterprise-grade features like rate limiting, authentication, and monitoring.

#### Subfolders:
- **`fastapi-sse-mcp/`** - FastAPI-based SSE MCP server
  - `app/` - FastAPI application code
  - `server.py` - Server startup configuration
  - `pyproject.toml` - Project dependencies
  - `README.md` - Detailed setup instructions

- **`fastmcp-streaming/`** - FastMCP streaming implementation
  - `server.py` - Streaming server implementation

- **`resources/`** - Apigee configuration and assets
  - `apigee-sse-demo.zip` - Apigee proxy bundle
  - `mcp-gateway-demo-policies.zip` - Apigee policies
  - `images/` - Documentation screenshots
  - `start_sse.sh` / `start_streaming.sh` - Service startup scripts

**Key Features:**
- Server-Sent Events (SSE) streaming
- FastMCP streaming implementation
- Apigee proxy with security policies
- Model Armor integration for prompt sanitization
- Rate limiting and authentication
- Comprehensive monitoring and logging

### 📁 `apigee-sse-demo/`
**Frontend Chat Interface**

A simple web-based chat interface for testing the MCP streaming capabilities.

**Contents:**
- `index.html` - Chat interface with real-time streaming
- `package.json` - Node.js dependencies
- `package-lock.json` - Dependency lock file

**Features:**
- Real-time chat interface
- Server-Sent Events integration
- Simple static server setup
- Modern UI with streaming animations

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js (for frontend demo)
- Google Cloud SDK
- Apigee Edge or Apigee X/Hybrid access
- Service account with Apigee Admin permissions

### Quick Start

1. **Start the MCP Server:**
   ```bash
   cd apigee-mcp-server/apigee-api-to-mcp
   ./start_sse.sh
   ```

2. **Start the MCP Gateway:**
   ```bash
   cd apigee-mcp-gateway
   ./start_sse.sh
   ```

3. **Start the Frontend Demo:**
   ```bash
   cd apigee-sse-demo
   npm install
   npm start
   ```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Apigee        │    │   MCP Server    │
│   (Chat UI)     │◄──►│   Gateway       │◄──►│   (API Tools)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Apigee APIs   │
                       └─────────────────┘
```

## Use Cases

1. **AI-Powered API Management** - Convert existing APIs into AI-accessible tools
2. **Enterprise Streaming** - Real-time AI interactions with enterprise-grade security
3. **API Gateway Integration** - Leverage Apigee's security and monitoring capabilities
4. **Prompt Sanitization** - Use Model Armor to prevent prompt injection attacks

## Key Technologies

- **Model Context Protocol (MCP)** - Standard for AI model integration
- **Apigee API Gateway** - Enterprise API management
- **Server-Sent Events (SSE)** - Real-time streaming
- **FastAPI** - Modern Python web framework
- **Google Cloud** - Infrastructure and services

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support, please refer to the individual README files in each component folder or create an issue in this repository.