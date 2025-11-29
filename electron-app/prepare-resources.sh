#!/bin/bash

# Booner Trade - Prepare Resources for Desktop Build
# Downloads and prepares MongoDB, Python, and all required resources

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Booner Trade - Resource Preparation"
echo "======================================"
echo ""

# 1. MongoDB herunterladen
echo -e "${YELLOW}[1/4] MongoDB vorbereiten...${NC}"

MONGODB_DIR="$SCRIPT_DIR/mongodb-mac"

if [ -d "$MONGODB_DIR" ] && [ -f "$MONGODB_DIR/bin/mongod" ]; then
    echo -e "${GREEN}✅ MongoDB bereits vorhanden${NC}"
else
    echo "MongoDB wird für macOS heruntergeladen..."
    echo ""
    echo -e "${YELLOW}⚠️  WICHTIG: MongoDB muss manuell heruntergeladen werden!${NC}"
    echo ""
    echo "Schritte:"
    echo "1. Gehe zu: https://www.mongodb.com/try/download/community"
    echo "2. Wähle:"
    echo "   - Version: 7.0 (oder aktuell)"
    echo "   - Platform: macOS"
    echo "   - Package: TGZ"
    echo "   - Architecture: $(uname -m)"
    echo "3. Download und entpacken"
    echo "4. Verschiebe den Inhalt nach:"
    echo "   $MONGODB_DIR"
    echo ""
    echo "Beispiel Befehle:"
    echo "  cd ~/Downloads"
    echo "  tar -xzf mongodb-macos-*-7.0.*.tgz"
    echo "  mkdir -p '$MONGODB_DIR'"
    echo "  cp -r mongodb-macos-*/bin '$MONGODB_DIR/'"
    echo ""
    
    read -p "Drücke ENTER wenn MongoDB vorbereitet ist..."
    
    if [ ! -f "$MONGODB_DIR/bin/mongod" ]; then
        echo -e "${RED}❌ MongoDB nicht gefunden!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ MongoDB gefunden${NC}"
fi

# 2. Python Environment vorbereiten
echo ""
echo -e "${YELLOW}[2/4] Python Environment vorbereiten...${NC}"

PYTHON_DIR="$SCRIPT_DIR/python-env"

if [ -d "$PYTHON_DIR" ] && [ -f "$PYTHON_DIR/bin/python3" ]; then
    echo -e "${GREEN}✅ Python Environment bereits vorhanden${NC}"
else
    echo "Python Portable Environment wird erstellt..."
    echo ""
    echo "Option A: System Python verwenden (einfach, aber nicht portabel)"
    echo "Option B: Eigenständiges Python erstellen (komplex, aber besser)"
    echo ""
    
    read -p "Wähle Option (A/B): " choice
    
    if [ "$choice" = "A" ] || [ "$choice" = "a" ]; then
        # Verwende System Python
        echo "Verwende System Python..."
        SYSTEM_PYTHON=$(which python3)
        
        if [ -z "$SYSTEM_PYTHON" ]; then
            echo -e "${RED}❌ System Python nicht gefunden!${NC}"
            exit 1
        fi
        
        echo "Erstelle Symlinks zu System Python..."
        mkdir -p "$PYTHON_DIR/bin"
        ln -sf "$SYSTEM_PYTHON" "$PYTHON_DIR/bin/python3"
        ln -sf "$(dirname $SYSTEM_PYTHON)/pip3" "$PYTHON_DIR/bin/pip3" 2>/dev/null || true
        
        # Installiere uvicorn global
        pip3 install uvicorn fastapi --user
        ln -sf "$(dirname $SYSTEM_PYTHON)/uvicorn" "$PYTHON_DIR/bin/uvicorn" 2>/dev/null || \
        ln -sf "$HOME/.local/bin/uvicorn" "$PYTHON_DIR/bin/uvicorn" 2>/dev/null || true
        
        echo -e "${YELLOW}⚠️  WARNUNG: Verwendet System Python (nicht portabel auf anderen Macs)${NC}"
        
    else
        echo "Erstelle eigenständiges Python Environment..."
        
        # Erstelle Virtual Environment
        python3 -m venv "$PYTHON_DIR"
        
        # Aktiviere und installiere Requirements
        source "$PYTHON_DIR/bin/activate"
        pip install --upgrade pip
        
        # Verwende DESKTOP requirements (ohne emergentintegrations!)
        if [ -f "$PROJECT_ROOT/backend/requirements-desktop.txt" ]; then
            echo "Installing from requirements-desktop.txt (ohne Emergent Dependencies)..."
            pip install -r "$PROJECT_ROOT/backend/requirements-desktop.txt"
        elif [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
            echo "⚠️  WARNING: Using requirements.txt (may include Emergent dependencies)"
            echo "Installing and filtering out emergentintegrations..."
            grep -v "emergentintegrations" "$PROJECT_ROOT/backend/requirements.txt" > /tmp/requirements-filtered.txt
            pip install -r /tmp/requirements-filtered.txt
            rm /tmp/requirements-filtered.txt
        else
            # Minimale Installation
            echo "No requirements file found, installing minimal dependencies..."
            pip install fastapi uvicorn motor python-dotenv metaapi-cloud-sdk
        fi
        
        deactivate
        
        echo -e "${GREEN}✅ Python Virtual Environment erstellt${NC}"
    fi
fi

# 3. Backend vorbereiten
echo ""
echo -e "${YELLOW}[3/4] Backend prüfen...${NC}"

if [ -d "$PROJECT_ROOT/backend" ] && [ -f "$PROJECT_ROOT/backend/server.py" ]; then
    echo -e "${GREEN}✅ Backend gefunden${NC}"
else
    echo -e "${RED}❌ Backend nicht gefunden in: $PROJECT_ROOT/backend${NC}"
    exit 1
fi

# 4. Frontend Build prüfen
echo ""
echo -e "${YELLOW}[4/4] Frontend Build prüfen...${NC}"

if [ -d "$PROJECT_ROOT/frontend/build" ] && [ -f "$PROJECT_ROOT/frontend/build/index.html" ]; then
    echo -e "${GREEN}✅ Frontend Build gefunden${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend Build nicht gefunden${NC}"
    echo "Soll Frontend jetzt gebaut werden? (J/N)"
    read -p "> " build_frontend
    
    if [ "$build_frontend" = "J" ] || [ "$build_frontend" = "j" ]; then
        cd "$PROJECT_ROOT/frontend"
        
        # Configure for desktop
        cat > .env << 'EOF'
PUBLIC_URL=.
REACT_APP_BACKEND_URL=http://localhost:8000
EOF
        
        echo "Installing frontend dependencies..."
        yarn install
        
        echo "Building frontend..."
        yarn build
        
        echo -e "${GREEN}✅ Frontend gebaut${NC}"
    else
        echo -e "${RED}❌ Frontend Build wird benötigt!${NC}"
        exit 1
    fi
fi

# 5. Zusammenfassung
echo ""
echo "======================================"
echo -e "${GREEN}✅ Alle Ressourcen vorbereitet!${NC}"
echo "======================================"
echo ""
echo "Verzeichnisse:"
echo "  ✅ MongoDB:  $MONGODB_DIR"
echo "  ✅ Python:   $PYTHON_DIR"
echo "  ✅ Backend:  $PROJECT_ROOT/backend"
echo "  ✅ Frontend: $PROJECT_ROOT/frontend/build"
echo ""
echo "Nächster Schritt:"
echo "  cd $SCRIPT_DIR"
echo "  ./build.sh"
echo ""
