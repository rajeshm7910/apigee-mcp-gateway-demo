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
import shutil
import json
import asyncio
from fastapi import HTTPException
from google.auth import default
from google.auth.transport.requests import Request

# Load environment variables
load_dotenv()


class RegisterRequest(BaseModel):
    proxy_name: str

class Flow(BaseModel):
    name: str
    description: Optional[str]
    condition: Optional[str]
    request_steps: List[str] = []
    response_steps: List[str] = []

class ProxyInfo(BaseModel):
    base_path: str
    flows: List[Flow]

def extract_path_and_method(condition: str) -> tuple[str, str]:
    """Extract path and HTTP method from Apigee condition"""
    path_match = re.search(r'proxy\.pathsuffix MatchesPath "([^"]+)"', condition)
    method_match = re.search(r'request\.verb = "([^"]+)"', condition)
    
    path = path_match.group(1) if path_match else ""
    method = method_match.group(1) if method_match else ""
    
    return path, method

def generate_openapi_spec(proxy_info: ProxyInfo) -> Dict:
    """Generate OpenAPI specification from proxy flows"""
    paths = {}
    
    for flow in proxy_info.flows:
        if not flow.condition:
            continue
            
        path, method = extract_path_and_method(flow.condition)
        if not path or not method:
            continue
            
        # Convert path parameters from Apigee format to OpenAPI format
        openapi_path = path.replace("/*", "/{id}")
        
        if openapi_path not in paths:
            paths[openapi_path] = {}
            
        operation = {
            "summary": flow.description or flow.name,
            "operationId": flow.name,
            "responses": {
                "200": {
                    "description": "Successful operation",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "400": {
                    "description": "Bad request"
                },
                "404": {
                    "description": "Not found"
                },
                "500": {
                    "description": "Internal server error"
                }
            }
        }
        
        # Add request body for POST/PATCH operations
        if method in ["POST", "PATCH"]:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
        # Add path parameters for paths with {id}
        if "{id}" in openapi_path:
            operation["parameters"] = [{
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string"
                }
            }]
            
        paths[openapi_path][method.lower()] = operation
    
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "API Specification",
            "version": "1.0.0",
            "description": "Generated from Apigee proxy flows"
        },
        "paths": paths,
        "servers": [
            {
                "url": proxy_info.base_path,
                "description": "API Server"
            }
        ]
    }
    
    return openapi_spec

def get_apigee_token():
    """Get OAuth token using Google Application Default Credentials"""
    credentials, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def get_proxy_deployment(org: str, env: str, proxy_name: str) -> str:
    """Get the latest deployment version of a proxy"""
    token = get_apigee_token()
    url = f"https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/apis/{proxy_name}/deployments"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to get proxy deployment")
    
    deployments = response.json()
    if not deployments.get("deployments"):
        raise HTTPException(status_code=404, detail="No deployments found")
    
    return deployments["deployments"][0]["revision"]

def download_proxy_bundle(org: str, proxy_name: str, revision: str) -> bytes:
    """Download the proxy bundle for a specific revision"""
    token = get_apigee_token()
    url = f"https://apigee.googleapis.com/v1/organizations/{org}/apis/{proxy_name}/revisions/{revision}?format=bundle"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to download proxy bundle")
    
    return response.content

def extract_proxy_xml(bundle_content: bytes) -> str:
    """Extract the proxy XML from the bundle"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save the bundle to a temporary file
        bundle_path = os.path.join(temp_dir, "bundle.zip")
        with open(bundle_path, "wb") as f:
            f.write(bundle_content)
        
        # Extract the bundle
        with zipfile.ZipFile(bundle_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find and read the proxy XML file
        apiproxy_dir = os.path.join(temp_dir, "apiproxy")
        proxy_xml_path = os.path.join(apiproxy_dir, "proxies", "default.xml")
        
        if not os.path.exists(proxy_xml_path):
            raise HTTPException(status_code=404, detail="Proxy XML not found in bundle")
        
        with open(proxy_xml_path, 'r') as f:
            return f.read()

def parse_proxy_xml(xml_content: str) -> ProxyInfo:
    """Parse the proxy XML and extract flows and base path"""
    root = ET.fromstring(xml_content)
    
    # Get base path
    base_path = root.find(".//BasePath").text if root.find(".//BasePath") is not None else ""
    
    # Parse flows
    flows = []
    for flow in root.findall(".//Flow"):
        flow_info = Flow(
            name=flow.get("name", ""),
            description=flow.find("Description").text if flow.find("Description") is not None else None,
            condition=flow.find("Condition").text if flow.find("Condition") is not None else None,
            request_steps=[step.find("Name").text for step in flow.findall(".//Request/Step")],
            response_steps=[step.find("Name").text for step in flow.findall(".//Response/Step")]
        )
        flows.append(flow_info)
    
    return ProxyInfo(base_path=base_path, flows=flows)


def create_openapi_spec(proxy_name: str):
    try:
        org = os.getenv("APIGEE_ORG")
        env = os.getenv("APIGEE_ENV")
        
        if not org or not env:
            raise HTTPException(status_code=500, detail="APIGEE_ORG or APIGEE_ENV not configured")
        
        # Get latest deployment version
        revision = get_proxy_deployment(org, env, proxy_name)
        print(f"Revision: {revision}")
        
        # Download proxy bundle
        bundle_content = download_proxy_bundle(org, proxy_name, revision)
        print("Bundle downloaded successfully")
        
        # Extract and parse proxy XML
        proxy_xml = extract_proxy_xml(bundle_content)
        print(f"Proxy XML extracted")
        
        # Parse proxy XML
        proxy_info = parse_proxy_xml(proxy_xml)
        print(f"Proxy Info: {proxy_info}")
        
        # Generate OpenAPI specification
        openapi_spec = generate_openapi_spec(proxy_info)
        
        return openapi_spec
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

