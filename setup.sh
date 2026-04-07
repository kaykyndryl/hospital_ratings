#!/bin/bash

# Hospital Ratings Setup Script
# Run this to set up the app for local development

set -e

echo "🏥 Hospital Ratings Setup"
echo "========================"

# Check Python exists
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python $(python3 --version) found"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the app, run:"
echo "  source .venv/bin/activate"
echo "  streamlit run app.py"
echo ""
echo "Then open http://localhost:8501 in your browser"
