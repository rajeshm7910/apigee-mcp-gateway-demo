import httpx
from fastmcp import FastMCP
from utils import proxy_spec_for_mcp
from dotenv import load_dotenv
import os
from fastmcp.server.openapi import RouteMap, MCPType

load_dotenv()

# Create an HTTP client for your API
base_url = os.getenv("APIGEE_RUNTIME_URL", "https://bap-amer-west-demo1.cs.apigee.net")
proxy_name = os.getenv("PROXY_NAME", "retail-v1");

proxy_spec = proxy_spec_for_mcp(proxy_name)

# Load your OpenAPI spec 
openapi_spec =  proxy_spec["openapi_spec"]
base_path = proxy_spec["base_path"]
base_url = base_url + base_path 

client = httpx.AsyncClient(base_url=base_url)


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