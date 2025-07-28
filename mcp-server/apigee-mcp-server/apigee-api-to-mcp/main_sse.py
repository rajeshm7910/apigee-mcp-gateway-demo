# main_sse.py
import argparse
import asyncio
import os
import yaml
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Mount, Route
import uvicorn
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from openapi_generator import OpenAPIToolGenerator
from typing import Optional
from starlette.responses import Response

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get headers and query params from the request
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        
        # Remove content-length as it will be recalculated
        if 'content-length' in headers:
            del headers['content-length']
        
        # Store request context in a way that's accessible to tools
        request.scope['mcp_request_context'] = {
            'headers': headers,
            'query_params': query_params
        }
        
        # Continue with the request
        response = await call_next(request)
        return response

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        # Get request context from scope
        request_context = request.scope.get('mcp_request_context', {})
        
        try:
            async with sse.connect_sse(
                    request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                # Create initialization options with request context
                init_options = mcp_server.create_initialization_options()
                # Store request context in a way that's accessible to tools
                mcp_server._request_context = request_context
                
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    init_options,
                )
        except Exception as e:
            print(f"SSE connection error: {e}")
            # Let the SSE transport handle the disconnection
            return None

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        middleware=[
            (RequestContextMiddleware, [], {}),
        ],
    )

async def setup_mcp_server(openapi_spec_path: str, base_url: str) -> FastMCP:
    """Set up the MCP server and tool generator using a local OpenAPI spec file."""
    
    # Load OpenAPI spec from file
    try:
        with open(openapi_spec_path, 'r') as f:
            openapi_spec = yaml.safe_load(f)
        print(f"Loaded OpenAPI spec from: {openapi_spec_path}")
    except (yaml.YAMLError, FileNotFoundError) as e:
        raise ValueError(f"Failed to read or parse OpenAPI spec file '{openapi_spec_path}': {e}")
    
    # Extract server name from OpenAPI spec
    server_name = openapi_spec.get("info", {}).get("title", "MCP Server")
    if not server_name or server_name == "MCP Server":
        server_name = "Apigee MCP Server"
    
    print(f"Using base URL: {base_url}")
    
    # Create MCP server
    mcp = FastMCP(server_name)
    
    # Create and run the OpenAPI tool generator with the spec dictionary and base URL
    generator = OpenAPIToolGenerator(mcp, openapi_spec, base_url=base_url)
    await generator.generate_tools()
    
    return mcp

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run an MCP server for Apigee proxy with SSE transport.')
    parser.add_argument('--openapi-spec', default=os.getenv('OPENAPI_SPEC_PATH', 'resources/hipster-openapi.yaml'), 
                       help='Path to the OpenAPI specification file')
    parser.add_argument('--base-url', default=os.getenv('APIGEE_PROXY_BASE_URL', 'https://bap-amer-west-demo1.cs.apigee.net'), 
                       help='Base URL for the proxy API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    # Set up MCP server
    mcp = asyncio.run(setup_mcp_server(args.openapi_spec, args.base_url))
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    print(f"\nSSE Server is ready. Starting Uvicorn on http://{args.host}:{args.port}")
    print(f"Configuration:")
    print(f"  OpenAPI Spec: {args.openapi_spec}")
    print(f"  Base URL: {args.base_url}")
    print(f"\nAvailable endpoints:")
    print(f"  GET  /sse      - SSE connection endpoint")
    print(f"  POST /messages/ - MCP message endpoint")
    
    uvicorn.run(starlette_app, host=args.host, port=args.port)