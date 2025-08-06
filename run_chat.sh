#!/bin/bash
# OSFI CAR Chat Agent Launcher

echo "🚀 Starting OSFI CAR Interactive Agent..."

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not detected. Activating .venv..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "❌ Virtual environment .venv not found. Please create one:"
        echo "python3 -m venv .venv"
        echo "source .venv/bin/activate"
        exit 1
    fi
fi

# Check if in correct directory
if [ ! -f "osfi_car_chat.py" ]; then
    echo "❌ Please run this script from the pdf directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check dependencies quietly
echo "📦 Checking dependencies..."
python -c "
import sys
required = ['langchain', 'langchain_community', 'pypdf', 'google', 'langgraph', 'tiktoken', 'openai']
missing = []
for pkg in required:
    try:
        if pkg == 'google':
            __import__('google.generativeai')
        else:
            __import__(pkg.replace('-', '_'))
    except ImportError:
        missing.append(pkg)

if missing:
    print('❌ Missing packages. Please install them manually:')
    print('pip install langchain langchain-community pypdf google-generativeai langgraph tiktoken openai')
    sys.exit(1)
else:
    print('✅ All dependencies available')
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Run the agent
echo "🤖 Launching OSFI CAR Agent..."
python osfi_car_chat.py --pdf-dir "osfi car"