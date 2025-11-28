#!/bin/bash
set -e

echo "🔧 Booner Trade - Quick Fix & Rebuild"
echo "======================================"
echo ""

# 1. Cleanup vorheriger fehlgeschlagener Builds
echo "🧹 Cleaning up previous failed builds..."
rm -rf mongodb-mac
rm -rf mongodb-macos-*
rm -rf python-env
rm -rf dist
rm -f *.tgz
echo "✅ Cleanup done"
echo ""

# 2. Prüfe Voraussetzungen
echo "🔍 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found! Install with: brew install node"
    exit 1
fi

if ! command -v yarn &> /dev/null; then
    echo "❌ Yarn not found! Install with: brew install yarn"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found! Install with: brew install python@3.11"
    exit 1
fi

echo "✅ All prerequisites found"
echo ""

# 3. Frontend bauen
echo "📦 Building Frontend (this takes 2-3 minutes)..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    yarn install
fi
yarn build
cd ../electron-app
echo "✅ Frontend built"
echo ""

# 4. MongoDB herunterladen (mit verbesserter Fehlerbehandlung)
echo "📦 Downloading MongoDB..."
MONGO_VERSION="7.0.4"
ARCH=$(uname -m)

if [ "$ARCH" = "arm64" ]; then
    MONGO_URL="https://fastdl.mongodb.org/osx/mongodb-macos-arm64-${MONGO_VERSION}.tgz"
    MONGO_FILE="mongodb-macos-arm64-${MONGO_VERSION}.tgz"
else
    MONGO_URL="https://fastdl.mongodb.org/osx/mongodb-macos-x86_64-${MONGO_VERSION}.tgz"
    MONGO_FILE="mongodb-macos-x86_64-${MONGO_VERSION}.tgz"
fi

echo "  URL: $MONGO_URL"
echo "  Architecture: $ARCH"
echo ""

curl -L -o "$MONGO_FILE" "$MONGO_URL" --progress-bar

if [ ! -f "$MONGO_FILE" ]; then
    echo "❌ MongoDB download failed!"
    exit 1
fi

echo "📦 Extracting MongoDB..."
tar -zxf "$MONGO_FILE"

# Finde das extrahierte Verzeichnis
MONGO_DIR=$(find . -maxdepth 1 -type d -name "mongodb-macos-*" | head -n 1)

if [ -z "$MONGO_DIR" ]; then
    echo "❌ Could not find extracted MongoDB directory!"
    ls -la
    exit 1
fi

echo "  Found: $MONGO_DIR"
mv "$MONGO_DIR" mongodb-mac
rm "$MONGO_FILE"
echo "✅ MongoDB ready"
echo ""

# 5. Python Environment
echo "📦 Creating Python Environment..."
python3 -m venv python-env
source python-env/bin/activate
pip install --upgrade pip

echo "📦 Installing emergentintegrations from custom index..."
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

echo "📦 Installing other requirements..."
pip install -r ../backend/requirements.txt

deactivate
echo "✅ Python environment ready"
echo ""

# 6. Icon & DMG Background konvertieren
echo "🎨 Preparing Icon & DMG Background..."

# DMG Background (WICHTIG für DMG-Build!)
if command -v rsvg-convert &> /dev/null; then
    echo "Creating DMG background..."
    rsvg-convert -w 540 -h 380 assets/dmg-background.svg -o assets/dmg-background.png
    echo "✅ DMG background created"
else
    echo "⚠️  Creating simple gradient background..."
    if command -v convert &> /dev/null; then
        convert -size 540x380 gradient:"#1e293b-#0f172a" assets/dmg-background.png
    else
        # Erstelle minimales PNG falls nichts verfügbar
        echo "Creating minimal background..."
        python3 -c "
from PIL import Image
img = Image.new('RGB', (540, 380), color='#0f172a')
img.save('assets/dmg-background.png')
print('✅ Minimal background created')
" 2>/dev/null || echo "⚠️  No background tools available"
    fi
fi

# App Icon
if command -v rsvg-convert &> /dev/null && command -v iconutil &> /dev/null; then
    echo "Converting SVG to ICNS..."
    mkdir -p assets/logo.iconset
    
    for size in 16 32 64 128 256 512; do
        rsvg-convert -w $size -h $size assets/logo.svg -o assets/logo.iconset/icon_${size}x${size}.png
        if [ $size -le 512 ]; then
            size2=$((size * 2))
            rsvg-convert -w $size2 -h $size2 assets/logo.svg -o assets/logo.iconset/icon_${size}x${size}@2x.png
        fi
    done
    
    iconutil -c icns assets/logo.iconset -o assets/logo.icns
    rm -rf assets/logo.iconset
    echo "✅ Icon created: assets/logo.icns"
else
    echo "⚠️  Icon tools not found, creating PNG fallback..."
    if command -v rsvg-convert &> /dev/null; then
        rsvg-convert -w 512 -h 512 assets/logo.svg -o assets/logo.png
        cp assets/logo.png assets/logo.icns
    else
        echo "⚠️  Warning: librsvg not installed. Install with: brew install librsvg"
        echo "   Continuing without icon conversion..."
    fi
fi
echo ""

# 7. Electron Dependencies installieren
echo "📦 Installing Electron dependencies..."
yarn install
echo "✅ Dependencies installed"
echo ""

# 8. Build Electron App
echo "🔨 Building Electron App (this takes 2-3 minutes)..."
yarn build:dmg

# 9. Erfolg!
echo ""
echo "✅ =================================="
echo "✅  BUILD SUCCESSFUL!"
echo "✅ =================================="
echo ""
echo "📦 Your DMG file is ready:"
echo "   $(pwd)/dist/Booner Trade-1.0.0.dmg"
echo ""
echo "🚀 To install:"
echo "   open dist/Booner\ Trade-1.0.0.dmg"
echo ""
