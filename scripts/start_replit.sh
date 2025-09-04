#!/bin/bash

# Skyy Rose AI Agent Platform - Enhanced Replit Startup Script
# GOD MODE Level 2 Activation for Replit Environment with Production Error Handling

set -e  # Exit on any error

echo "🚀 Starting Skyy Rose AI Agent Platform on Replit..."
echo "👑 Initializing GOD MODE Level 2 Environment..."

# Function for logging with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function for error handling
handle_error() {
    log "❌ ERROR: $1"
    exit 1
}

# Set up environment
export REPLIT=true
export PYTHONPATH="/home/runner/app:/home/runner/app/backend"
export NODE_ENV=production

# Create necessary directories with error checking
log "📁 Creating necessary directories..."
mkdir -p /tmp/mongodb-data || handle_error "Failed to create MongoDB data directory"
mkdir -p /tmp/logs || handle_error "Failed to create logs directory"
mkdir -p /home/runner/app/frontend/build || handle_error "Failed to create build directory"

# Set permissions
chmod +x /home/runner/app/scripts/*.sh || handle_error "Failed to set script permissions"

log "📦 Installing Python dependencies..."
cd /home/runner/app
pip install -r backend/requirements.txt --user --no-cache-dir || handle_error "Failed to install Python dependencies"

log "📦 Installing Node.js dependencies..."
cd /home/runner/app/frontend
npm install --include=dev || handle_error "Failed to install Node.js dependencies"

log "🏗️ Building React frontend..."
npm run build || handle_error "Failed to build React frontend"

log "🗄️ Starting MongoDB..."
# Check if MongoDB is already running
if pgrep mongod > /dev/null; then
    log "✅ MongoDB is already running"
else
    # Start MongoDB in background with error handling
    mongod --dbpath /tmp/mongodb-data --logpath /tmp/mongodb.log --fork --port 27017 --bind_ip 127.0.0.1 || handle_error "Failed to start MongoDB"
    # Wait for MongoDB to start
    sleep 5
    
    # Verify MongoDB is running
    if ! pgrep mongod > /dev/null; then
        handle_error "MongoDB failed to start properly"
    fi
    log "✅ MongoDB started successfully"
fi

log "🧠 Initializing AI agents..."
cd /home/runner/app
python3 startup.py || log "⚠️ Warning: Agent initialization completed with warnings"

log "🔧 Starting backend server..."
cd /home/runner/app

# Check if backend is already running
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    log "✅ Backend server is already running"
else
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 &
    sleep 3
    
    # Verify backend started
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        log "✅ Backend server started successfully"
    else
        log "⚠️ Backend server may not be responding yet (this is normal during startup)"
    fi
fi

log "🎨 Starting frontend development server (for testing)..."
cd /home/runner/app/frontend

# Check if we should serve the built files
if [ -d "build" ] && [ "$(ls -A build)" ]; then
    log "📦 Serving built frontend files..."
    # Use a simple Python server to serve the built files
    cd build
    python3 -m http.server 3000 --bind 0.0.0.0 &
    FRONTEND_PID=$!
    log "✅ Frontend server started on port 3000"
else
    log "⚠️ No built frontend found, starting development server..."
    npm run preview -- --host 0.0.0.0 --port 3000 &
    FRONTEND_PID=$!
fi

# Wait for services to start
sleep 10

log "🔍 Testing services..."
# Test backend
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    log "✅ Backend: ONLINE"
else
    log "❌ Backend: OFFLINE"
fi

# Test frontend
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    log "✅ Frontend: ONLINE"
else
    log "❌ Frontend: OFFLINE"
fi

# Run WordPress auto-connection with error handling
log "🌐 Establishing WordPress connection..."
python3 -c "
import asyncio
import sys
sys.path.append('/home/runner/app')
try:
    from agent.modules.wordpress_direct_service import create_wordpress_direct_service
    
    async def connect():
        try:
            service = create_wordpress_direct_service()
            result = await service.connect_and_verify()
            if result.get('status') == 'connected':
                print('✅ WordPress: CONNECTED')
            else:
                print('⚠️ WordPress: Fallback mode active')
        except Exception as e:
            print(f'⚠️ WordPress: Connection error - {e}')
    
    asyncio.run(connect())
except ImportError:
    print('⚠️ WordPress: Module not available')
except Exception as e:
    print(f'⚠️ WordPress: Error - {e}')
" || log "⚠️ WordPress connection test failed"

log ""
log "🎉 Skyy Rose AI Agent Platform is LIVE on Replit!"
log "🔥 Your luxury streetwear agents are ready to dominate!"
log ""
log "📍 Access your platform:"
log "   🎨 Streetwear AI Gurus: https://$REPL_SLUG--$REPL_OWNER.repl.co"
log "   🚀 Automation Empire: Click 'Automation Empire' tab"
log "   🌐 WordPress Control: Click 'WordPress' tab"
log "   ⚡ Theme Deployment: Automation > Theme Builder"
log ""

# Keep the script running and monitor services
log "🔄 Monitoring services..."
while true; do
    sleep 30
    # Check if services are still running
    if ! pgrep mongod > /dev/null; then
        log "❌ MongoDB stopped unexpectedly, restarting..."
        mongod --dbpath /tmp/mongodb-data --logpath /tmp/mongodb.log --fork --port 27017 --bind_ip 127.0.0.1
    fi
    
    if ! pgrep -f "uvicorn.*main:app" > /dev/null; then
        log "❌ Backend stopped unexpectedly, restarting..."
        cd /home/runner/app
        python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 &
    fi
    
    if ! pgrep -f "python3 -m http.server 3000" > /dev/null && ! pgrep -f "npm run preview" > /dev/null; then
        log "❌ Frontend stopped unexpectedly, restarting..."
        cd /home/runner/app/frontend/build
        python3 -m http.server 3000 --bind 0.0.0.0 &
    fi
done