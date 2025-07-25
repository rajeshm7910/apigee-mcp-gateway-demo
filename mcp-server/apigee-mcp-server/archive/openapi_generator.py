import json
from typing import Any, Callable, Coroutine, Union, Type
import httpx
import yaml
from mcp.server.fastmcp import FastMCP
import inspect
from functools import wraps

class OpenAPIToolGenerator:
    """
    Dynamically generates and registers MCP tools from an OpenAPI specification.
    Supports both URL and local file paths, as well as direct OpenAPI spec dictionaries.
    """

    def __init__(self, mcp: FastMCP, openapi_source: Union[str, dict], base_url: str = ""):
        """
        Initializes the generator.

        Args:
            mcp: An instance of FastMCP to register tools with.
            openapi_source: The URL, file path to the OpenAPI spec (JSON or YAML), or the OpenAPI spec dictionary.
            base_url: The base URL to use for API requests. If not provided, will try to extract from spec.
        """
        self.mcp = mcp
        self.openapi_source = openapi_source
        self.spec: dict[str, Any] = {}
        self.base_url: str = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate_tools(self):
        """
        Loads the spec and generates all tools.
        """
        print("Loading OpenAPI spec...")
        await self._load_spec()
        if not self.base_url:
            self._extract_base_url()
        print(f"Using API base URL: {self.base_url}")
        print("Generating tools from spec...")
        self._create_tools_from_spec()
        print("Tool generation complete.")

    async def _load_spec(self):
        """Fetches and parses the OpenAPI spec from URL, file, or uses the provided dictionary."""
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
                raise ValueError("openapi_source must be either a string (URL/file path) or a dictionary")
        except Exception as e:
            print(f"Error loading or parsing OpenAPI spec: {e}")
            raise

    def _extract_base_url(self):
        """Extracts the base URL from the spec's 'servers' block."""
        if "servers" in self.spec and self.spec["servers"]:
            self.base_url = self.spec["servers"][0]["url"]
        elif isinstance(self.openapi_source, str) and self.openapi_source.startswith(('http://', 'https://')):
            print("Warning: No 'servers' block in OpenAPI spec. Using source URL as base URL.")
            from urllib.parse import urlparse
            parsed_url = urlparse(self.openapi_source)
            self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        else:
            print("Warning: Could not determine base URL from spec. Using empty base URL.")
            self.base_url = ""
        
        self.base_url = self.base_url.rstrip('/')

    def _create_tools_from_spec(self):
        """Iterates through paths and methods in the spec to create tools."""
        paths = self.spec.get("paths", {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    self._create_and_register_tool(path, method, operation)

    def _create_and_register_tool(self, path: str, method: str, operation: dict):
        """Creates a single tool function and registers it with MCP."""
        op_id = operation.get("operationId")
        if not op_id:
            op_id = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
            print(f"Warning: No operationId found for {method.upper()} {path}. Using generated name: {op_id}")

        # The factory now returns a function that is complete with its
        # logic, signature, and docstring, ready for registration.
        tool_func = self._tool_function_factory(path, method, operation)
        tool_func.__name__ = op_id

        self.mcp.tool(name=op_id)(tool_func)
        print(f"  - Registered tool: {op_id}")

    def _tool_function_factory(
        self, path: str, method: str, operation: dict
    ) -> Callable[..., Coroutine[Any, Any, str]]:
        """
        A factory that creates a complete, ready-to-register async tool function
        for a given API operation, including its dynamic signature.
        """
        params_spec = operation.get("parameters", [])
        
        # Logic to map named parameters to their location (path, query, header, etc.)
        param_map = {p["name"]: p["in"] for p in params_spec}

        async def tool_function(**kwargs: Any) -> str:
            """
            Dynamically generated tool function.
            It receives named arguments from the MCP framework and maps them to the correct
            parts of the HTTP request (path, query, header, body).
            """
            request_context = getattr(self.mcp._mcp_server, '_request_context', {})

            headers: dict[str, str] = {"Accept": "application/json"}
            query_params_dict: dict[str, Any] = {}
            path_params_dict: dict[str, Any] = {}
            json_body: Any = None 

            if request_context:
                if 'authorization' in request_context.get('headers', {}):
                    headers['Authorization'] = request_context['headers']['authorization']
                query_params_dict.update(request_context.get('query_params', {}))
            
            # Map the provided keyword arguments to the correct request part
            for name, value in kwargs.items():
                if value is None:
                    continue
                
                param_location = param_map.get(name)

                if param_location in ("path", "text"):
                    path_params_dict[name] = value
                elif param_location == "query":
                    query_params_dict[name] = value
                elif param_location == "header":
                    headers[name] = str(value)
                elif name == "body":
                    json_body = value

            try:
                formatted_path = path.format(**path_params_dict)
                full_url = f"{self.base_url}{formatted_path}"
            except KeyError as e:
                return f"Error: Missing required path parameter: {e}"

            try:
                print(f"\nMaking API call for tool: {tool_function.__name__}")
                print(f"  - Method: {method.upper()}")
                print(f"  - URL: {full_url}")
                print(f"  - Query (Text values): {query_params_dict}")
                print(f"  - Headers (Text values): {headers}")
                if json_body:
                    print(f"  - Body (JSON object): {json.dumps(json_body, indent=2)}")

                response = await self.client.request(
                    method=method,
                    url=full_url,
                    headers=headers,
                    params=query_params_dict,
                    json=json_body
                )
                response.raise_for_status()
                try:
                    return json.dumps(response.json(), indent=2)
                except json.JSONDecodeError:
                    return response.text
            except httpx.HTTPStatusError as e:
                error_msg = f"API Error: {e.response.status_code} - {e.response.text}"
                print(f"ERROR: {error_msg}")
                return error_msg
            except Exception as e:
                error_msg = f"An unexpected error occurred: {str(e)}"
                print(f"ERROR: {error_msg}")
                return error_msg

        # ---- MODIFIED SECTION: DYNAMIC SIGNATURE GENERATION ----

        # Map OpenAPI types to primitive Python types for clear type hinting.
        # This guides the LLM to provide simple values, not nested JSON.
        openapi_type_to_python_type: dict[str, Type] = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
        }

        sig_params = []
        for param in params_spec:
            is_required = param.get("required", False)
            schema = param.get("schema", {})
            
            # Get the Python type. Default to 'str' if not specified, as it's the
            # most common type for path/query/header params. Fallback to Any for complex types.
            openapi_type = schema.get("type", "string")
            python_type = openapi_type_to_python_type.get(openapi_type, Any)

            sig_params.append(inspect.Parameter(
                name=param["name"],
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=inspect.Parameter.empty if is_required else None,
                annotation=python_type  # Use the specific Python type here
            ))

        # The 'body' parameter is still handled as 'Any' because it *is* a JSON object.
        if method.lower() not in ["get", "head"] and "requestBody" in operation:
            is_required = operation["requestBody"].get("required", False)
            sig_params.append(inspect.Parameter(
                name="body",
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=inspect.Parameter.empty if is_required else None,
                annotation=Any # 'Any' is correct for the request body
            ))
        
        # ---- END OF MODIFIED SECTION ----

        tool_function.__signature__ = inspect.Signature(parameters=sig_params)
        tool_function.__doc__ = self._generate_docstring(operation)
        
        return tool_function

    @staticmethod
    def _generate_docstring(operation: dict) -> str:
        """Generates a Python docstring from OpenAPI operation details."""
        summary = operation.get("summary", "No summary provided.")
        description = operation.get("description", "")
        doc = f"{summary}\n\n{description}\n\nArgs:\n"
        
        for param in operation.get("parameters", []):
            name, p_in = param.get("name"), param.get("in")
            p_desc = param.get("description", "No description.")
            p_type = param.get("schema", {}).get("type", "any")
            required = "required" if param.get("required", False) else "optional"
            doc += f"    {name} ({p_type}, {required}, in {p_in}): {p_desc}\n"

        if "requestBody" in operation:
            rb_desc = operation["requestBody"].get("description", "The request body.")
            required = "required" if operation["requestBody"].get("required", False) else "optional"
            doc += f"    body (dict | list, {required}): {rb_desc}\n"
            
        return doc