#!/bin/bash
# Quick start guide for Gmail integration

echo "========================================="
echo "Job Automation Agent - Gmail Setup"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "📝 Creating .env from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

echo ""
echo "📧 Gmail Setup Required"
echo "========================================="
echo ""
echo "1. Go to: https://myaccount.google.com/apppasswords"
echo "2. Select 'Mail' and 'Mac'"
echo "3. Generate 16-character app password"
echo "4. Copy password (remove spaces)"
echo ""
echo "5. Edit .env file and add:"
echo "   GMAIL_ADDRESS=your-email@gmail.com"
echo "   GMAIL_APP_PASSWORD=xxxxxxxxxxxx"
echo ""
read -p "Press Enter after updating .env file..."

echo ""
echo "🧪 Running Integration Tests..."
echo "========================================="
echo ""

# Activate virtual environment
if [ -d .venv ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found at .venv"
    exit 1
fi

# Run tests
python3 tests/test_gmail_integration.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ALL TESTS PASSED!"
    echo ""
    echo "🚀 Ready to Start Agent"
    echo "========================================="
    echo ""
    echo "Run: python3 orchestrator/agent.py"
    echo ""
else
    echo ""
    echo "❌ TESTS FAILED"
    echo ""
    echo "⚠️  Troubleshooting:"
    echo "   - Check GMAIL_ADDRESS is correct"
    echo "   - Check GMAIL_APP_PASSWORD (no spaces or typos)"
    echo "   - Verify 2FA is enabled on Gmail account"
    echo "   - Generate new App Password at https://myaccount.google.com/apppasswords"
    exit 1
fi
