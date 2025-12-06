#!/bin/bash

# FAT Simulator launch script

echo "==================================="
echo "FAT16 Simulator - Forensic Tool"
echo "==================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv

    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✓ Installation complete"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Launch application
echo "🚀 Launching FAT Simulator..."
echo ""
python fat_simulator_gui.py

# Deactivate environment
deactivate
