#!/bin/bash
# DevSkyy - Setup Clean Python Environment for Google Gemini

echo "🔧 Setting up clean Python environment for DevSkyy..."
echo ""

# Navigate to DevSkyy directory
cd /home/user/DevSkyy

# Create virtual environment
echo "1️⃣ Creating virtual environment..."
python3 -m venv venv

# Activate it
echo "2️⃣ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "3️⃣ Upgrading pip..."
pip install --upgrade pip

# Install all required packages in clean environment
echo "4️⃣ Installing AI model packages..."
pip install \
    anthropic \
    openai \
    google-generativeai \
    python-dotenv \
    transformers \
    torch

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "📝 To use DevSkyy with full multi-model support:"
echo ""
echo "   # Activate the environment:"
echo "   source venv/bin/activate"
echo ""
echo "   # Run your scripts:"
echo "   python test_multi_model.py"
echo ""
echo "   # Deactivate when done:"
echo "   deactivate"
echo ""
