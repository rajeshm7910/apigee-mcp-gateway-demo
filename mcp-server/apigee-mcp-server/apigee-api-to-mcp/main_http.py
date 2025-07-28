# main_http.py
import argparse
import asyncio
import os
import yaml
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Mount, Route
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from openapi_generator import OpenAPIToolGenerator
from typing import Optional
import json

# This global variable will hold the generator instance, allowing the request
# handler to access the OpenAPI operation details needed for schema building.
generator: Optional[OpenAPIToolGenerator] = None

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        if 'content-length' in headers:
            del headers['content-length']
        request.scope['mcp_request_context'] = {'headers': headers, 'query_params': query_params}
        response = await call_next(request)
        return response

def create_starlette_app(mcp: FastMCP, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with HTTP."""
    
    async def handle_mcp_request(request: Request) -> Response:
        """Handle MCP JSON-RPC requests by building compliant responses manually."""
        try:
            body = await request.json()

            if hasattr(mcp, '_mcp_server'):
                mcp._mcp_server._request_context = request.scope.get('mcp_request_context', {})

            method = body.get("method")
            request_id = body.get("id")
            
            if method == "initialize":
                response_data = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"listChanged": True},
                            "prompts": {"listChanged": True}
                        },
                        "serverInfo": {
                            "name": "Apigee MCP Server",
                            "version": "1.0.0"
                        }
                    }
                }
                return JSONResponse(content=response_data)
                
            elif method == "tools/list":
                try:
                    tool_list = await mcp.list_tools()
                    
                    tools_for_response = []
                    for tool in tool_list:
                        operation = generator.operations.get(tool.name, {})
                        
                        properties = {}
                        required = []
                        for param in operation.get("parameters", []):
                            param_name = param.get("name")
                            if not param_name: continue
                            
                            properties[param_name] = {
                                "title": param_name.capitalize(),
                                "type": param.get("schema", {}).get("type", "string")
                            }
                            if param.get("required"):
                                required.append(param_name)
                        
                        input_schema = {
                            "title": f"{tool.name}Arguments",
                            "type": "object",
                            "properties": properties,
                        }
                        if required:
                            input_schema["required"] = required

                        tools_for_response.append({
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": input_schema
                        })
                    
                    response_data = {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools_for_response}}
                    return JSONResponse(content=response_data)
                except Exception as e:
                    import traceback; traceback.print_exc()
                    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": f"Internal error during tools/list: {str(e)}"}})
                
            elif method in ["resources/list", "prompts/list"]:
                 return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {method.split('/')[0]: []}})

            elif method == "tools/call":
                # Handle tools/call request
                params = body.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                try:
                    # --- FINAL FIX: Handle the `TextContent` object ---
                    # 1. The library returns the result wrapped in a content object(s).
                    result_from_mcp = await mcp.call_tool(tool_name, tool_args)
                    
                    content_for_response = []
                    # 2. Check if the result is a list, as the spec allows multiple content blocks.
                    if isinstance(result_from_mcp, list):
                        for item in result_from_mcp:
                            # 3. Safely get the .text attribute from each item.
                            content_for_response.append({
                                "type": "text",
                                "text": getattr(item, 'text', str(item))
                            })
                    # 4. Handle the case where a single content object is returned.
                    else:
                         content_for_response.append({
                            "type": "text",
                            "text": getattr(result_from_mcp, 'text', str(result_from_mcp))
                        })

                    # 5. Build the final, compliant response.
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": content_for_response
                        }
                    }
                    return JSONResponse(content=response_data)
                except Exception as tool_error:
                    import traceback; traceback.print_exc()
                    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": f"Tool execution failed: {str(tool_error)}"}})
                
            else:
                return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})
                
        except Exception as e:
            import traceback; traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": f"Internal Server Error: {str(e)}"})
    
    async def handle_health(request: Request) -> Response:
        return JSONResponse(content={"status": "healthy", "service": "MCP HTTP Server"})

    return Starlette(debug=debug, routes=[
        Mount("/mcp", routes=[
            Route("/", endpoint=handle_mcp_request, methods=["POST"]),
            Route("/health", endpoint=handle_health, methods=["GET"]),
        ])
    ], middleware=[
        (RequestContextMiddleware, [], {})
    ])

async def setup_mcp_server(openapi_spec_path: str, base_url: str) -> FastMCP:
    """Set up the MCP server and tool generator using a local OpenAPI spec file."""
    global generator
    
    # Load OpenAPI spec from file
    try:
        with open(openapi_spec_path, 'r') as f:
            openapi_spec = yaml.safe_load(f)
    except (yaml.YAMLError, FileNotFoundError) as e:
        raise ValueError(f"Failed to read or parse OpenAPI spec file '{openapi_spec_path}': {e}")
    
    # Extract server name from OpenAPI spec
    server_name = openapi_spec.get("info", {}).get("title", "MCP Server")
    if not server_name or server_name == "MCP Server":
        server_name = "Apigee MCP Server"
    
    mcp = FastMCP(server_name)
    
    generator = OpenAPIToolGenerator(mcp, openapi_spec, base_url=base_url)
    await generator.generate_tools()
    
    return mcp

if __name__ == "__main__":
    import pathlib
    script_dir = pathlib.Path(__file__).parent
    env_file = script_dir / ".env"
    
    if env_file.exists(): load_dotenv(env_file)
    else: load_dotenv()
    
    parser = argparse.ArgumentParser(description='Run an MCP server for Apigee proxy with HTTP transport.')
    parser.add_argument('--openapi-spec', default=os.getenv('OPENAPI_SPEC_PATH', 'resources/hipster-openapi.yaml'), 
                       help='Path to the OpenAPI specification file')
    parser.add_argument('--base-url', default=os.getenv('APIGEE_PROXY_BASE_URL', 'https://bap-amer-west-demo1.cs.apigee.net'), 
                       help='Base URL for the proxy API')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    mcp = asyncio.run(setup_mcp_server(args.openapi_spec, args.base_url))
    starlette_app = create_starlette_app(mcp, debug=True)
    
    print(f"\nHTTP Server is ready. Starting Uvicorn on http://{args.host}:{args.port}")
    print(f"Configuration:")
    print(f"  OpenAPI Spec: {args.openapi_spec}")
    print(f"  Base URL: {args.base_url}")
    print(f"\nAvailable endpoints:")
    print(f"  GET  /mcp/health - Health check")
    print(f"  POST /mcp/       - MCP JSON-RPC endpoint")
    
    uvicorn.run(starlette_app, host=args.host, port=args.port)