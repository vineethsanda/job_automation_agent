#!/bin/bash

# Quick start script for Job Automation Agent
# Usage: ./start_agent.sh [mode]
# Modes: full, orchestrator, test

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  .env file not found. Copy .env.example to .env and configure."
    exit 1
fi

# Activate virtual environment
if [ ! -d .venv ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    playwright install chromium
    echo "✅ Virtual environment ready"
else
    source .venv/bin/activate
fi

MODE=${1:-orchestrator}

echo "🚀 Starting Job Automation Agent ($MODE mode)"
echo "=================================================="

case $MODE in
    full)
        echo ""
        echo "Full mode: Starting all services"
        echo "You need multiple terminals for this:"
        echo ""
        echo "Terminal 1: ollama serve"
        echo "Terminal 2: python3 mcp_servers/gmail_mcp/server.py"
        echo "Terminal 3: python3 mcp_servers/linkedin_mcp/server.py"
        echo "Terminal 4: python3 mcp_servers/jobportal_mcp/server.py"
        echo "Terminal 5: python3 orchestrator/agent.py"
        echo ""
        echo "Or run: ./start_agent.sh orchestrator"
        ;;

    orchestrator)
        echo ""
        echo "Starting orchestrator (mock MCP mode)..."
        echo "Enter master password when prompted"
        echo ""
        export GMAIL_ADDRESS="${GMAIL_ADDRESS:-}"
        export GMAIL_APP_PASSWORD="${GMAIL_APP_PASSWORD:-}"
        python3 orchestrator/agent.py
        ;;

    test)
        echo ""
        echo "Running tests..."
        python3 -m pytest tests/ -v
        ;;

    *)
        echo "Unknown mode: $MODE"
        echo "Usage: $0 [full|orchestrator|test]"
        exit 1
        ;;
esac
