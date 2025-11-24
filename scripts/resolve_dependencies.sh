#!/bin/bash
set -e

echo "🔧 Resolving DevSkyy dependency conflicts..."
echo ""

# Critical: Upgrade pyopenssl for cryptography 46.x
echo "1. Upgrading pyopenssl to support cryptography 46.x..."
pip install 'pyopenssl>=24.2.1' --upgrade --quiet

# Critical: Downgrade protobuf for TensorFlow compatibility  
echo "2. Fixing protobuf version for TensorFlow..."
pip install 'protobuf>=4.25.5,<5.0.0' --force-reinstall --quiet

# High: Upgrade uvicorn and fastmcp dependencies
echo "3. Upgrading uvicorn..."
pip install 'uvicorn[standard]>=0.35.0' --upgrade --quiet

echo "4. Upgrading rich and websockets..."
pip install 'rich>=13.9.4' 'websockets>=15.0.1' --upgrade --quiet

# High: Upgrade aiobotocore
echo "5. Upgrading aiobotocore..."
pip install 'aiobotocore>=2.15.0' --upgrade --quiet

echo ""
echo "✅ Dependency resolution complete!"
echo ""
echo "Running pip check..."
pip check 2>&1 | head -20
