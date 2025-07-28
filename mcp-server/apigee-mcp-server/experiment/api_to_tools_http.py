import httpx
from fastmcp import FastMCP
import os
from dotenv import load_dotenv
import yaml

# Load environment variables from .env
load_dotenv()

# Get OpenAPI spec path/URL and base URL from environment
openapi_spec_path = os.getenv("PROXY_OPENAPI_SPEC")
base_url = os.getenv("APIGEE_BASE_PATH")

if not openapi_spec_path:
    raise ValueError("PROXY_OPENAPI_SPEC environment variable is not set.")
if not base_url:
    raise ValueError("APIGEE_BASE_PATH environment variable is not set.")

# Load the OpenAPI spec (from file or URL)
if openapi_spec_path.startswith(("http://", "https://")):
    openapi_spec = httpx.get(openapi_spec_path).json()
else:
    with open(openapi_spec_path, "r") as f:
        # Support YAML or JSON
        content = f.read()
        try:
            openapi_spec = yaml.safe_load(content)
        except Exception:
            import json
            openapi_spec = json.loads(content)

# Create an HTTP client for your API
client = httpx.AsyncClient(base_url=base_url)

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Apigee MCP Server - HTTP"
)

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=4202,
        log_level="debug"
    )