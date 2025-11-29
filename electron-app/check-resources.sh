#!/bin/bash

# Schneller Check was für den Build fehlt

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Resource Check für Desktop Build"
echo "======================================"
echo ""

MISSING=0

# MongoDB
echo -n "MongoDB (mongodb-mac/bin/mongod): "
if [ -f "$SCRIPT_DIR/mongodb-mac/bin/mongod" ]; then
    SIZE=$(du -sh "$SCRIPT_DIR/mongodb-mac" 2>/dev/null | cut -f1)
    echo -e "${GREEN}✅ Vorhanden ($SIZE)${NC}"
else
    echo -e "${RED}❌ FEHLT${NC}"
    MISSING=$((MISSING + 1))
fi

# Python
echo -n "Python (python-env/bin/python3): "
if [ -f "$SCRIPT_DIR/python-env/bin/python3" ]; then
    SIZE=$(du -sh "$SCRIPT_DIR/python-env" 2>/dev/null | cut -f1)
    echo -e "${GREEN}✅ Vorhanden ($SIZE)${NC}"
else
    echo -e "${RED}❌ FEHLT${NC}"
    MISSING=$((MISSING + 1))
fi

# Uvicorn
echo -n "Uvicorn (python-env/bin/uvicorn): "
if [ -f "$SCRIPT_DIR/python-env/bin/uvicorn" ]; then
    echo -e "${GREEN}✅ Vorhanden${NC}"
else
    echo -e "${RED}❌ FEHLT${NC}"
    MISSING=$((MISSING + 1))
fi

# Backend
echo -n "Backend (backend/server.py): "
if [ -f "$PROJECT_ROOT/backend/server.py" ]; then
    SIZE=$(du -sh "$PROJECT_ROOT/backend" 2>/dev/null | cut -f1)
    echo -e "${GREEN}✅ Vorhanden ($SIZE)${NC}"
else
    echo -e "${RED}❌ FEHLT${NC}"
    MISSING=$((MISSING + 1))
fi

# Frontend Build
echo -n "Frontend Build (frontend/build/): "
if [ -d "$PROJECT_ROOT/frontend/build" ] && [ -f "$PROJECT_ROOT/frontend/build/index.html" ]; then
    SIZE=$(du -sh "$PROJECT_ROOT/frontend/build" 2>/dev/null | cut -f1)
    echo -e "${GREEN}✅ Vorhanden ($SIZE)${NC}"
else
    echo -e "${RED}❌ FEHLT${NC}"
    MISSING=$((MISSING + 1))
fi

echo ""
echo "======================================"

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✅ ALLES DA! Bereit zu bauen.${NC}"
    echo ""
    echo "Nächster Schritt:"
    echo "  ./build.sh"
    echo ""
    echo "Erwartete DMG Größe: ~900MB - 1.2GB"
else
    echo -e "${RED}❌ $MISSING Ressource(n) fehlen!${NC}"
    echo ""
    
    if [ ! -f "$SCRIPT_DIR/mongodb-mac/bin/mongod" ]; then
        echo -e "${YELLOW}MongoDB fehlt!${NC}"
        echo "1. Download von: https://www.mongodb.com/try/download/community"
        echo "   - Version: 7.0.x"
        echo "   - Platform: macOS"
        echo "   - Package: TGZ"
        echo "   - Architecture: arm64"
        echo ""
        echo "2. Entpacken und kopieren:"
        echo "   cd ~/Downloads"
        echo "   tar -xzf mongodb-macos-arm64-7.0.*.tgz"
        echo "   mkdir -p '$SCRIPT_DIR/mongodb-mac/bin'"
        echo "   cp mongodb-macos-*/bin/* '$SCRIPT_DIR/mongodb-mac/bin/'"
        echo ""
    fi
    
    if [ ! -f "$SCRIPT_DIR/python-env/bin/python3" ]; then
        echo -e "${YELLOW}Python fehlt!${NC}"
        echo "Ausführen:"
        echo "   ./prepare-resources.sh"
        echo "   (Wähle Option A)"
        echo ""
    fi
    
    if [ ! -d "$PROJECT_ROOT/frontend/build" ]; then
        echo -e "${YELLOW}Frontend Build fehlt!${NC}"
        echo "Ausführen:"
        echo "   cd '$PROJECT_ROOT/frontend'"
        echo "   yarn build"
        echo ""
    fi
fi

# Zeige aktuelle DMG Größe falls vorhanden
if [ -f "dist/Booner Trade-1.0.0-arm64.dmg" ]; then
    echo "Aktuelle DMG:"
    ls -lh dist/*.dmg
    echo ""
    echo -e "${YELLOW}⚠️  Aktuelle DMG ist nur 161MB - MongoDB/Python fehlen!${NC}"
fi
