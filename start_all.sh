#!/bin/bash
# DevSkyy - Start All Services for Flawless Execution

echo "🚀 DevSkyy Enhanced Platform - Starting All Services"
echo "===================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "⬇️  Installing backend dependencies..."
    pip install -r backend/requirements.txt --quiet
else
    echo "✅ Using existing virtual environment"
    source venv/bin/activate
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install --silent && cd ..
else
    echo "✅ Frontend dependencies already installed"
fi

echo ""
echo "🌟 All systems ready for flawless execution!"
echo ""
echo "To start services:"
echo "  Backend:  uvicorn backend.server:app --host 0.0.0.0 --port 8001"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "🧪 Run tests: python -m pytest tests/ -v"
echo "🏗️  Build frontend: cd frontend && npm run build"