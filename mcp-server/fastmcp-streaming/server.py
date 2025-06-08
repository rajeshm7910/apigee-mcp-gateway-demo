from fastmcp import FastMCP
import uvicorn

mcp = FastMCP(
    name="Httpbin MCP Server",
    instructions="This returns the httpbin endpoints."
)

@mcp.tool()
def echo_tool(message: str) -> str:
    """Echo a message as a tool"""
    return f"Tool echo: {message}"


@mcp.prompt()
def echo_prompt(message: str) -> str:
    """Create an echo prompt"""
    return f"Please process this message: {message}"


@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"


#if __name__ == "__main__":
#    mcp.run(transport="streamable-http", host="0.0.0.0", log_level="debug", port=8080, path="/mcp-gateway-demo/mcp")

def get_app():
    return mcp.http_app(transport="streamable-http", path="/mcp-gateway-demo/mcp")

if __name__ == "__main__":
    uvicorn.run(get_app(), host="0.0.0.0", port=8080)
    
