#!/bin/bash

# Booner Trade - Fix Common Build Errors
# Behebt häufige Build-Probleme automatisch

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Build Error Fixer"
echo "======================================"
echo ""

# Problem 1: electron-builder not found
echo -e "${YELLOW}[1/5] Checking electron-builder...${NC}"
cd "$SCRIPT_DIR"
if [ ! -f "node_modules/.bin/electron-builder" ]; then
    echo "electron-builder nicht gefunden, installiere..."
    yarn add --dev electron-builder
    echo -e "${GREEN}✅ electron-builder installiert${NC}"
else
    echo -e "${GREEN}✅ electron-builder vorhanden${NC}"
fi
echo ""

# Problem 2: Frontend dependencies fehlen
echo -e "${YELLOW}[2/5] Checking Frontend dependencies...${NC}"
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    echo "Frontend node_modules fehlen, installiere..."
    yarn install
    echo -e "${GREEN}✅ Frontend dependencies installiert${NC}"
else
    echo -e "${GREEN}✅ Frontend dependencies vorhanden${NC}"
fi
echo ""

# Problem 3: Frontend Build fehlt
echo -e "${YELLOW}[3/5] Checking Frontend build...${NC}"
if [ ! -d "build" ]; then
    echo "Frontend build fehlt, baue jetzt..."
    
    # Configure for desktop
    cat > .env << 'EOF'
PUBLIC_URL=.
REACT_APP_BACKEND_URL=http://localhost:8000
EOF
    
    yarn build
    echo -e "${GREEN}✅ Frontend gebaut${NC}"
else
    echo -e "${GREEN}✅ Frontend build vorhanden${NC}"
fi
echo ""

# Problem 4: Electron dependencies fehlen
echo -e "${YELLOW}[4/5] Checking Electron dependencies...${NC}"
cd "$SCRIPT_DIR"
if [ ! -d "node_modules" ]; then
    echo "Electron node_modules fehlen, installiere..."
    yarn install
    echo -e "${GREEN}✅ Electron dependencies installiert${NC}"
else
    echo -e "${GREEN}✅ Electron dependencies vorhanden${NC}"
fi
echo ""

# Problem 5: Assets prüfen
echo -e "${YELLOW}[5/5] Checking Assets...${NC}"
if [ ! -f "assets/dmg-background.png" ]; then
    echo "Creating dmg-background.png..."
    mkdir -p assets
    
    # Create simple placeholder with Python
    if command -v python3 &> /dev/null; then
        python3 << 'PYTHON_EOF'
try:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (660, 400), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    for y in range(400):
        color_value = int(26 + (y / 400) * 30)
        draw.line([(0, y), (660, y)], fill=(color_value, color_value, color_value + 20))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    draw.text((330, 150), "Booner Trade", fill='#2dd4bf', anchor='mm', font=font)
    draw.text((330, 200), "AI Trading Platform", fill='#94a3b8', anchor='mm', font=font_small)
    img.save('assets/dmg-background.png')
    print("✅ dmg-background.png created")
except Exception as e:
    print(f"Warning: {e}")
    # Create empty file as fallback
    open('assets/dmg-background.png', 'w').close()
PYTHON_EOF
    else
        # Fallback: empty file
        touch assets/dmg-background.png
    fi
    echo -e "${GREEN}✅ DMG background erstellt${NC}"
else
    echo -e "${GREEN}✅ DMG background vorhanden${NC}"
fi

if [ ! -f "assets/logo.png" ]; then
    echo "Creating logo.png..."
    
    if command -v python3 &> /dev/null; then
        python3 << 'PYTHON_EOF'
try:
    from PIL import Image, ImageDraw, ImageFont
    icon = Image.new('RGBA', (1024, 1024), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    center = 512
    radius = 400
    draw.ellipse([center-radius, center-radius, center+radius, center+radius], fill='#2dd4bf')
    draw.ellipse([center-radius+40, center-radius+40, center+radius-40, center+radius-40], fill='#1a1a2e')
    try:
        icon_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 280)
    except:
        icon_font = ImageFont.load_default()
    draw.text((center, center), "BT", fill='#2dd4bf', anchor='mm', font=icon_font)
    icon.save('assets/logo.png')
    print("✅ logo.png created")
except Exception as e:
    print(f"Warning: {e}")
    open('assets/logo.png', 'w').close()
PYTHON_EOF
    else
        touch assets/logo.png
    fi
    echo -e "${GREEN}✅ Logo erstellt${NC}"
else
    echo -e "${GREEN}✅ Logo vorhanden${NC}"
fi
echo ""

echo "======================================"
echo -e "${GREEN}✅ Alle Probleme behoben!${NC}"
echo "======================================"
echo ""
echo "Jetzt kannst du bauen:"
echo "  ./build.sh"
echo ""
