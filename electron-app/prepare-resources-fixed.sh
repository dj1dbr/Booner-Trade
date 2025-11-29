#!/bin/bash

# Booner Trade - FIXED Resource Preparation Script
# Automatically creates complete portable Python environment with all dependencies

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Booner Trade - FIXED Resource Prep"
echo "======================================"
echo ""

# 1. MongoDB herunterladen und vorbereiten
echo -e "${YELLOW}[1/4] MongoDB vorbereiten...${NC}"

MONGODB_DIR="$SCRIPT_DIR/mongodb-mac"

if [ -d "$MONGODB_DIR" ] && [ -f "$MONGODB_DIR/bin/mongod" ]; then
    echo -e "${GREEN}✅ MongoDB bereits vorhanden${NC}"
    MONGO_VERSION=$("$MONGODB_DIR/bin/mongod" --version | head -n1)
    echo "   Version: $MONGO_VERSION"
else
    echo -e "${BLUE}📥 MongoDB wird heruntergeladen...${NC}"
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        MONGODB_URL="https://fastdl.mongodb.org/osx/mongodb-macos-arm64-7.0.26.tgz"
    else
        MONGODB_URL="https://fastdl.mongodb.org/osx/mongodb-macos-x86_64-7.0.26.tgz"
    fi
    
    echo "Architecture: $ARCH"
    echo "Downloading from: $MONGODB_URL"
    
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR"
    
    curl -L -o mongodb.tgz "$MONGODB_URL"
    
    echo "Extracting MongoDB..."
    tar -xzf mongodb.tgz
    
    # Find the extracted directory
    MONGODB_EXTRACTED=$(find . -name "mongodb-macos-*" -type d | head -n1)
    
    if [ -z "$MONGODB_EXTRACTED" ]; then
        echo -e "${RED}❌ Failed to extract MongoDB${NC}"
        exit 1
    fi
    
    echo "Moving MongoDB to: $MONGODB_DIR"
    mkdir -p "$MONGODB_DIR"
    cp -r "$MONGODB_EXTRACTED/bin" "$MONGODB_DIR/"
    
    cd "$SCRIPT_DIR"
    rm -rf "$TMP_DIR"
    
    if [ -f "$MONGODB_DIR/bin/mongod" ]; then
        echo -e "${GREEN}✅ MongoDB successfully installed${NC}"
    else
        echo -e "${RED}❌ MongoDB installation failed${NC}"
        exit 1
    fi
fi

# 2. Python Environment mit allen Dependencies erstellen
echo ""
echo -e "${YELLOW}[2/4] Python Environment erstellen...${NC}"

PYTHON_DIR="$SCRIPT_DIR/python-env"

# Entferne altes, defektes Environment
if [ -d "$PYTHON_DIR" ]; then
    echo "Removing old Python environment..."
    rm -rf "$PYTHON_DIR"
fi

echo -e "${BLUE}📦 Creating fresh Python virtual environment...${NC}"

# Check for Python 3
PYTHON_CMD=""
for cmd in python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        echo "Found: $PYTHON_CMD"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "Using: $PYTHON_VERSION"

# Create virtual environment
echo "Creating venv..."
$PYTHON_CMD -m venv "$PYTHON_DIR"

# Activate environment
source "$PYTHON_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo ""
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
echo "This may take 3-5 minutes..."
echo ""

if [ -f "$PROJECT_ROOT/backend/requirements-desktop.txt" ]; then
    echo "Installing from requirements-desktop.txt"
    pip install -r "$PROJECT_ROOT/backend/requirements-desktop.txt"
elif [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
    echo "⚠️  Using requirements.txt, filtering out emergentintegrations..."
    grep -v "emergentintegrations" "$PROJECT_ROOT/backend/requirements.txt" > /tmp/requirements-filtered.txt
    pip install -r /tmp/requirements-filtered.txt
    rm /tmp/requirements-filtered.txt
else
    echo "Installing minimal dependencies..."
    pip install fastapi==0.110.1 uvicorn==0.25.0 motor==3.3.1 python-dotenv==1.2.1 metaapi_cloud_sdk==29.1.0
fi

# Verify critical packages
echo ""
echo -e "${BLUE}🔍 Verifying installation...${NC}"
MISSING_PACKAGES=()

for package in uvicorn fastapi motor; do
    if ! pip show $package &> /dev/null; then
        MISSING_PACKAGES+=($package)
    else
        VERSION=$(pip show $package | grep Version | cut -d' ' -f2)
        echo -e "${GREEN}✅ $package $VERSION${NC}"
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    deactivate
    exit 1
fi

# Check uvicorn executable
if [ -f "$PYTHON_DIR/bin/uvicorn" ]; then
    echo -e "${GREEN}✅ uvicorn executable found${NC}"
else
    echo -e "${RED}❌ uvicorn executable not found!${NC}"
    deactivate
    exit 1
fi

deactivate

echo -e "${GREEN}✅ Python Environment successfully created${NC}"

# 3. Backend vorbereiten
echo ""
echo -e "${YELLOW}[3/4] Backend prüfen...${NC}"

if [ -d "$PROJECT_ROOT/backend" ] && [ -f "$PROJECT_ROOT/backend/server.py" ]; then
    echo -e "${GREEN}✅ Backend gefunden${NC}"
    
    # Copy backend to electron-app for packaging
    if [ -d "$SCRIPT_DIR/backend" ]; then
        rm -rf "$SCRIPT_DIR/backend"
    fi
    
    echo "Copying backend files..."
    cp -r "$PROJECT_ROOT/backend" "$SCRIPT_DIR/"
    
    # Remove unnecessary files from backend copy
    rm -f "$SCRIPT_DIR/backend/__pycache__" 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/backend/.pytest_cache" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Backend copied to electron-app${NC}"
else
    echo -e "${RED}❌ Backend not found in: $PROJECT_ROOT/backend${NC}"
    exit 1
fi

# 4. Frontend Build prüfen und kopieren
echo ""
echo -e "${YELLOW}[4/4] Frontend Build prüfen...${NC}"

if [ -d "$PROJECT_ROOT/frontend/build" ] && [ -f "$PROJECT_ROOT/frontend/build/index.html" ]; then
    echo -e "${GREEN}✅ Frontend Build gefunden${NC}"
    
    # Copy frontend build
    if [ -d "$SCRIPT_DIR/frontend" ]; then
        rm -rf "$SCRIPT_DIR/frontend"
    fi
    
    echo "Copying frontend build..."
    mkdir -p "$SCRIPT_DIR/frontend"
    cp -r "$PROJECT_ROOT/frontend/build" "$SCRIPT_DIR/frontend/"
    
    echo -e "${GREEN}✅ Frontend copied to electron-app${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend Build nicht gefunden${NC}"
    echo "Building frontend now..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Configure for desktop
    cat > .env.production << 'EOF'
PUBLIC_URL=.
REACT_APP_BACKEND_URL=http://localhost:8000
EOF
    
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        yarn install
    fi
    
    echo "Building frontend..."
    yarn build
    
    if [ -f "build/index.html" ]; then
        echo -e "${GREEN}✅ Frontend built successfully${NC}"
        
        # Copy to electron-app
        mkdir -p "$SCRIPT_DIR/frontend"
        cp -r build "$SCRIPT_DIR/frontend/"
    else
        echo -e "${RED}❌ Frontend build failed!${NC}"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
fi

# Final Summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ ALL RESOURCES READY!${NC}"
echo "======================================"
echo ""
echo "Resource Locations:"
echo -e "  ${GREEN}✅${NC} MongoDB:  $MONGODB_DIR"
echo -e "  ${GREEN}✅${NC} Python:   $PYTHON_DIR"
echo -e "  ${GREEN}✅${NC} Backend:  $SCRIPT_DIR/backend"
echo -e "  ${GREEN}✅${NC} Frontend: $SCRIPT_DIR/frontend/build"
echo ""

# Verify all critical files
echo "Critical Files Check:"
FILES_TO_CHECK=(
    "$MONGODB_DIR/bin/mongod"
    "$PYTHON_DIR/bin/python3"
    "$PYTHON_DIR/bin/uvicorn"
    "$SCRIPT_DIR/backend/server.py"
    "$SCRIPT_DIR/frontend/build/index.html"
)

ALL_OK=true
for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ] || [ -x "$file" ]; then
        echo -e "  ${GREEN}✅${NC} $file"
    else
        echo -e "  ${RED}❌${NC} $file"
        ALL_OK=false
    fi
done

echo ""
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}🎉 Ready to build!${NC}"
    echo ""
    echo "Next step:"
    echo "  cd $SCRIPT_DIR"
    echo "  ./build.sh"
else
    echo -e "${RED}❌ Some files are missing!${NC}"
    exit 1
fi
echo ""
