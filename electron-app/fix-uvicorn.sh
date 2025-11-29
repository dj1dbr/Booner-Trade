#!/bin/bash

# Fix Uvicorn Installation

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Fix Uvicorn Installation"
echo "======================================"
echo ""

cd "$SCRIPT_DIR"

# Check if python-env exists
if [ ! -d "python-env" ]; then
    echo -e "${RED}❌ python-env nicht gefunden!${NC}"
    echo "Erstelle Python Environment..."
    python3 -m venv python-env
fi

# Activate and install uvicorn
echo "Aktiviere Python Environment..."
source python-env/bin/activate

echo "Installiere uvicorn und FastAPI..."
pip install --upgrade pip
pip install uvicorn fastapi

# Install from requirements-desktop if exists
if [ -f "$PROJECT_ROOT/backend/requirements-desktop.txt" ]; then
    echo "Installiere Backend Dependencies..."
    pip install -r "$PROJECT_ROOT/backend/requirements-desktop.txt"
fi

deactivate

# Verify
echo ""
if [ -f "python-env/bin/uvicorn" ]; then
    echo -e "${GREEN}✅ Uvicorn erfolgreich installiert${NC}"
    python-env/bin/uvicorn --version
else
    echo -e "${RED}❌ Uvicorn Installation fehlgeschlagen${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo "Prüfe alle Python Packages:"
echo "======================================"
source python-env/bin/activate
pip list | grep -E "uvicorn|fastapi|motor|metaapi"
deactivate

echo ""
echo -e "${GREEN}✅ Fertig!${NC}"
