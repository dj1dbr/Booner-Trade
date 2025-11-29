#!/bin/bash

# Debug DMG - Was ist drin?

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "Debug: Was ist in der DMG?"
echo "======================================"
echo ""

# Find newest DMG
DMG=$(ls -t dist/*-arm64.dmg 2>/dev/null | head -1)

if [ -z "$DMG" ]; then
    echo -e "${RED}❌ Keine DMG gefunden!${NC}"
    exit 1
fi

echo "DMG: $DMG"
echo "Größe: $(du -h "$DMG" | cut -f1)"
echo ""

# Mount
echo "Mounte DMG..."
MOUNT_POINT=$(hdiutil attach "$DMG" 2>/dev/null | grep Volumes | awk '{print $3}')

if [ -z "$MOUNT_POINT" ]; then
    echo -e "${RED}❌ Konnte DMG nicht mounten${NC}"
    exit 1
fi

echo "Mounted at: $MOUNT_POINT"
echo ""

APP_PATH="$MOUNT_POINT/Booner Trade.app"
RESOURCES="$APP_PATH/Contents/Resources"

if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}❌ App nicht in DMG gefunden${NC}"
    hdiutil detach "$MOUNT_POINT" -quiet
    exit 1
fi

echo "======================================"
echo "Struktur:"
echo "======================================"
echo ""

# Show structure
echo "Resources Verzeichnis:"
ls -lh "$RESOURCES" 2>/dev/null || echo "Keine Resources"
echo ""

echo "App Verzeichnis:"
if [ -d "$RESOURCES/app" ]; then
    ls -lh "$RESOURCES/app" 2>/dev/null
else
    echo -e "${RED}❌ app/ Verzeichnis fehlt!${NC}"
fi
echo ""

# Check each resource
echo "======================================"
echo "Resource Check:"
echo "======================================"
echo ""

# MongoDB
if [ -d "$RESOURCES/app/mongodb" ]; then
    echo -e "${GREEN}✅ MongoDB:${NC} $(du -sh "$RESOURCES/app/mongodb" 2>/dev/null | cut -f1)"
    ls -lh "$RESOURCES/app/mongodb/bin/" 2>/dev/null | head -5
else
    echo -e "${RED}❌ MongoDB fehlt${NC}"
fi
echo ""

# Python
if [ -d "$RESOURCES/app/python" ]; then
    echo -e "${GREEN}✅ Python:${NC} $(du -sh "$RESOURCES/app/python" 2>/dev/null | cut -f1)"
    ls -lh "$RESOURCES/app/python/bin/" 2>/dev/null | head -5
else
    echo -e "${RED}❌ Python fehlt${NC}"
fi
echo ""

# Backend
if [ -d "$RESOURCES/app/backend" ]; then
    echo -e "${GREEN}✅ Backend:${NC} $(du -sh "$RESOURCES/app/backend" 2>/dev/null | cut -f1)"
    ls -lh "$RESOURCES/app/backend/" 2>/dev/null | head -5
else
    echo -e "${RED}❌ Backend fehlt${NC}"
fi
echo ""

# Frontend
if [ -d "$RESOURCES/app/frontend/build" ]; then
    echo -e "${GREEN}✅ Frontend:${NC} $(du -sh "$RESOURCES/app/frontend/build" 2>/dev/null | cut -f1)"
else
    echo -e "${RED}❌ Frontend fehlt${NC}"
fi
echo ""

# Full size breakdown
echo "======================================"
echo "Größen-Breakdown:"
echo "======================================"
echo ""
du -sh "$RESOURCES"/* 2>/dev/null | sort -h

# Unmount
echo ""
echo "Unmounte DMG..."
hdiutil detach "$MOUNT_POINT" -quiet

echo ""
echo "======================================"
echo "Analyse:"
echo "======================================"
echo ""

# Calculate expected vs actual
EXPECTED_SIZE=900
ACTUAL_SIZE=$(du -m "$DMG" | cut -f1)

echo "Erwartete Größe: ~${EXPECTED_SIZE}MB"
echo "Tatsächliche Größe: ${ACTUAL_SIZE}MB"
echo ""

if [ $ACTUAL_SIZE -lt 500 ]; then
    echo -e "${RED}❌ DMG ist zu klein!${NC}"
    echo ""
    echo "Wahrscheinliche Ursachen:"
    echo "1. extraResources werden nicht gepackt"
    echo "2. Pfade in package.json sind falsch"
    echo "3. Verzeichnisse existieren nicht beim Build"
    echo ""
    echo "Lösung:"
    echo "1. Prüfe: ls -la mongodb-mac/ python-env/ ../backend/ ../frontend/build/"
    echo "2. Prüfe package.json extraResources"
    echo "3. electron-builder mit --dir statt --mac testen"
else
    echo -e "${GREEN}✅ Größe sieht gut aus!${NC}"
fi
