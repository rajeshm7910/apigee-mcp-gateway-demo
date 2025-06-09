import httpx
from fastmcp import FastMCP
from utils import create_openapi_spec
from dotenv import load_dotenv
import os
from fastmcp.server.openapi import RouteMap, MCPType

load_dotenv()

# Create an HTTP client for your API
base_url = os.getenv("PROXY_BASE_URL", "https://bap-amer-west-demo1.cs.apigee.net/retail/v1")
client = httpx.AsyncClient(base_url=base_url)

proxy_name = os.getenv("PROXY_NAME", "retail-v1");

# Load your OpenAPI spec 
openapi_spec =  create_openapi_spec(proxy_name)

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Apigee MCP Server",
    route_maps=[
        RouteMap(mcp_type=MCPType.TOOL),
    ],
)

if __name__ == "__main__":
    mcp.run(transport="streamable-http",path="/mcp")