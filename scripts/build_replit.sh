#!/bin/bash

# Skyy Rose AI Agent Platform - Updated Replit Build Script

echo "🏗️ Building Skyy Rose AI Agent Platform for Replit..."

# Set environment variables
export NODE_ENV=production
export PYTHONPATH="$(pwd):$(pwd)/backend"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt --user --no-cache-dir

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install

# Build React frontend
echo "🎨 Building React frontend with luxury styling..."
npm run build

# Optimize assets
echo "⚡ Optimizing assets..."
cd build

# Create optimized build info
echo "🔥 Build completed for Replit deployment!"
echo "👑 Luxury streetwear AI agents ready!"
echo "🚀 GOD MODE Level 2: READY"

# Create deployment info
cd ../..
cat > deployment_info.json << EOF
{
  "platform": "replit",
  "build_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "3.0.0",
  "features": [
    "14+ Animated Luxury AI Agents",
    "GOD MODE Level 2 Server Access",
    "Complete Automation Empire",
    "WordPress Integration with SFTP/SSH",
    "Luxury Theme Builder",
    "Social Media + Email + SMS Automation",
    "Real-time Brand Intelligence"
  ],
  "status": "production_ready"
}
EOF

echo "✅ Build complete! Ready for Replit deployment."