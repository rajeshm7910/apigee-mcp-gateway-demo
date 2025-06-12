# Apigee MCP Server

A FastAPI-based server that implements the Model Control Protocol (MCP) for Apigee API proxies. This server acts as a bridge between AI models and Apigee APIs, enabling seamless integration and control of API proxies through the MCP interface.

This server creates MCP tools by analyzing the flows defined in your Apigee proxy. It works best with proxies that have explicit flow definitions, such as those generated from OpenAPI specifications. For simple passthrough proxies without defined flows, the MCP functionality will be limited since there are no specific flows to map to tools.

## Features

- FastAPI-based MCP server implementation
- Integration with Apigee API proxies
- OpenAPI specification support
- SSE (Server-Sent Events) transport for real-time communication
- Automatic tool generation from OpenAPI specifications

## Prerequisites

- Python 3.8 or higher
- Apigee API proxy access
- Google Cloud credentials (apigee-sa.json)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd apigee-mcp-server
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Authentication:
   - Option 1: Generate a token using gcloud CLI:
     ```bash
     gcloud auth application-default login
     ```
   - Option 2: Set credentials file path in environment:
     ```bash 
     export GOOGLE_APPLICATION_CREDENTIALS="apigee-sa.json"
     ```
   - Option 3: Add credentials path to .env file:
     ```env
     GOOGLE_APPLICATION_CREDENTIALS=apigee-sa.json
     ```

2. Create/Update `.env` file with the following variables:
```env
# Organization name in Apigee
export APIGEE_ORG="bap-amer-west-demo1"
# Environment name in Apigee
export APIGEE_ENV="default-dev"
# Path to service account credentials file (uncomment if using)
#export GOOGLE_APPLICATION_CREDENTIALS="./resources/apigee-sa.json"
# Path to OpenAPI specification file for the API proxy. This is optional, if you don't specify it will read all conditional flows in Proxy and genereate spec for you.
export PROXY_OPENAPI_SPEC="./resources/hipster-openapi.yaml"
# Name of the API proxy to use
export PROXY_NAME="Hipster-Products-API"
#export PROXY_NAME=retail-v1

# Base URL for the Apigee runtime environment
export APIGEE_RUNTIME_URL="https://bap-amer-west-demo1.cs.apigee.net"

```

## Usage

Run the server using the provided script:
```bash
./run.sh
```

Or run directly with Python:
```bash
python main.py --proxy-name "your-proxy-name" --base-url "your-runtime-url"
```

Command-line arguments:
- `--proxy-name`: Name of the Apigee proxy to use (default: from PROXY_NAME env var)
- `--base-url`: Base URL for the Apigee runtime (default: from APIGEE_RUNTIME_URL env var)
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to listen on (default: 8080)
- `--access-token`: Access token for Apigee API authentication (optional)

The server will start and expose:
- SSE endpoint at `/sse`
- Message handling at `/messages/`

## Project Structure

- `main.py` - Main server implementation with MCP and SSE integration
- `utils.py` - Utility functions for proxy specification and MCP integration
- `openapi_generator.py` - OpenAPI specification to MCP tools generator
- `requirements.txt` - Project dependencies
- `run.sh` - Convenience script for running the server
- `apigee-sa.json` - Apigee service account credentials

## Dependencies

- fastapi==0.104.1
- uvicorn==0.24.0
- pydantic==2.4.2
- requests==2.31.0
- google-auth==2.23.3
- google-auth-oauthlib==1.1.0
- google-auth-httplib2==0.1.1
- fastmcp==0.1.0
- pyyaml==6.0.1
- python-dotenv==1.0.0
- starlette==0.27.0

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]

## Support

For support, please [add your support contact information]
