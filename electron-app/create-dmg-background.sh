#!/bin/bash
set -e

echo "🎨 Creating DMG background image..."

cd assets

if command -v rsvg-convert &> /dev/null; then
    echo "Converting SVG to PNG..."
    rsvg-convert -w 540 -h 380 dmg-background.svg -o dmg-background.png
    echo "✅ dmg-background.png created"
else
    echo "⚠️  rsvg-convert not found. Creating simple background..."
    
    # Erstelle ein einfaches PNG mit ImageMagick (falls verfügbar)
    if command -v convert &> /dev/null; then
        convert -size 540x380 gradient:"#1e293b-#0f172a" dmg-background.png
        echo "✅ Simple gradient background created"
    else
        echo "❌ Cannot create background. Please install librsvg:"
        echo "   brew install librsvg"
        exit 1
    fi
fi

ls -lh dmg-background.png

cd ..
