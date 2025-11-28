#!/bin/bash
set -e

echo "🚀 Booner Trade - Minimal Build (ohne embedded MongoDB)"
echo "========================================================"
echo ""
echo "HINWEIS: Diese Version benötigt MongoDB separat installiert!"
echo "          brew install mongodb-community"
echo ""

# 1. Cleanup
echo "🧹 Cleaning..."
rm -rf dist
rm -rf python-env
echo ""

# 2. Frontend
echo "📦 Building Frontend..."
cd ../frontend
yarn build
cd ../electron-app
echo ""

# 3. Python Environment
echo "📦 Creating Python Environment..."
python3 -m venv python-env
source python-env/bin/activate
pip install --upgrade pip --quiet
echo "📦 Installing requirements (Fallback-Mode)..."
# emergentintegrations only works in Emergent Platform
grep -v "^emergentintegrations" ../backend/requirements.txt > requirements-desktop.txt
pip install -r requirements-desktop.txt --quiet
rm requirements-desktop.txt
deactivate
echo ""

# 4. Icon & DMG Background
echo "🎨 Creating Icon & DMG Background..."
if command -v rsvg-convert &> /dev/null; then
    rsvg-convert -w 512 -h 512 assets/logo.svg -o assets/logo.png
    rsvg-convert -w 540 -h 380 assets/dmg-background.svg -o assets/dmg-background.png
    echo "✅ Icon & Background created"
else
    echo "⚠️  librsvg not found"
    echo "Creating minimal background with Python..."
    python3 -c "
from PIL import Image
img = Image.new('RGB', (540, 380), color='#0f172a')
img.save('assets/dmg-background.png')
" 2>/dev/null || echo "⚠️  Install Pillow: pip install Pillow"
fi
echo ""

# 5. Modifiziere main.js um MongoDB-Start zu überspringen
echo "⚙️  Configuring for external MongoDB..."
cp main.js main.js.backup

cat > main.js.temp << 'MAINJS'
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

const isDev = process.env.NODE_ENV === 'development';
const appPath = isDev ? __dirname : path.join(process.resourcesPath, 'app');
const backendPath = path.join(appPath, 'backend');

console.log('App paths:', { appPath, backendPath });

// Backend starten (MongoDB läuft extern)
async function startBackend() {
  return new Promise((resolve) => {
    const pythonPath = path.join(appPath, 'python', 'bin', 'python3');
    const serverPath = path.join(backendPath, 'server.py');
    
    console.log('Starting Backend from:', serverPath);
    
    const env = {
      ...process.env,
      MONGO_URL: 'mongodb://localhost:27017',
      DB_NAME: 'booner_trade_db',
      PORT: '8001'
    };

    backendProcess = spawn(pythonPath, [serverPath], {
      cwd: backendPath,
      env: env
    });

    backendProcess.stdout.on('data', (data) => {
      console.log('[Backend]:', data.toString());
      if (data.toString().includes('Uvicorn running')) {
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error('[Backend]:', data.toString());
    });

    setTimeout(() => resolve(), 8000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    icon: path.join(__dirname, 'assets', 'logo.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0f172a'
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(appPath, 'frontend', 'build', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  try {
    console.log('🚀 Starting Booner Trade...');
    console.log('📊 MongoDB should be running externally on port 27017');
    
    await startBackend();
    
    setTimeout(() => {
      createWindow();
    }, 2000);
    
  } catch (error) {
    console.error('❌ Failed to start:', error);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
MAINJS

mv main.js.temp main.js
echo "✅ Configured for external MongoDB"
echo ""

# 6. Package.json anpassen (MongoDB nicht einbetten)
echo "⚙️  Updating package.json..."
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
pkg.build.extraResources = pkg.build.extraResources.filter(r => 
  !r.to || !r.to.includes('mongodb')
);
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
console.log('✅ Removed MongoDB from build');
"
echo ""

# 7. Install & Build
echo "📦 Installing dependencies..."
yarn install --silent
echo ""

echo "🔨 Building App..."
yarn build:dmg

# 8. Restore original files
echo "🔄 Restoring original files..."
mv main.js.backup main.js
git checkout package.json 2>/dev/null || true

echo ""
echo "✅ =================================="
echo "✅  MINIMAL BUILD SUCCESSFUL!"
echo "✅ =================================="
echo ""
echo "⚠️  WICHTIG: Diese App benötigt MongoDB!"
echo "   Installation: brew install mongodb-community"
echo "   Start: brew services start mongodb-community"
echo ""
echo "📦 DMG Location:"
echo "   $(pwd)/dist/Booner Trade-1.0.0.dmg"
echo ""
