# main.py
import argparse
import asyncio
import os
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Mount, Route
import uvicorn
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from utils import proxy_spec_for_mcp
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

async def setup_mcp_server(proxy_name: str, base_url: str, access_token: Optional[str] = None) -> FastMCP:
    """Set up the MCP server with the given configuration."""
    # Get proxy spec
    proxy_spec = proxy_spec_for_mcp(proxy_name, access_token)
    
    # Extract OpenAPI spec and base path
    openapi_spec = proxy_spec["openapi_spec"]
    base_path = proxy_spec["base_path"]
    full_base_url = base_url.rstrip('/') + base_path.rstrip('/')
    
    print(f"Using base URL: {full_base_url}")
    
    # Create MCP server
    mcp = FastMCP(f"{proxy_name} MCP Server")
    
    # Create and run the OpenAPI tool generator with the spec dictionary and base URL
    generator = OpenAPIToolGenerator(mcp, openapi_spec, base_url=full_base_url)
    await generator.generate_tools()
    
    return mcp

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run an MCP server for Apigee proxy.')
    parser.add_argument(
        '--proxy-name',
        default=os.getenv('PROXY_NAME', 'retail-v1'),
        help='Name of the Apigee proxy to use'
    )
    parser.add_argument(
        '--base-url',
        default=os.getenv('APIGEE_RUNTIME_URL', 'https://bap-amer-west-demo1.cs.apigee.net'),
        help='Base URL for the Apigee runtime'
    )
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--access-token', help='Access token for Apigee API authentication')
    args = parser.parse_args()

    # Set up MCP server
    mcp = asyncio.run(setup_mcp_server(args.proxy_name, args.base_url, args.access_token))
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    print(f"\nServer '{args.proxy_name}' is ready. Starting Uvicorn on http://{args.host}:{args.port}")
    uvicorn.run(starlette_app, host=args.host, port=args.port)