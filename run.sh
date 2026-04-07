#!/bin/bash
# Quick start script for Hospital Rating App

echo "🏥 Hospital Star Rating App - Quick Start"
echo "=========================================="
echo ""

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "🚀 Starting Streamlit app..."
echo "   The app will open at: http://localhost:8501"
echo ""
echo "   To stop the app, press Ctrl+C"
echo ""

streamlit run app.py
