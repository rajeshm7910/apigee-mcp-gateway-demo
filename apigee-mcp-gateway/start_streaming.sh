cd fastmcp-streaming
uvicorn server:get_app --host 0.0.0.0 --port 8080 --log-level debug
