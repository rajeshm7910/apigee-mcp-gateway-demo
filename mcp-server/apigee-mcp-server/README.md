# Apigee MCP Server

A FastAPI-based server that implements the Model Control Protocol (MCP) for Apigee API proxies. This server acts as a bridge between AI models and Apigee APIs, enabling seamless integration and control of API proxies through the MCP interface.

This server creates MCP tools by analyzing the flows defined in your Apigee proxy. It works best with proxies that have explicit flow definitions, such as those generated from OpenAPI specifications. For simple passthrough proxies without defined flows, the MCP functionality will be limited since there are no specific flows to map to tools.


## Features

- FastAPI-based MCP server implementation
- Integration with Apigee API proxies
- OpenAPI specification support

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
2. Create/Update  `.env` file with the following variables:
```env
APIGEE_RUNTIME_URL=https://your-apigee-runtime-url
PROXY_NAME=your-proxy-name
```

## Usage

Run the server:
```bash
python server.py
```

The server will start on the default port and expose the MCP endpoint at `/mcp`.

## Project Structure

- `server.py` - Main server implementation
- `utils.py` - Utility functions for proxy specification and MCP integration
- `requirements.txt` - Project dependencies
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
