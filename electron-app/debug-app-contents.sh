#!/bin/bash

echo "🔍 Debugging Booner Trade App Contents"
echo "======================================"
echo ""

APP_PATH="/Applications/Booner Trade.app/Contents/Resources/app"

echo "1️⃣ Checking if app exists..."
if [ ! -d "/Applications/Booner Trade.app" ]; then
    echo "❌ App not found!"
    exit 1
fi
echo "✅ App found"
echo ""

echo "2️⃣ Checking Resources structure..."
ls -la "/Applications/Booner Trade.app/Contents/Resources/"
echo ""

echo "3️⃣ Checking app folder..."
if [ -d "$APP_PATH" ]; then
    echo "✅ app folder exists"
    ls -la "$APP_PATH/"
else
    echo "❌ app folder missing!"
fi
echo ""

echo "4️⃣ Checking frontend build..."
if [ -d "$APP_PATH/frontend/build" ]; then
    echo "✅ Frontend build folder exists"
    ls -la "$APP_PATH/frontend/build/" | head -n 20
    
    if [ -f "$APP_PATH/frontend/build/index.html" ]; then
        echo "✅ index.html exists"
        echo "Size: $(wc -c < "$APP_PATH/frontend/build/index.html") bytes"
    else
        echo "❌ index.html MISSING!"
    fi
else
    echo "❌ Frontend build folder MISSING!"
fi
echo ""

echo "5️⃣ Checking backend..."
if [ -f "$APP_PATH/backend/server.py" ]; then
    echo "✅ Backend exists"
else
    echo "❌ Backend missing!"
fi
echo ""

echo "6️⃣ Checking MongoDB..."
if [ -d "$APP_PATH/mongodb" ]; then
    echo "✅ MongoDB folder exists"
    ls -la "$APP_PATH/mongodb/bin/" 2>/dev/null | head -n 5
else
    echo "❌ MongoDB folder missing!"
fi
echo ""

echo "7️⃣ Checking Python..."
if [ -d "$APP_PATH/python" ]; then
    echo "✅ Python folder exists"
    "$APP_PATH/python/bin/python3" --version 2>/dev/null || echo "⚠️  Python not executable"
else
    echo "❌ Python folder missing!"
fi
echo ""

echo "📊 Summary:"
echo "==========="
echo "App Path: $APP_PATH"
echo ""
echo "Next steps:"
echo "1. If frontend/build is missing → Rebuild with 'cd frontend && yarn build'"
echo "2. If anything else is missing → Re-run build script"
