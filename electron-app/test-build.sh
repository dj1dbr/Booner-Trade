#!/bin/bash

# Booner Trade - Quick Build Test
# Testet ob alle Komponenten für den Build bereit sind

set -e

echo "======================================"
echo "Booner Trade - Build Readiness Check"
echo "======================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

ERRORS=0

# Check 1: Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    echo -e "${GREEN}✅ $(node -v)${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Yarn
echo -n "Checking Yarn... "
if command -v yarn &> /dev/null; then
    echo -e "${GREEN}✅ $(yarn -v)${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: Frontend build directory
echo -n "Checking Frontend... "
if [ -d "$PROJECT_ROOT/frontend" ]; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ frontend directory not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: Backend directory
echo -n "Checking Backend... "
if [ -d "$PROJECT_ROOT/backend" ]; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ backend directory not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: Electron app structure
echo -n "Checking Electron App... "
if [ -f "$SCRIPT_DIR/main.js" ] && [ -f "$SCRIPT_DIR/package.json" ]; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ main.js or package.json missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 6: Assets
echo -n "Checking Assets... "
if [ -f "$SCRIPT_DIR/assets/dmg-background.png" ] && [ -f "$SCRIPT_DIR/assets/logo.png" ]; then
    echo -e "${GREEN}✅ Found (PNG)${NC}"
else
    echo -e "${YELLOW}⚠️  PNG assets missing (will be created)${NC}"
fi

# Check 7: build.sh
echo -n "Checking build.sh... "
if [ -x "$SCRIPT_DIR/build.sh" ]; then
    echo -e "${GREEN}✅ Executable${NC}"
else
    echo -e "${RED}❌ Not executable or missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 8: Disk space
echo -n "Checking Disk Space... "
AVAILABLE=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
echo -e "${GREEN}✅ ${AVAILABLE} available${NC}"

# Check 9: Port 8000 configuration
echo -n "Checking main.js Port... "
if grep -q "8000" "$SCRIPT_DIR/main.js"; then
    echo -e "${GREEN}✅ Port 8000 configured${NC}"
else
    echo -e "${RED}❌ Port 8000 not found in main.js${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "======================================"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to build.${NC}"
    echo ""
    echo "Run the build:"
    echo "  cd /app/electron-app"
    echo "  ./build.sh"
    echo ""
else
    echo -e "${RED}❌ $ERRORS error(s) found. Fix them before building.${NC}"
    echo ""
    exit 1
fi
