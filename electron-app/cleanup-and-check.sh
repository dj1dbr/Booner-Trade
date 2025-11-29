#!/bin/bash

# Booner Trade - Cleanup & Check
# Räumt alte Installationen auf und prüft die App

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "Booner Trade - Cleanup & Check"
echo "======================================"
echo ""

# Schritt 1: Alle alten Installationen entfernen
echo -e "${YELLOW}[1/4] Entferne alte Installationen...${NC}"

# Finde alle Booner Trade Apps
APPS=$(mdfind "kMDItemFSName == 'Booner Trade.app'" 2>/dev/null || true)

if [ -n "$APPS" ]; then
    echo "Gefundene Installationen:"
    echo "$APPS"
    echo ""
    
    while IFS= read -r app; do
        echo "Lösche: $app"
        rm -rf "$app"
    done <<< "$APPS"
    
    echo -e "${GREEN}✅ Alte Installationen entfernt${NC}"
else
    echo "Keine alten Installationen gefunden"
fi

# Auch direkt in Applications prüfen
if [ -d "/Applications/Booner Trade.app" ]; then
    echo "Lösche: /Applications/Booner Trade.app"
    rm -rf "/Applications/Booner Trade.app"
fi

echo ""

# Schritt 2: App-Support-Dateien löschen
echo -e "${YELLOW}[2/4] Lösche App-Support-Dateien...${NC}"

if [ -d "$HOME/Library/Application Support/booner-trade" ]; then
    echo "Lösche: ~/Library/Application Support/booner-trade"
    rm -rf "$HOME/Library/Application Support/booner-trade"
fi

if [ -d "$HOME/Library/Logs/Booner Trade" ]; then
    echo "Lösche: ~/Library/Logs/Booner Trade"
    rm -rf "$HOME/Library/Logs/Booner Trade"
fi

if [ -d "$HOME/Library/Caches/booner-trade" ]; then
    echo "Lösche: ~/Library/Caches/booner-trade"
    rm -rf "$HOME/Library/Caches/booner-trade"
fi

echo -e "${GREEN}✅ App-Support-Dateien gelöscht${NC}"
echo ""

# Schritt 3: Prüfe die DMG Größe
echo -e "${YELLOW}[3/4] Prüfe DMG-Dateien...${NC}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -d "dist" ]; then
    echo "Gefundene DMG-Dateien:"
    ls -lh dist/*.dmg 2>/dev/null || echo "Keine DMG gefunden"
    
    for dmg in dist/*.dmg; do
        if [ -f "$dmg" ]; then
            SIZE=$(du -h "$dmg" | cut -f1)
            echo ""
            echo "Datei: $(basename "$dmg")"
            echo "Größe: $SIZE"
            
            # Mount DMG und prüfe Inhalt
            echo "Prüfe Inhalt..."
            MOUNT_POINT=$(hdiutil attach "$dmg" | grep Volumes | awk '{print $3}')
            
            if [ -n "$MOUNT_POINT" ]; then
                APP_PATH="$MOUNT_POINT/Booner Trade.app"
                
                if [ -d "$APP_PATH" ]; then
                    RESOURCES="$APP_PATH/Contents/Resources/app"
                    
                    echo "Checking Resources:"
                    
                    # MongoDB
                    if [ -d "$RESOURCES/mongodb/bin" ]; then
                        echo "  ✅ MongoDB: $(du -sh "$RESOURCES/mongodb" 2>/dev/null | cut -f1)"
                    else
                        echo "  ❌ MongoDB: FEHLT"
                    fi
                    
                    # Python
                    if [ -d "$RESOURCES/python/bin" ]; then
                        echo "  ✅ Python: $(du -sh "$RESOURCES/python" 2>/dev/null | cut -f1)"
                    else
                        echo "  ❌ Python: FEHLT"
                    fi
                    
                    # Backend
                    if [ -f "$RESOURCES/backend/server.py" ]; then
                        echo "  ✅ Backend: $(du -sh "$RESOURCES/backend" 2>/dev/null | cut -f1)"
                    else
                        echo "  ❌ Backend: FEHLT"
                    fi
                    
                    # Frontend
                    if [ -f "$RESOURCES/frontend/build/index.html" ]; then
                        echo "  ✅ Frontend: $(du -sh "$RESOURCES/frontend/build" 2>/dev/null | cut -f1)"
                    else
                        echo "  ❌ Frontend: FEHLT"
                    fi
                fi
                
                # Unmount
                hdiutil detach "$MOUNT_POINT" -quiet
            fi
        fi
    done
else
    echo -e "${RED}Keine dist/ Verzeichnis gefunden!${NC}"
fi

echo ""

# Schritt 4: Prüfe Ressourcen für nächsten Build
echo -e "${YELLOW}[4/4] Prüfe Ressourcen für Build...${NC}"

PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Checking build resources:"

# MongoDB
if [ -d "mongodb-mac/bin" ] && [ -f "mongodb-mac/bin/mongod" ]; then
    echo "  ✅ MongoDB: $(du -sh mongodb-mac 2>/dev/null | cut -f1)"
else
    echo "  ❌ MongoDB: FEHLT (Download erforderlich)"
fi

# Python
if [ -d "python-env/bin" ] && [ -f "python-env/bin/python3" ]; then
    echo "  ✅ Python: $(du -sh python-env 2>/dev/null | cut -f1)"
else
    echo "  ❌ Python: FEHLT (./prepare-resources.sh ausführen)"
fi

# Backend
if [ -f "$PROJECT_ROOT/backend/server.py" ]; then
    echo "  ✅ Backend: $(du -sh "$PROJECT_ROOT/backend" 2>/dev/null | cut -f1)"
else
    echo "  ❌ Backend: FEHLT"
fi

# Frontend Build
if [ -f "$PROJECT_ROOT/frontend/build/index.html" ]; then
    echo "  ✅ Frontend: $(du -sh "$PROJECT_ROOT/frontend/build" 2>/dev/null | cut -f1)"
else
    echo "  ❌ Frontend: FEHLT (yarn build erforderlich)"
fi

echo ""
echo "======================================"
echo "Zusammenfassung"
echo "======================================"
echo ""

if [ -d "mongodb-mac/bin" ] && [ -d "python-env/bin" ]; then
    echo -e "${GREEN}✅ Ressourcen vorhanden - bereit zu bauen${NC}"
    echo ""
    echo "Nächste Schritte:"
    echo "  1. ./build.sh"
    echo "  2. open dist/*.dmg"
    echo "  3. Installiere nur EINE Version (arm64 für Apple Silicon)"
else
    echo -e "${RED}❌ Ressourcen fehlen!${NC}"
    echo ""
    echo "Nächste Schritte:"
    echo "  1. MongoDB herunterladen (siehe KOMPLETTE-ANLEITUNG.md)"
    echo "  2. ./prepare-resources.sh"
    echo "  3. ./build.sh"
fi

echo ""
