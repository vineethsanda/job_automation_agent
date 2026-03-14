#!/bin/bash

# Setup script for Job Automation Agent
# Initializes environment and dependencies

set -e

echo "🚀 Job Automation Agent - Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    echo "❌ Python 3.11+ required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Check for Ollama
echo ""
echo "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Install from https://ollama.ai"
    exit 1
else
    echo "✓ Ollama found at: $(which ollama)"
fi

# Create virtual environment
echo ""
echo "Setting up Python environment..."
if [ ! -d venv ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✓ Dependencies installed"

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
python3 -m playwright install chromium --quiet
echo "✓ Playwright browsers installed"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p ~/.llm_agent
echo "✓ Directories created"

# Setup env file
echo ""
echo "Checking environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  .env created from .env.example"
    echo "Please edit .env with your Gmail and LinkedIn credentials:"
    echo "  - GMAIL_ADDRESS"
    echo "  - GMAIL_APP_PASSWORD (get from myaccount.google.com/apppasswords)"
    echo "  - LINKEDIN_EMAIL (optional)"
    echo "  - LINKEDIN_PASSWORD (optional)"
else
    echo "✓ .env configuration found"
fi

# Setup metadata
echo ""
echo "Setting up metadata..."
if [ ! -f ~/.llm_agent/metadata.json ]; then
    echo "Launching metadata setup wizard..."
    python3 setup_metadata.py
else
    echo "✓ Metadata already configured"
    echo "  To reconfigure: rm ~/.llm_agent/metadata.json && python3 setup_metadata.py"
fi

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Gmail and LinkedIn credentials"
echo "2. Ensure Ollama is installed: brew install ollama"
echo "3. Download Llama model: ollama pull llama2:latest"
echo "4. Start orchestrator: ./start_agent.sh orchestrator"
echo ""
echo "For detailed setup instructions, see README.md"
echo "=================================================="
