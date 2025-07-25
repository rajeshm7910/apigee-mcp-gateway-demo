#!/bin/bash

case "$1" in
  start)
    # Set up Python virtual environment
    if [ ! -d "venv" ]; then
      python3 -m venv venv
      echo "Created virtual environment in ./venv"
    fi
    # Activate virtual environment
    source venv/bin/activate
    echo "Activated virtual environment."
    # Install requirements
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Installed requirements from requirements.txt."
    # Start HTTP server
    nohup python3 api_to_tools_http.py > http_server.log 2>&1 &
    echo "Started HTTP server on port 4200 (log: http_server.log)"
    # Start SSE server
    nohup python3 api_to_tools_sse.py > sse_server.log 2>&1 &
    echo "Started SSE server on port 4201 (log: sse_server.log)"
    ;;
  stop)
    # Stop HTTP server
    pkill -f "python3 api_to_tools_http.py"
    echo "Stopped HTTP server (api_to_tools_http.py)"
    # Stop SSE server
    pkill -f "python3 api_to_tools_sse.py"
    echo "Stopped SSE server (api_to_tools_sse.py)"
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac 