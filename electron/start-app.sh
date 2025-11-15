#!/bin/bash

echo "🚀 Starting WTI Smart Trader Desktop App..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 ist nicht installiert!"
    echo "   Installieren Sie Python von https://www.python.org"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js ist nicht installiert!"
    echo "   Installieren Sie Node.js von https://nodejs.org"
    exit 1
fi

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB läuft nicht!"
    echo "   Starten Sie MongoDB mit: brew services start mongodb-community"
    echo ""
fi

# Check if yarn is installed
if ! command -v yarn &> /dev/null; then
    echo "📦 Yarn wird installiert..."
    npm install -g yarn
fi

# Install backend dependencies if needed
if [ ! -d "../backend/venv" ]; then
    echo "📦 Installing Backend Dependencies..."
    cd ../backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ../electron
fi

# Install electron dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Electron Dependencies..."
    yarn install
fi

echo ""
echo "✅ All dependencies ready!"
echo "🎯 Starting Electron App..."
echo ""

# Start the app
yarn start
