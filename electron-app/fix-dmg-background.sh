#!/bin/bash
set -e

echo "🎨 Quick Fix: Creating DMG Background"
echo "====================================="
echo ""

cd "$(dirname "$0")"

# Prüfe ob SVG existiert
if [ ! -f "assets/dmg-background.svg" ]; then
    echo "❌ assets/dmg-background.svg not found!"
    exit 1
fi

# Methode 1: rsvg-convert (beste Qualität)
if command -v rsvg-convert &> /dev/null; then
    echo "✅ Using rsvg-convert..."
    rsvg-convert -w 540 -h 380 assets/dmg-background.svg -o assets/dmg-background.png
    echo "✅ DMG background created (high quality)"
    ls -lh assets/dmg-background.png
    exit 0
fi

# Methode 2: ImageMagick convert
if command -v convert &> /dev/null; then
    echo "✅ Using ImageMagick..."
    convert -size 540x380 gradient:"#1e293b-#0f172a" assets/dmg-background.png
    echo "✅ DMG background created (gradient)"
    ls -lh assets/dmg-background.png
    exit 0
fi

# Methode 3: Python mit Pillow
echo "⚠️  Trying Python/Pillow..."
python3 << 'PYTHON_SCRIPT'
try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Erstelle Gradient Background
    img = Image.new('RGB', (540, 380))
    draw = ImageDraw.Draw(img)
    
    # Gradient von dunkelblau zu schwarz
    for y in range(380):
        r = int(30 * (1 - y/380) + 15 * (y/380))
        g = int(41 * (1 - y/380) + 23 * (y/380))
        b = int(59 * (1 - y/380) + 42 * (y/380))
        draw.line([(0, y), (540, y)], fill=(r, g, b))
    
    # Text hinzufügen
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
    except:
        font = ImageFont.load_default()
    
    # "Booner Trade" Text
    text_bbox = draw.textbbox((0, 0), "Booner Trade", font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (540 - text_width) // 2
    draw.text((text_x, 80), "Booner Trade", fill='white', font=font)
    
    # Save
    img.save('assets/dmg-background.png')
    print('✅ DMG background created with Python/Pillow')
    
except ImportError:
    print('❌ Pillow not installed!')
    print('   Install: pip3 install Pillow')
    print('   OR install librsvg: brew install librsvg')
    exit(1)
PYTHON_SCRIPT

if [ -f "assets/dmg-background.png" ]; then
    echo "✅ Success!"
    ls -lh assets/dmg-background.png
else
    echo ""
    echo "❌ All methods failed!"
    echo ""
    echo "Please install one of:"
    echo "  1. brew install librsvg      (recommended)"
    echo "  2. brew install imagemagick"
    echo "  3. pip3 install Pillow"
    exit 1
fi
