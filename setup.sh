#!/bin/bash
# Setup script for ClawBot

echo "🔧 Setting up ClawBot..."

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "Run agents with:"
echo "  source venv/bin/activate"
echo "  python stock_agent.py AAPL"
