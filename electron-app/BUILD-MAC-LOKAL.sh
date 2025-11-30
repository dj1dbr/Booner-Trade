#!/bin/bash

################################################################################
# Booner Trade - LOKALER MAC BUILD
# Dieses Script läuft DIREKT auf Ihrem Mac und erstellt eine funktionierende App
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════"
echo "  Booner Trade - LOKALER MAC BUILD"
echo "═══════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ============================================================================
# SCHRITT 1: System-Prüfung
# ============================================================================
echo -e "${BLUE}[1/8] Systemprüfung...${NC}"

# macOS Check
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ Dieses Script muss auf macOS laufen!${NC}"
    exit 1
fi

# Architecture detection
ARCH=$(uname -m)
echo -e "${GREEN}✅ macOS erkannt (Architektur: $ARCH)${NC}"

# Node.js Check
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js nicht gefunden!${NC}"
    echo "Installation: https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✅ Node.js $(node -v)${NC}"

# Yarn Check
if ! command -v yarn &> /dev/null; then
    echo -e "${YELLOW}⚠️  Yarn nicht gefunden, installiere...${NC}"
    npm install -g yarn
fi
echo -e "${GREEN}✅ Yarn $(yarn -v)${NC}"

# Python Check
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        PYTHON_VERSION=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 9 ]; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Python 3.9+ nicht gefunden!${NC}"
    echo "Installation: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

echo ""

# ============================================================================
# SCHRITT 2: MongoDB herunterladen
# ============================================================================
echo -e "${BLUE}[2/8] MongoDB für macOS vorbereiten...${NC}"

MONGODB_DIR="$SCRIPT_DIR/mongodb-mac"

if [ -f "$MONGODB_DIR/bin/mongod" ]; then
    echo -e "${GREEN}✅ MongoDB bereits vorhanden${NC}"
else
    echo "Downloade MongoDB für $ARCH..."
    
    # URL basierend auf Architektur
    if [ "$ARCH" = "arm64" ]; then
        MONGODB_URL="https://fastdl.mongodb.org/osx/mongodb-macos-arm64-7.0.26.tgz"
    else
        MONGODB_URL="https://fastdl.mongodb.org/osx/mongodb-macos-x86_64-7.0.26.tgz"
    fi
    
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR"
    
    curl -L -o mongodb.tgz "$MONGODB_URL"
    tar -xzf mongodb.tgz
    
    MONGODB_EXTRACTED=$(find . -name "mongodb-macos-*" -type d | head -1)
    
    if [ -z "$MONGODB_EXTRACTED" ]; then
        echo -e "${RED}❌ MongoDB Download fehlgeschlagen${NC}"
        exit 1
    fi
    
    mkdir -p "$MONGODB_DIR"
    cp -r "$MONGODB_EXTRACTED/bin" "$MONGODB_DIR/"
    
    cd "$SCRIPT_DIR"
    rm -rf "$TMP_DIR"
    
    if [ -f "$MONGODB_DIR/bin/mongod" ]; then
        echo -e "${GREEN}✅ MongoDB erfolgreich heruntergeladen${NC}"
    else
        echo -e "${RED}❌ MongoDB Installation fehlgeschlagen${NC}"
        exit 1
    fi
fi

echo ""

# ============================================================================
# SCHRITT 3: Python Packages installieren (LOKAL!)
# ============================================================================
echo -e "${BLUE}[3/8] Python Packages lokal installieren...${NC}"

PYTHON_PACKAGES_DIR="$SCRIPT_DIR/python-packages"
rm -rf "$PYTHON_PACKAGES_DIR"
mkdir -p "$PYTHON_PACKAGES_DIR"

echo "Installiere Python Dependencies nach $PYTHON_PACKAGES_DIR..."

# Installiere alle Packages in einen lokalen Ordner
if [ -f "$PROJECT_ROOT/backend/requirements-desktop.txt" ]; then
    $PYTHON_CMD -m pip install --target="$PYTHON_PACKAGES_DIR" -r "$PROJECT_ROOT/backend/requirements-desktop.txt" --upgrade
else
    echo -e "${YELLOW}⚠️  requirements-desktop.txt nicht gefunden, installiere Basis-Packages${NC}"
    $PYTHON_CMD -m pip install --target="$PYTHON_PACKAGES_DIR" \
        fastapi==0.110.1 \
        uvicorn==0.25.0 \
        motor==3.3.1 \
        python-dotenv==1.2.1 \
        metaapi_cloud_sdk==29.1.0 \
        --upgrade
fi

# Prüfe kritische Packages
echo ""
echo "Verifiziere Installation..."
MISSING=()

for pkg in uvicorn fastapi motor; do
    if [ ! -d "$PYTHON_PACKAGES_DIR/$pkg" ]; then
        MISSING+=($pkg)
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "${RED}❌ Fehlende Packages: ${MISSING[*]}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Alle Python Packages installiert${NC}"
echo ""

# ============================================================================
# SCHRITT 4: Python Starter Script erstellen
# ============================================================================
echo -e "${BLUE}[4/8] Python Launcher erstellen...${NC}"

PYTHON_LAUNCHER="$SCRIPT_DIR/python-launcher"
mkdir -p "$PYTHON_LAUNCHER/bin"

# Erstelle ein Wrapper-Script für Python
cat > "$PYTHON_LAUNCHER/bin/python3" << EOF
#!/bin/bash
SCRIPT_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
PACKAGES_DIR="\$(dirname "\$(dirname "\$SCRIPT_DIR")")/python-packages"
export PYTHONPATH="\$PACKAGES_DIR:\$PYTHONPATH"
exec $PYTHON_CMD "\$@"
EOF

chmod +x "$PYTHON_LAUNCHER/bin/python3"

# Erstelle Wrapper für uvicorn
cat > "$PYTHON_LAUNCHER/bin/uvicorn" << EOF
#!/bin/bash
SCRIPT_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
PACKAGES_DIR="\$(dirname "\$(dirname "\$SCRIPT_DIR")")/python-packages"
export PYTHONPATH="\$PACKAGES_DIR:\$PYTHONPATH"
exec $PYTHON_CMD -m uvicorn "\$@"
EOF

chmod +x "$PYTHON_LAUNCHER/bin/uvicorn"

# Test uvicorn
if "$PYTHON_LAUNCHER/bin/uvicorn" --version &> /dev/null; then
    echo -e "${GREEN}✅ Python Launcher funktioniert${NC}"
else
    echo -e "${RED}❌ Python Launcher Test fehlgeschlagen${NC}"
    exit 1
fi

echo ""

# ============================================================================
# SCHRITT 5: Backend kopieren
# ============================================================================
echo -e "${BLUE}[5/8] Backend vorbereiten...${NC}"

if [ -d "$SCRIPT_DIR/backend" ]; then
    rm -rf "$SCRIPT_DIR/backend"
fi

cp -r "$PROJECT_ROOT/backend" "$SCRIPT_DIR/"

# Entferne unnötige Dateien
find "$SCRIPT_DIR/backend" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$SCRIPT_DIR/backend" -name "*.pyc" -delete 2>/dev/null || true

echo -e "${GREEN}✅ Backend kopiert${NC}"
echo ""

# ============================================================================
# SCHRITT 6: Frontend bauen
# ============================================================================
echo -e "${BLUE}[6/8] Frontend bauen...${NC}"

cd "$PROJECT_ROOT/frontend"

# Backup .env
if [ -f .env ]; then
    cp .env .env.backup
fi

# Desktop .env
cat > .env << 'EOF'
PUBLIC_URL=.
REACT_APP_BACKEND_URL=http://localhost:8000
EOF

# Dependencies
if [ ! -d "node_modules" ]; then
    echo "Installiere Frontend Dependencies..."
    yarn install
fi

# Build
echo "Building Frontend..."
yarn build

if [ ! -f "build/index.html" ]; then
    echo -e "${RED}❌ Frontend Build fehlgeschlagen${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend gebaut ($(du -sh build | cut -f1))${NC}"

# Frontend nach electron-app kopieren
rm -rf "$SCRIPT_DIR/frontend"
mkdir -p "$SCRIPT_DIR/frontend"
cp -r build "$SCRIPT_DIR/frontend/"

# .env wiederherstellen
if [ -f .env.backup ]; then
    mv .env.backup .env
fi

cd "$SCRIPT_DIR"
echo ""

# ============================================================================
# SCHRITT 7: Assets und Icons vorbereiten
# ============================================================================
echo -e "${BLUE}[7/8] Assets und Icons vorbereiten...${NC}"

ASSETS_DIR="$SCRIPT_DIR/assets"
mkdir -p "$ASSETS_DIR"

# Erstelle einfaches Icon (falls nicht vorhanden)
if [ ! -f "$ASSETS_DIR/icon.png" ]; then
    echo "⚠️  Kein Icon gefunden, erstelle Platzhalter..."
    # Erstelle ein 512x512 PNG mit Text
    if command -v sips &> /dev/null; then
        # macOS hat sips - nutzen wir das
        sips -z 512 512 -c 512 512 --setProperty format png "$ASSETS_DIR/logo.png" --out "$ASSETS_DIR/icon.png" 2>/dev/null || cp "$ASSETS_DIR/logo.png" "$ASSETS_DIR/icon.png" 2>/dev/null || touch "$ASSETS_DIR/icon.png"
    else
        cp "$ASSETS_DIR/logo.png" "$ASSETS_DIR/icon.png" 2>/dev/null || touch "$ASSETS_DIR/icon.png"
    fi
fi

# DMG Background
if [ ! -f "$ASSETS_DIR/dmg-background.png" ]; then
    echo "⚠️  DMG Background nicht gefunden, erstelle Platzhalter..."
    touch "$ASSETS_DIR/dmg-background.png"
fi

echo -e "${GREEN}✅ Assets bereit${NC}"
echo ""

# ============================================================================
# SCHRITT 8: Electron App bauen
# ============================================================================
echo -e "${BLUE}[8/8] Electron App bauen...${NC}"

cd "$SCRIPT_DIR"

# Electron Dependencies
if [ ! -d "node_modules" ]; then
    echo "Installiere Electron Dependencies..."
    yarn install
fi

echo "Baue macOS App..."
echo "(Dies kann 5-10 Minuten dauern...)"
echo ""

# Build nur für aktuelle Architektur
if [ "$ARCH" = "arm64" ]; then
    yarn build:dmg --arm64
else
    yarn build:dmg --x64
fi

# ============================================================================
# FINAL: Validierung
# ============================================================================
echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "${GREEN}✅ BUILD ABGESCHLOSSEN!${NC}"
echo "═══════════════════════════════════════════════════════"
echo ""

# Finde DMG
DMG_FILE=$(find dist -name "*.dmg" 2>/dev/null | head -1)

if [ -z "$DMG_FILE" ]; then
    echo -e "${YELLOW}⚠️  DMG nicht gefunden, aber .app sollte vorhanden sein:${NC}"
    APP_FILE=$(find dist -name "*.app" 2>/dev/null | head -1)
    if [ -n "$APP_FILE" ]; then
        echo ""
        echo "📦 App: $APP_FILE"
        echo "Größe: $(du -sh "$APP_FILE" | cut -f1)"
        echo ""
        echo "Installation:"
        echo "  cp -r '$APP_FILE' /Applications/"
        echo "  xattr -cr '/Applications/$(basename "$APP_FILE")'"
    fi
else
    echo "📦 DMG: $DMG_FILE"
    echo "Größe: $(du -sh "$DMG_FILE" | cut -f1)"
    echo ""
    echo "Installation:"
    echo "  1. Öffne: open '$DMG_FILE'"
    echo "  2. Ziehe 'Booner Trade' nach Applications"
    echo "  3. Öffne Terminal und führe aus:"
    echo "     xattr -cr '/Applications/Booner Trade.app'"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
