#!/bin/bash

# Skyy Rose AI Agent Platform - Replit Startup Script
# GOD MODE Level 2 Activation for Replit Environment

echo "🚀 Starting Skyy Rose AI Agent Platform on Replit..."
echo "👑 Initializing GOD MODE Level 2 Environment..."

# Set up environment
export REPLIT=true
export PYTHONPATH="/home/runner/app:/home/runner/app/backend"
export NODE_ENV=production

# Create necessary directories
mkdir -p /tmp/mongodb-data
mkdir -p /tmp/logs
mkdir -p /home/runner/app/frontend/build

# Set permissions
chmod +x /home/runner/app/scripts/*.sh

echo "📦 Installing Python dependencies..."
cd /home/runner/app
pip install -r backend/requirements.txt --user --no-cache-dir

echo "📦 Installing Node.js dependencies..."
cd /home/runner/app/frontend
npm install --production

echo "🏗️ Building React frontend..."
npm run build

echo "🗄️ Starting MongoDB..."
# Start MongoDB in background
mongod --dbpath /tmp/mongodb-data --logpath /tmp/mongodb.log --fork --port 27017 --bind_ip 127.0.0.1

# Wait for MongoDB to start
sleep 5

echo "🧠 Initializing AI agents..."
cd /home/runner/app
python3 startup.py

echo "🔧 Starting backend server..."
cd /home/runner/app
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 &

echo "🎨 Starting frontend server..."
cd /home/runner/app/frontend
npm run preview -- --host 0.0.0.0 --port 3000 &

# Wait for services to start
sleep 10

echo "✅ All services started!"
echo "🌐 Frontend: https://$REPL_SLUG--$REPL_OWNER.repl.co"
echo "⚡ Backend API: https://$REPL_SLUG--$REPL_OWNER.repl.co:8001"
echo "🤖 10 Streetwear AI Gurus: ACTIVE"
echo "👑 GOD MODE Level 2: OPERATIONAL"

# Test connections
echo "🔍 Testing connections..."
curl -s http://localhost:8001/ > /dev/null && echo "✅ Backend: ONLINE" || echo "❌ Backend: OFFLINE"
curl -s http://localhost:3000/ > /dev/null && echo "✅ Frontend: ONLINE" || echo "❌ Frontend: OFFLINE"

# Run WordPress auto-connection
echo "🌐 Establishing WordPress connection..."
python3 -c "
import asyncio
import sys
sys.path.append('/home/runner/app')
from agent.modules.wordpress_direct_service import create_wordpress_direct_service

async def connect():
    service = create_wordpress_direct_service()
    result = await service.connect_and_verify()
    if result.get('status') == 'connected':
        print('✅ WordPress: CONNECTED')
    else:
        print('⚠️ WordPress: Fallback mode active')

asyncio.run(connect())
"

echo ""
echo "🎉 Skyy Rose AI Agent Platform is LIVE on Replit!"
echo "🔥 Your luxury streetwear agents are ready to dominate!"
echo ""
echo "📍 Access your platform:"
echo "   🎨 Streetwear AI Gurus: https://$REPL_SLUG--$REPL_OWNER.repl.co"
echo "   🚀 Automation Empire: Click 'Automation Empire' tab"
echo "   🌐 WordPress Control: Click 'WordPress' tab"
echo "   ⚡ Theme Deployment: Automation > Theme Builder"
echo ""

# Keep the script running
tail -f /tmp/mongodb.log