#!/bin/bash
set -e

echo "🧪 Testing Electron App Locally (Development Mode)"
echo ""

# 1. Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node dependencies..."
    yarn install
fi

# 2. Check if backend is running
if ! curl -s http://localhost:8001/api/ping > /dev/null; then
    echo "⚠️  Backend is not running!"
    echo "Please start backend first:"
    echo "  cd /app/backend"
    echo "  python3 server.py"
    echo ""
    exit 1
fi

# 3. Check if frontend is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "⚠️  Frontend is not running!"
    echo "Please start frontend first:"
    echo "  cd /app/frontend"
    echo "  yarn start"
    echo ""
    exit 1
fi

echo "✅ Backend & Frontend are running"
echo ""
echo "🚀 Starting Electron in development mode..."
echo "   (This will open the app in a window)"
echo ""

# 4. Start Electron
NODE_ENV=development yarn start
