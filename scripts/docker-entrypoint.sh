#!/bin/bash
set -e

# Atlas-G Protocol - Intelligent Entrypoint
# Switches between Web Portfolio mode and MCP Server mode based on environment.

if [ -n "$PORT" ]; then
    echo "🌐 Starting Portfolio Web Engine on port $PORT..."
    # Run the FastAPI/Uvicorn application
    exec python -m uvicorn backend.main:application --host 0.0.0.0 --port "$PORT"
else
    echo "🔒 Starting MCP Protocol Engine (stdio)..."
    # Run the MCP server directly for Glama/Registry inspection
    exec python -m backend.mcp_server
fi
