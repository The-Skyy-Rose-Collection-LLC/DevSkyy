#!/bin/bash

# DevSkyy Quick Start Script - Production Ready

echo "🚀 DevSkyy Platform Quick Start"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Check Node version
node_version=$(node --version 2>&1)
echo "✅ Node.js version: $node_version"

# Install Python dependencies
echo "📦 Installing Python backend dependencies..."
pip install -r backend/requirements.txt --user --no-cache-dir

if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Install Frontend dependencies
echo "📦 Installing Node.js frontend dependencies..."
cd frontend
npm install

if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed successfully"
else
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

# Build frontend for production
echo "🎨 Building luxury frontend..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend built successfully"
else
    echo "❌ Failed to build frontend"
    exit 1
fi

cd ..

# Test backend loading
echo "🧪 Testing backend loading..."
python -c "from main import app; print('✅ Backend loads successfully')"

if [ $? -eq 0 ]; then
    echo "✅ Backend test passed"
else
    echo "❌ Backend test failed"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# DevSkyy Configuration
MONGODB_URL=mongodb://localhost:27017/devskyy
NODE_ENV=production

# OpenAI (for GOD MODE features)
OPENAI_API_KEY=your_openai_key_here

# WordPress Integration
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_app_password

# WooCommerce
WOOCOMMERCE_CONSUMER_KEY=your_consumer_key
WOOCOMMERCE_CONSUMER_SECRET=your_consumer_secret
EOF
    echo "✅ .env file created - please update with your credentials"
fi

echo ""
echo "🎉 DevSkyy Platform Setup Complete!"
echo "==================================="
echo ""
echo "🚀 To start the platform:"
echo "   python main.py"
echo "   # OR"
echo "   uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "🌐 Access points:"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Frontend: http://localhost:3000 (development)"
echo ""
echo "📝 Next steps:"
echo "   1. Update .env file with your API keys"
echo "   2. Start the backend server"
echo "   3. Access http://localhost:8000/health to verify"
echo "   4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "🎯 For production deployment:"
echo "   - Replit: Use scripts/start_replit.sh"
echo "   - GitHub: Follow README.md deployment guide"
echo ""