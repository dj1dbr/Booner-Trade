#!/bin/bash
set -e

echo "🚀 Building Booner Trade Desktop App for Mac..."

# 1. Frontend Build
echo "📦 Building Frontend..."
cd ../frontend
yarn build
cd ../electron-app

# 2. Backend Requirements vorbereiten
echo "📦 Preparing Backend..."
cd ../backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../electron-app

# 3. Icon konvertieren (SVG -> PNG -> ICNS)
echo "🎨 Converting Icon..."
if command -v rsvg-convert &> /dev/null && command -v iconutil &> /dev/null; then
    mkdir -p assets/logo.iconset
    
    # Generiere verschiedene Größen
    for size in 16 32 64 128 256 512 1024; do
        rsvg-convert -w $size -h $size assets/logo.svg -o assets/logo.iconset/icon_${size}x${size}.png
        if [ $size -le 512 ]; then
            size2=$((size * 2))
            rsvg-convert -w $size2 -h $size2 assets/logo.svg -o assets/logo.iconset/icon_${size}x${size}@2x.png
        fi
    done
    
    # Erstelle ICNS
    iconutil -c icns assets/logo.iconset -o assets/logo.icns
    rm -rf assets/logo.iconset
    echo "✅ Icon created: assets/logo.icns"
else
    echo "⚠️  Warning: rsvg-convert or iconutil not found. Using PNG fallback."
    # Erstelle zumindest ein PNG als Fallback
    if command -v rsvg-convert &> /dev/null; then
        rsvg-convert -w 512 -h 512 assets/logo.svg -o assets/logo.png
    else
        echo "❌ Cannot convert icon. Please install librsvg: brew install librsvg"
        exit 1
    fi
fi

# 4. MongoDB für Mac herunterladen (falls noch nicht vorhanden)
echo "📦 Preparing MongoDB..."
if [ ! -d "mongodb-mac" ]; then
    echo "Downloading MongoDB Community Edition for macOS..."
    MONGO_VERSION="7.0.4"
    ARCH=$(uname -m)
    
    if [ "$ARCH" = "arm64" ]; then
        MONGO_URL="https://fastdl.mongodb.org/osx/mongodb-macos-arm64-${MONGO_VERSION}.tgz"
    else
        MONGO_URL="https://fastdl.mongodb.org/osx/mongodb-macos-x86_64-${MONGO_VERSION}.tgz"
    fi
    
    curl -O "$MONGO_URL"
    tar -zxvf mongodb-macos-*.tgz
    mv mongodb-macos-* mongodb-mac
    rm mongodb-macos-*.tgz
    echo "✅ MongoDB downloaded"
else
    echo "✅ MongoDB already prepared"
fi

# 5. Python Environment vorbereiten (Portable)
echo "📦 Creating Portable Python Environment..."
if [ ! -d "python-env" ]; then
    python3 -m venv python-env
    source python-env/bin/activate
    pip install --upgrade pip
    pip install -r ../backend/requirements.txt
    deactivate
    echo "✅ Python environment created"
else
    echo "✅ Python environment already exists"
fi

# 6. Electron App bauen
echo "🔨 Building Electron App..."
yarn install
yarn build:dmg

echo ""
echo "✅ Build complete!"
echo "📦 DMG file location: dist/Booner Trade-1.0.0.dmg"
echo ""
echo "To install:"
echo "1. Open the DMG file"
echo "2. Drag 'Booner Trade' to Applications folder"
echo "3. Launch from Applications"
