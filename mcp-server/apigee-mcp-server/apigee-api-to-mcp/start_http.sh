#!/bin/bash

# Start HTTP MCP Server
# This script starts the HTTP implementation of the MCP server

echo "Starting HTTP MCP Server..."

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

# Start the HTTP server
echo "Starting server..."
python main_http.py "$@" 