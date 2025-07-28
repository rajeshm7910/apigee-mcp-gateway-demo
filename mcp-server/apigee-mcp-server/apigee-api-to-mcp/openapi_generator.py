import json
from typing import Any, Callable, Coroutine, Union, Type
import httpx
import yaml
from mcp.server.fastmcp import FastMCP
import inspect
from functools import wraps

class OpenAPIToolGenerator:
    """
    Dynamically generates and registers MCP tool functions from an OpenAPI specification.
    It also stores the raw operation details for later schema generation.
    """
    def __init__(self, mcp: FastMCP, openapi_source: Union[str, dict], base_url: str = ""):
        self.mcp = mcp
        self.openapi_source = openapi_source
        self.spec: dict[str, Any] = {}
        self.base_url: str = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        # This dictionary will hold the OpenAPI operation details for each tool.
        self.operations: dict[str, dict] = {}

    async def generate_tools(self):
        """Loads the spec and generates all tools."""
        print("Loading OpenAPI spec...")
        await self._load_spec()
        if not self.base_url:
            self._extract_base_url()
        print(f"Using API base URL: {self.base_url}")
        print("Generating tool functions from spec...")
        await self._create_tools_from_spec()
        print("Tool function generation complete.")

    async def _load_spec(self):
        """Fetches and parses the OpenAPI spec."""
        try:
            if isinstance(self.openapi_source, dict):
                self.spec = self.openapi_source
            elif isinstance(self.openapi_source, str):
                if self.openapi_source.startswith(('http://', 'https://')):
                    response = await self.client.get(self.openapi_source)
                    response.raise_for_status()
                    self.spec = yaml.safe_load(response.text)
                else:
                    with open(self.openapi_source, 'r') as f:
                        self.spec = yaml.safe_load(f.read())
            else:
                raise ValueError("openapi_source must be a string or a dictionary")
        except Exception as e:
            print(f"Error loading or parsing OpenAPI spec: {e}")
            raise

    def _extract_base_url(self):
        """Extracts the base URL from the spec's 'servers' block."""
        if "servers" in self.spec and self.spec["servers"]:
            self.base_url = self.spec["servers"][0]["url"]
        else:
             self.base_url = ""
        self.base_url = self.base_url.rstrip('/')

    async def _create_tools_from_spec(self):
        """Iterates through paths to create and register tool functions."""
        paths = self.spec.get("paths", {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    op_id = operation.get("operationId")
                    if not op_id:
                        op_id = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
                    
                    # Store the raw operation details for the HTTP handler to use later.
                    self.operations[op_id] = operation
                    
                    # Create and register the tool function.
                    await self._create_and_register_tool(op_id, path, method, operation)

    async def _create_and_register_tool(self, op_id: str, path: str, method: str, operation: dict):
        """Creates and registers a simple tool function."""
        tool_func = self._tool_function_factory(path, method, operation)
        tool_func.__name__ = op_id
        print(f"  - Registering tool function: {op_id}")
        # Use the simple, reliable add_tool method.
        self.mcp.add_tool(tool_func, name=op_id)

    def _tool_function_factory(
        self, path: str, method: str, operation: dict
    ) -> Callable[..., Coroutine[Any, Any, Union[dict, list, str]]]:
        """Factory to create the async tool function that makes the HTTP call."""
        param_map = {p["name"]: p["in"] for p in operation.get("parameters", [])}

        async def tool_function(**kwargs: Any) -> Union[dict, list, str]:
            request_context = getattr(self.mcp._mcp_server, '_request_context', {})
            headers: dict[str, str] = {"Accept": "application/json"}
            query_params_dict: dict[str, Any] = {}
            path_params_dict: dict[str, Any] = {}
            json_body: Any = None 

            if request_context:
                if 'authorization' in request_context.get('headers', {}):
                    headers['Authorization'] = request_context['headers']['authorization']
                query_params_dict.update(request_context.get('query_params', {}))
            
            for name, value in kwargs.items():
                if value is None: continue
                param_location = param_map.get(name)
                if param_location in ("path", "text"): path_params_dict[name] = value
                elif param_location == "query": query_params_dict[name] = value
                elif param_location == "header": headers[name] = str(value)
                elif name == "body": json_body = value

            try:
                formatted_path = path.format(**path_params_dict)
                full_url = f"{self.base_url}{formatted_path}"
            except KeyError as e:
                return f"Error: Missing required path parameter: {e}"

            try:
                response = await self.client.request(
                    method=method, url=full_url, headers=headers, params=query_params_dict, json=json_body
                )
                response.raise_for_status()
                try: return response.json()
                except json.JSONDecodeError: return response.text
            except httpx.HTTPStatusError as e:
                return f"API Error: {e.response.status_code} - {e.response.text}"
            except Exception as e:
                return f"An unexpected error occurred: {str(e)}"
        
        tool_function.__signature__ = self._generate_signature(operation)
        tool_function.__doc__ = self._generate_docstring(operation)
        return tool_function
    
    @staticmethod
    def _generate_signature(operation: dict) -> inspect.Signature:
        """Generates a Python function signature from an OpenAPI operation."""
        sig_params = []
        for param in operation.get("parameters", []):
            sig_params.append(inspect.Parameter(
                name=param["name"], kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=None if not param.get("required") else inspect.Parameter.empty
            ))
        return inspect.Signature(parameters=sig_params)

    @staticmethod
    def _generate_docstring(operation: dict) -> str:
        """Generates a Python docstring from OpenAPI operation details."""
        return operation.get("summary") or operation.get("description") or "No description."