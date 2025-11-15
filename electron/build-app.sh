#!/bin/bash

echo "🔨 Building WTI Smart Trader Desktop App"
echo "========================================="
echo ""

# Check platform
PLATFORM=$(uname)
echo "🖥️  Platform: $PLATFORM"
echo ""

# Step 1: Build Frontend
echo "📦 Step 1/3: Building Frontend (React Production Build)..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "   Installing frontend dependencies..."
    yarn install
fi
yarn build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi
echo "✅ Frontend built successfully!"
echo ""

# Step 2: Prepare Backend
echo "📦 Step 2/3: Preparing Backend..."
cd ../backend
if [ ! -f "requirements.txt" ]; then
    echo "   Creating requirements.txt..."
    pip freeze > requirements.txt
fi
echo "✅ Backend ready!"
echo ""

# Step 3: Build Electron App
echo "📦 Step 3/3: Building Electron App..."
cd ../electron

if [ ! -d "node_modules" ]; then
    echo "   Installing electron dependencies..."
    yarn install
fi

# Build based on platform
case "$PLATFORM" in
    Darwin*)
        echo "   Building for macOS..."
        yarn build:mac
        echo ""
        echo "✅ macOS App built successfully!"
        echo "📍 Location: /app/electron/dist/WTI Smart Trader.dmg"
        echo ""
        echo "🎯 To install:"
        echo "   1. Open the .dmg file"
        echo "   2. Drag 'WTI Smart Trader' to Applications"
        echo "   3. Open from Applications or Spotlight"
        ;;
    Linux*)
        echo "   Building for Linux..."
        yarn build:linux
        echo ""
        echo "✅ Linux App built successfully!"
        echo "📍 Location: /app/electron/dist/WTI Smart Trader.AppImage"
        echo ""
        echo "🎯 To use:"
        echo "   chmod +x 'dist/WTI Smart Trader.AppImage'"
        echo "   ./dist/WTI\ Smart\ Trader.AppImage"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "   Building for Windows..."
        yarn build:win
        echo ""
        echo "✅ Windows App built successfully!"
        echo "📍 Location: /app/electron/dist/WTI Smart Trader Setup.exe"
        echo ""
        echo "🎯 To install:"
        echo "   Double-click the Setup.exe and follow the wizard"
        ;;
    *)
        echo "❌ Unknown platform: $PLATFORM"
        echo "   Please build manually:"
        echo "   - macOS:   yarn build:mac"
        echo "   - Windows: yarn build:win"
        echo "   - Linux:   yarn build:linux"
        exit 1
        ;;
esac

echo ""
echo "🎉 Build complete! Your standalone app is ready!"
echo ""
echo "📝 Note: The app includes:"
echo "   - React Frontend (built-in)"
echo "   - Python Backend (starts automatically)"
echo "   - All dependencies"
echo ""
echo "⚠️  Required on user's system:"
echo "   - Python 3.9+"
echo "   - MongoDB"
echo "   - Ollama (optional, for local AI)"
