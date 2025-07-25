# utils.py

from pydantic import BaseModel
import requests
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dotenv import load_dotenv
import re
import zipfile
import io
import tempfile
import yaml
from google.auth import default
from google.auth.transport.requests import Request

# Load environment variables from .env file
load_dotenv()

class Flow(BaseModel):
    name: str
    description: Optional[str]
    condition: Optional[str]

class ProxyInfo(BaseModel):
    base_path: str
    flows: List[Flow]

def extract_path_and_method(condition: str) -> tuple[str, str]:
    """Extract path and HTTP method from Apigee condition string."""
    path_match = re.search(r'proxy\.pathsuffix MatchesPath "([^"]+)"', condition)
    method_match = re.search(r'request\.verb = "([^"]+)"', condition)
    
    path = path_match.group(1) if path_match else ""
    method = method_match.group(1) if method_match else ""
    
    # Convert Apigee path wildcards to OpenAPI format
    path = re.sub(r'/\*\*', '/{proxy+}', path) # Catch-all
    path = re.sub(r'/\*', '/{id}', path)      # Single path segment
    
    return path, method

def generate_openapi_spec(proxy_info: ProxyInfo, proxy_name: str) -> Dict:
    """Generate a basic OpenAPI specification from proxy flows."""
    paths = {}
    
    for flow in proxy_info.flows:
        if not flow.condition:
            continue
            
        path, method = extract_path_and_method(flow.condition)
        if not path or not method:
            continue
            
        if path not in paths:
            paths[path] = {}
            
        operation = {
            "summary": flow.description or flow.name,
            "operationId": flow.name.replace("-", "_"), # Ensure valid function name
            "responses": {
                "200": {"description": "Successful operation"},
                "400": {"description": "Bad request"},
                "404": {"description": "Not found"},
                "500": {"description": "Internal server error"}
            }
        }

        # Add path parameters if they exist in the path template
        path_params = re.findall(r'\{(\w+)\}', path)
        if path_params:
            operation["parameters"] = [
                {"name": param, "in": "path", "required": True, "schema": {"type": "string"}}
                for param in path_params
            ]

        paths[path][method.lower()] = operation
    
    api_description = next((flow.description for flow in proxy_info.flows if flow.description), f"API specification for {proxy_name}")
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": f"{proxy_name} API",
            "version": "1.0.0",
            "description": api_description
        },
        "paths": paths
    }

def get_apigee_token(access_token: Optional[str] = None) -> str:
    """Get OAuth token using provided access token or Google Application Default Credentials."""
    if access_token:
        return access_token
    try:
        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        raise ValueError(f"Failed to get Apigee token. Ensure you have authenticated with gcloud. Error: {e}")

def get_proxy_deployment(org: str, env: str, proxy_name: str, access_token: Optional[str] = None) -> str:
    """Get the latest deployment revision of a proxy."""
    token = get_apigee_token(access_token)
    url = f"https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/apis/{proxy_name}/deployments"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        raise ValueError(f"Failed to get proxy deployment (Status {response.status_code}): {response.text}")
    
    deployments = response.json().get("deployments")
    if not deployments:
        raise ValueError(f"No deployments found for proxy '{proxy_name}' in environment '{env}'.")
    
    return deployments[0]["revision"]

def download_proxy_bundle(org: str, proxy_name: str, revision: str, access_token: Optional[str] = None) -> bytes:
    """Download the proxy bundle for a specific revision."""
    token = get_apigee_token(access_token)
    url = f"https://apigee.googleapis.com/v1/organizations/{org}/apis/{proxy_name}/revisions/{revision}?format=bundle"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        raise ValueError(f"Failed to download proxy bundle (Status {response.status_code}): {response.text}")
    return response.content

def extract_proxy_xml(bundle_content: bytes) -> str:
    """Extract the main proxy XML file content from the bundle zip."""
    with io.BytesIO(bundle_content) as bundle_io, zipfile.ZipFile(bundle_io, 'r') as zip_ref:
        proxy_files = [f for f in zip_ref.namelist() if f.startswith('apiproxy/proxies/') and f.endswith('.xml')]
        if not proxy_files:
            raise ValueError("No proxy endpoint XML file found in the 'apiproxy/proxies/' directory of the bundle.")
        with zip_ref.open(proxy_files[0]) as xml_file:
            return xml_file.read().decode('utf-8')

def parse_proxy_xml(xml_content: str) -> ProxyInfo:
    """Parse the proxy XML and extract flows and base path."""
    root = ET.fromstring(xml_content)
    base_path = root.find(".//BasePath").text if root.find(".//BasePath") is not None else ""
    flows = [
        Flow(
            name=flow.get("name", ""),
            description=flow.find("Description").text if flow.find("Description") is not None else None,
            condition=flow.find("Condition").text if flow.find("Condition") is not None else None
        )
        for flow in root.findall(".//Flow")
    ]
    return ProxyInfo(base_path=base_path, flows=flows)


def proxy_spec_for_mcp(proxy_name: str, access_token: Optional[str] = None) -> dict:
    """
    Main utility function to fetch, parse, and generate the configuration for an Apigee proxy.

    It can either generate an OpenAPI spec from the proxy flows or load a specified one from a file.
    """
    try:
        org = os.getenv("APIGEE_ORG")
        env = os.getenv("APIGEE_ENV")
        if not org or not env:
            raise ValueError("APIGEE_ORG and APIGEE_ENV environment variables must be set.")
        
        print(f"-> Fetching spec for proxy '{proxy_name}' in org '{org}', env '{env}'...")
        
        # If PROXY_OPENAPI_SPEC is set, load it directly and skip generation
        if openapi_spec_path := os.getenv("PROXY_OPENAPI_SPEC"):
            print(f"-> Loading OpenAPI spec from file: {openapi_spec_path}")
            try:
                with open(openapi_spec_path, 'r') as f:
                    openapi_spec = yaml.safe_load(f)
                # We still need the base path from the proxy itself
                revision = get_proxy_deployment(org, env, proxy_name, access_token)
                bundle_content = download_proxy_bundle(org, proxy_name, revision, access_token)
                proxy_xml = extract_proxy_xml(bundle_content)
                proxy_info = parse_proxy_xml(proxy_xml)
                base_path = proxy_info.base_path
                revision_info = revision
            except (yaml.YAMLError, FileNotFoundError) as e:
                raise ValueError(f"Failed to read or parse specified OpenAPI spec file: {e}")
        else:
            # Generate the spec from the proxy bundle
            print("-> Generating OpenAPI spec from proxy bundle...")
            revision = get_proxy_deployment(org, env, proxy_name, access_token)
            bundle_content = download_proxy_bundle(org, proxy_name, revision, access_token)
            proxy_xml = extract_proxy_xml(bundle_content)
            proxy_info = parse_proxy_xml(proxy_xml)
            openapi_spec = generate_openapi_spec(proxy_info, proxy_name)
            base_path = proxy_info.base_path
            revision_info = revision

        return {
            "proxy_name": proxy_name,
            "revision": revision_info,
            "base_path": base_path,
            "openapi_spec": openapi_spec
        }
        
    except Exception as e:
        # Wrap any exception in a clear error message
        print(f"Error in proxy_spec_for_mcp: {e}")
        raise