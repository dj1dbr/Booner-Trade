#!/bin/bash

# Booner Trade Desktop - Komplettes Setup
# Führt alle notwendigen Schritte aus

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Booner Trade Desktop - Setup"
echo "======================================"
echo ""
echo "Dieses Script führt ALLE Schritte aus:"
echo "1. Resource Check"
echo "2. MongoDB Setup (falls nötig)"
echo "3. Python Setup"
echo "4. Frontend Build"
echo "5. Electron Build"
echo "6. DMG erstellen"
echo ""

read -p "Fortfahren? (J/N): " continue
if [ "$continue" != "J" ] && [ "$continue" != "j" ]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""

# Schritt 1: Resource Check
echo -e "${BLUE}[Schritt 1/6] Resource Check${NC}"
./check-resources.sh

echo ""
read -p "Sehen die Ressourcen gut aus? (J/N): " resources_ok

if [ "$resources_ok" != "J" ] && [ "$resources_ok" != "j" ]; then
    echo ""
    echo -e "${YELLOW}Ressourcen müssen vorbereitet werden!${NC}"
    echo ""
    
    # MongoDB Check
    if [ ! -f "mongodb-mac/bin/mongod" ]; then
        echo -e "${RED}MongoDB MUSS manuell heruntergeladen werden!${NC}"
        echo ""
        echo "1. Öffne Browser:"
        echo "   https://www.mongodb.com/try/download/community"
        echo ""
        echo "2. Wähle:"
        echo "   - Version: 7.0.x"
        echo "   - Platform: macOS"
        echo "   - Package: TGZ"
        echo "   - Architecture: arm64"
        echo ""
        echo "3. Nach Download:"
        read -p "Pfad zur heruntergeladenen TGZ-Datei: " MONGODB_TGZ
        
        if [ -f "$MONGODB_TGZ" ]; then
            echo "Entpacke MongoDB..."
            TEMP_DIR=$(mktemp -d)
            tar -xzf "$MONGODB_TGZ" -C "$TEMP_DIR"
            
            echo "Kopiere MongoDB Binaries..."
            mkdir -p mongodb-mac/bin
            cp "$TEMP_DIR"/mongodb-macos-*/bin/* mongodb-mac/bin/
            
            rm -rf "$TEMP_DIR"
            
            echo -e "${GREEN}✅ MongoDB installiert${NC}"
            
            # Test
            if ./mongodb-mac/bin/mongod --version &>/dev/null; then
                echo -e "${GREEN}✅ MongoDB funktioniert${NC}"
            else
                echo -e "${RED}❌ MongoDB Test fehlgeschlagen${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Datei nicht gefunden!${NC}"
            exit 1
        fi
    fi
    
    # Python Setup
    if [ ! -f "python-env/bin/python3" ]; then
        echo ""
        echo -e "${YELLOW}Python Environment wird erstellt...${NC}"
        ./prepare-resources.sh
    fi
    
    # Frontend Build
    if [ ! -d "$PROJECT_ROOT/frontend/build" ]; then
        echo ""
        echo -e "${YELLOW}Frontend wird gebaut...${NC}"
        cd "$PROJECT_ROOT/frontend"
        
        # Configure
        cat > .env << 'EOF'
PUBLIC_URL=.
REACT_APP_BACKEND_URL=http://localhost:8000
EOF
        
        yarn install
        yarn build
        
        cd "$SCRIPT_DIR"
        echo -e "${GREEN}✅ Frontend gebaut${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Alle Ressourcen vorbereitet!${NC}"
    echo ""
fi

# Schritt 2: Final Check
echo -e "${BLUE}[Schritt 2/6] Final Resource Check${NC}"
./check-resources.sh

# Schritt 3: Fix Build Errors
echo ""
echo -e "${BLUE}[Schritt 3/6] Fix Build Errors${NC}"
./fix-build-errors.sh

# Schritt 4: Build
echo ""
echo -e "${BLUE}[Schritt 4/6] Building Desktop App${NC}"
echo "Dies kann 10-15 Minuten dauern..."
echo ""

./build.sh

# Schritt 5: Check Result
echo ""
echo -e "${BLUE}[Schritt 5/6] Checking Result${NC}"

if [ -f "dist/Booner Trade-1.0.0-arm64.dmg" ]; then
    SIZE=$(du -h "dist/Booner Trade-1.0.0-arm64.dmg" | cut -f1)
    echo -e "${GREEN}✅ DMG erstellt: $SIZE${NC}"
    
    # Check size
    SIZE_MB=$(du -m "dist/Booner Trade-1.0.0-arm64.dmg" | cut -f1)
    if [ $SIZE_MB -lt 500 ]; then
        echo -e "${RED}⚠️  WARNING: DMG ist nur ${SIZE_MB}MB!${NC}"
        echo "Erwartete Größe: 900MB - 1200MB"
        echo "MongoDB/Python könnten fehlen!"
    elif [ $SIZE_MB -gt 800 ]; then
        echo -e "${GREEN}✅ Größe sieht gut aus!${NC}"
    else
        echo -e "${YELLOW}⚠️  Größe ist OK aber könnte größer sein${NC}"
    fi
else
    echo -e "${RED}❌ DMG nicht gefunden!${NC}"
    exit 1
fi

# Schritt 6: Installation
echo ""
echo -e "${BLUE}[Schritt 6/6] Installation${NC}"
echo ""
echo "Die DMG wurde erstellt:"
ls -lh dist/*.dmg
echo ""
echo -e "${GREEN}Fertig!${NC}"
echo ""
echo "Nächste Schritte:"
echo "1. Öffne DMG:"
echo "   open 'dist/Booner Trade-1.0.0-arm64.dmg'"
echo ""
echo "2. Ziehe App nach /Applications"
echo ""
echo "3. Starte App:"
echo "   open -a 'Booner Trade'"
echo ""
echo "4. Bei Problemen, Terminal-Output ansehen:"
echo "   '/Applications/Booner Trade.app/Contents/MacOS/Booner Trade'"
echo ""
