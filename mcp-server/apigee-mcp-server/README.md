# Apigee MCP Server

A FastAPI-based server that implements the Model Control Protocol (MCP) for Apigee API proxies. This server acts as a bridge between AI models and Apigee APIs, enabling seamless integration and control of API proxies through the MCP interface.

This server creates MCP tools by analyzing the flows defined in your Apigee proxy. It works best with proxies that have explicit flow definitions, such as those generated from OpenAPI specifications. For simple passthrough proxies without defined flows, the MCP functionality will be limited since there are no specific flows to map to tools.

## Features

- FastAPI-based MCP server implementation
- Integration with Apigee API proxies
- OpenAPI specification support
- SSE (Server-Sent Events) and HTTP transport for real-time communication
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

1. Create/Update `.env` file with the following variables:

```bash
export PROXY_OPENAPI_SPEC="./resources/hipster-openapi.yaml"
export APIGEE_RUNTIME_URL="https://bap-amer-west-demo1.cs.apigee.net"
```

## Usage

Run the server using the provided script:
```bash
./local_start.sh {start|stop}
```


## Dependencies

- fastapi

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
