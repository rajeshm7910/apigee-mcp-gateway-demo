#!/bin/bash

# Start SSE MCP Server
# This script starts the SSE (Server-Sent Events) implementation of the MCP server

echo "Starting SSE MCP Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default environment variables if not already set
export OPENAPI_SPEC_PATH=${OPENAPI_SPEC_PATH:-"resources/hipster-openapi.yaml"}
export APIGEE_PROXY_BASE_URL=${APIGEE_PROXY_BASE_URL:-"https://bap-amer-west-demo1.cs.apigee.net"}

echo "Environment variables:"
echo "  OPENAPI_SPEC_PATH: $OPENAPI_SPEC_PATH"
echo "  APIGEE_PROXY_BASE_URL: $APIGEE_PROXY_BASE_URL"
echo ""

# Check if OpenAPI spec file exists
if [ ! -f "$OPENAPI_SPEC_PATH" ]; then
    echo "ERROR: OpenAPI spec file not found: $OPENAPI_SPEC_PATH"
    echo "Please ensure the OpenAPI specification file exists at the specified path"
    echo "Example: export OPENAPI_SPEC_PATH=resources/hipster-openapi.yaml"
    echo "Or create a .env file with: OPENAPI_SPEC_PATH=resources/hipster-openapi.yaml"
    exit 1
fi

echo "✓ OpenAPI spec file found: $OPENAPI_SPEC_PATH"

# Start the SSE server
echo "Starting SSE server..."
echo ""
echo "SSE Server endpoints:"
echo "  GET  /sse       - SSE connection endpoint"
echo "  POST /messages/  - Send messages to SSE connection"
echo ""
echo "Note: This server uses Server-Sent Events (SSE) for real-time communication"
echo "      Connect to /sse endpoint to establish an SSE connection"

python main_sse.py "$@" 