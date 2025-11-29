#!/bin/bash

# Check DMG Structure

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "DMG Struktur Check"
echo "======================================"
echo ""

# Find DMG
DMG=$(ls -t dist/*-arm64.dmg 2>/dev/null | head -1)

if [ -z "$DMG" ]; then
    echo -e "${RED}❌ Keine DMG gefunden${NC}"
    exit 1
fi

echo "DMG: $DMG"
echo "Größe: $(du -h "$DMG" | cut -f1)"
echo ""

# List contents without mounting
echo "DMG Inhalt (via hdiutil):"
hdiutil imageinfo "$DMG" | grep -A5 "Partitions"
echo ""

echo "Versuche zu mounten..."
MOUNT_OUTPUT=$(hdiutil attach "$DMG" 2>&1)
echo "$MOUNT_OUTPUT"
echo ""

MOUNT_POINT=$(echo "$MOUNT_OUTPUT" | grep "/Volumes" | tail -1 | awk '{print $3}')

if [ -z "$MOUNT_POINT" ]; then
    echo -e "${RED}❌ Konnte Mount Point nicht ermitteln${NC}"
    exit 1
fi

echo "Mount Point: $MOUNT_POINT"
echo ""

echo "======================================"
echo "Vollständiger Inhalt:"
echo "======================================"
ls -laR "$MOUNT_POINT"
echo ""

echo "======================================"
echo "Suche nach .app:"
echo "======================================"
find "$MOUNT_POINT" -name "*.app" -print0 | while IFS= read -r -d '' app; do
    echo "Gefunden: $app"
    echo "Größe: $(du -sh "$app" | cut -f1)"
    
    if [ -d "$app/Contents/Resources" ]; then
        echo "Resources:"
        ls -lh "$app/Contents/Resources/" | head -20
    fi
    echo ""
done

# Unmount
echo "Unmounte..."
hdiutil detach "$MOUNT_POINT" -quiet 2>/dev/null

echo ""
echo "======================================"
echo "Diagnose:"
echo "======================================"
echo ""

# Check if app exists in dist before DMG
if [ -d "dist/mac-arm64/Booner Trade.app" ]; then
    APP_SIZE=$(du -sh "dist/mac-arm64/Booner Trade.app" | cut -f1)
    echo -e "${GREEN}✅ App existiert in dist/mac-arm64: $APP_SIZE${NC}"
    
    # Check resources in dist
    if [ -d "dist/mac-arm64/Booner Trade.app/Contents/Resources/app" ]; then
        echo ""
        echo "Resources in dist/mac-arm64 App:"
        ls -lh "dist/mac-arm64/Booner Trade.app/Contents/Resources/app/" 2>/dev/null
    fi
else
    echo -e "${RED}❌ App existiert nicht in dist/mac-arm64${NC}"
fi

echo ""
echo "======================================"
echo "Mögliche Probleme:"
echo "======================================"
echo ""
echo "1. electron-builder erstellt App, aber packt sie nicht in DMG"
echo "2. DMG-Struktur ist falsch konfiguriert"
echo "3. ASAR packt Ressourcen anders"
echo ""
echo "Lösungen:"
echo "1. Prüfe dist/mac-arm64/Booner Trade.app direkt"
echo "2. Kopiere App manuell und erstelle DMG:"
echo "   hdiutil create -volname 'Booner Trade' -srcfolder 'dist/mac-arm64/Booner Trade.app' -ov -format UDZO dist/manual.dmg"
echo ""
