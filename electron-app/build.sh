#!/bin/bash

# Booner Trade - Desktop App Build Script
# Erstellt eine vollständige macOS DMG-Datei

set -e  # Exit on error

echo "======================================"
echo "Booner Trade Desktop App - Build"
echo "======================================"
echo ""

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project Root: $PROJECT_ROOT"
echo ""

# Schritt 1: Dependencies überprüfen
echo -e "${YELLOW}[1/7] Überprüfe Dependencies...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js nicht gefunden! Bitte installiere Node.js${NC}"
    exit 1
fi

if ! command -v yarn &> /dev/null; then
    echo -e "${RED}❌ Yarn nicht gefunden! Bitte installiere Yarn${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js $(node -v) gefunden${NC}"
echo -e "${GREEN}✅ Yarn $(yarn -v) gefunden${NC}"
echo ""

# Schritt 2: Frontend .env konfigurieren (Port 8000!)
echo -e "${YELLOW}[2/7] Konfiguriere Frontend für Desktop (Port 8000)...${NC}"
cd "$PROJECT_ROOT/frontend"

# Backup original .env
if [ -f .env ]; then
    cp .env .env.backup
fi

# Create desktop .env (relative URL for production build)
cat > .env << 'EOF'
PUBLIC_URL=.
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

echo -e "${GREEN}✅ Frontend .env konfiguriert (Backend: http://localhost:8000)${NC}"
echo ""

# Schritt 3: Frontend bauen
echo -e "${YELLOW}[3/7] Baue Frontend (React Production Build)...${NC}"
echo "Dies kann einige Minuten dauern..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    yarn install --non-interactive
fi

# Build frontend
echo "Running: yarn build"
if ! yarn build; then
    echo -e "${RED}❌ Frontend build failed!${NC}"
    echo "Trying alternative build command..."
    
    # Fallback: Direct react-scripts build
    if [ -f "node_modules/.bin/react-scripts" ]; then
        node_modules/.bin/react-scripts build
    elif [ -f "node_modules/.bin/craco" ]; then
        node_modules/.bin/craco build
    else
        echo -e "${RED}❌ No build tool found (react-scripts or craco)${NC}"
        exit 1
    fi
fi

if [ ! -d "build" ]; then
    echo -e "${RED}❌ Frontend build failed - build directory not found${NC}"
    ls -la
    exit 1
fi

echo -e "${GREEN}✅ Frontend erfolgreich gebaut ($(du -sh build | cut -f1))${NC}"
echo ""

# Schritt 4: Electron App vorbereiten
echo -e "${YELLOW}[4/7] Bereite Electron App vor...${NC}"
cd "$SCRIPT_DIR"

# Install electron dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing electron dependencies..."
    yarn install
fi

echo -e "${GREEN}✅ Electron dependencies installiert${NC}"
echo ""

# Schritt 5: DMG Background als PNG erstellen (falls noch nicht vorhanden)
echo -e "${YELLOW}[5/7] Erstelle DMG Background...${NC}"

if [ ! -f "assets/dmg-background.png" ]; then
    echo "Konvertiere SVG zu PNG..."
    
    # Check if ImageMagick or similar is available
    if command -v convert &> /dev/null; then
        convert -background none -size 660x400 assets/dmg-background.svg assets/dmg-background.png 2>/dev/null || {
            echo -e "${YELLOW}⚠️  ImageMagick convert failed, using alternative method${NC}"
        }
    fi
    
    # If PNG still doesn't exist, create a simple placeholder
    if [ ! -f "assets/dmg-background.png" ]; then
        echo -e "${YELLOW}⚠️  Creating placeholder PNG (install ImageMagick for better quality)${NC}"
        # Create a minimal placeholder if tools aren't available
        # This will be replaced by electron-builder's default
        touch assets/dmg-background.png
    fi
else
    echo -e "${GREEN}✅ DMG Background PNG existiert bereits${NC}"
fi
echo ""

# Schritt 6: App bauen (DMG erstellen)
echo -e "${YELLOW}[6/7] Baue macOS App (DMG wird erstellt)...${NC}"
echo "Dies kann 5-10 Minuten dauern..."

# Check if electron-builder is available
if ! command -v electron-builder &> /dev/null; then
    echo "electron-builder not in PATH, using local version..."
    if [ -f "node_modules/.bin/electron-builder" ]; then
        echo "Using: node_modules/.bin/electron-builder"
        node_modules/.bin/electron-builder --mac
    else
        echo -e "${RED}❌ electron-builder not found! Installing...${NC}"
        yarn add --dev electron-builder
        yarn build:dmg
    fi
else
    # Run electron-builder
    yarn build:dmg
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ electron-builder failed!${NC}"
    echo "Check the error messages above."
    exit 1
fi

echo -e "${GREEN}✅ DMG-Datei erfolgreich erstellt${NC}"
echo ""

# Schritt 7: DMG finden und anzeigen
echo -e "${YELLOW}[7/7] Suche erstellte DMG-Datei...${NC}"

# Find the DMG file (handles both naming conventions)
DMG_FILE=$(find dist -name "*.dmg" -type f | head -1)

if [ -z "$DMG_FILE" ]; then
    echo -e "${RED}❌ Keine DMG-Datei gefunden in dist/!${NC}"
    ls -la dist/ 2>/dev/null || echo "dist/ directory not found"
    exit 1
fi

echo -e "${GREEN}✅ DMG-Datei gefunden: $DMG_FILE${NC}"
echo ""

# Schritt 8: .env wiederherstellen
echo "Stelle original Frontend .env wieder her..."
cd "$PROJECT_ROOT/frontend"
if [ -f .env.backup ]; then
    mv .env.backup .env
    echo -e "${GREEN}✅ Original .env wiederhergestellt${NC}"
fi
echo ""

# Abschluss
echo "======================================"
echo -e "${GREEN}✅ BUILD ERFOLGREICH ABGESCHLOSSEN!${NC}"
echo "======================================"
echo ""
echo "📦 DMG-Datei: $DMG_FILE"
echo ""
echo "Dateigröße: $(du -h "$DMG_FILE" | cut -f1)"
echo ""
echo "Zum Öffnen der DMG:"
echo "  open '$DMG_FILE'"
echo ""
echo "Die App kann jetzt auf macOS installiert werden!"
echo ""
