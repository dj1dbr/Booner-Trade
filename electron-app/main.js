const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');

let mainWindow;
let backendProcess;
let mongoProcess;

// Setup logging to file
const logDir = path.join(app.getPath('logs'));
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}
const logFile = path.join(logDir, 'main.log');
const errorLogFile = path.join(logDir, 'error.log');

function log(message, isError = false) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  console.log(message);
  
  try {
    fs.appendFileSync(isError ? errorLogFile : logFile, logMessage);
  } catch (err) {
    console.error('Failed to write to log:', err);
  }
}

function logError(message, error) {
  const errorMessage = error ? `${message}: ${error.stack || error}` : message;
  log(errorMessage, true);
  console.error(errorMessage);
}

// Pfade für portable Installation
const isDev = process.env.NODE_ENV === 'development';
const appPath = isDev ? __dirname : path.join(process.resourcesPath, 'app');
const mongoPath = path.join(appPath, 'mongodb');
const dbPath = path.join(app.getPath('userData'), 'database');
const backendPath = path.join(appPath, 'backend');

log('=== Booner Trade Starting ===');
log(`App paths: ${JSON.stringify({ appPath, mongoPath, dbPath, backendPath }, null, 2)}`);

// MongoDB starten
async function startMongoDB() {
  return new Promise((resolve, reject) => {
    try {
      // Erstelle DB-Verzeichnis wenn nicht vorhanden
      if (!fs.existsSync(dbPath)) {
        log(`Creating DB directory: ${dbPath}`);
        fs.mkdirSync(dbPath, { recursive: true });
      }

      const mongodPath = path.join(mongoPath, 'bin', 'mongod');
      
      // Check if MongoDB binary exists
      if (!fs.existsSync(mongodPath)) {
        const error = `MongoDB binary not found at: ${mongodPath}`;
        logError(error);
        reject(new Error(error));
        return;
      }
      
      log(`Starting MongoDB from: ${mongodPath}`);
      log(`DB Path: ${dbPath}`);
      
      mongoProcess = spawn(mongodPath, [
        '--dbpath', dbPath,
        '--port', '27017',
        '--bind_ip', '127.0.0.1',
        '--noauth'
      ]);

      mongoProcess.stdout.on('data', (data) => {
        const message = data.toString();
        log(`MongoDB: ${message.trim()}`);
        if (message.includes('Waiting for connections')) {
          log('✅ MongoDB ready');
          resolve();
        }
      });

      mongoProcess.stderr.on('data', (data) => {
        const message = data.toString();
        logError(`MongoDB stderr: ${message.trim()}`);
      });

      mongoProcess.on('error', (error) => {
        logError('Failed to start MongoDB', error);
        reject(error);
      });

      mongoProcess.on('exit', (code) => {
        logError(`MongoDB process exited with code: ${code}`);
      });

      // Timeout nach 10 Sekunden
      setTimeout(() => {
        if (mongoProcess && !mongoProcess.killed) {
          log('MongoDB timeout reached, assuming it started');
          resolve();
        }
      }, 10000);
    } catch (error) {
      logError('MongoDB startup error', error);
      reject(error);
    }
  });
}

// Backend (FastAPI) starten
async function startBackend() {
  return new Promise((resolve, reject) => {
    try {
      const pythonPath = path.join(appPath, 'python', 'bin', 'python3');
      const serverPath = path.join(backendPath, 'server.py');
      
      // Check if backend files exist
      if (!fs.existsSync(serverPath)) {
        const error = `Backend server.py not found at: ${serverPath}`;
        logError(error);
        reject(new Error(error));
        return;
      }
      
      log(`Starting Backend from: ${serverPath}`);
      
      // Setze Environment Variables
      const env = {
        ...process.env,
        MONGO_URL: 'mongodb://localhost:27017',
        DB_NAME: 'booner_trade_db',
        PORT: '8000'
      };

      // Backend muss mit uvicorn gestartet werden, nicht direkt mit python
      const uvicornPath = path.join(appPath, 'python', 'bin', 'uvicorn');
      
      // Check if uvicorn exists
      if (!fs.existsSync(uvicornPath)) {
        const error = `Uvicorn not found at: ${uvicornPath}`;
        logError(error);
        reject(new Error(error));
        return;
      }
      
      log(`Using Uvicorn at: ${uvicornPath}`);
      log(`Backend directory: ${backendPath}`);
      
      backendProcess = spawn(uvicornPath, [
        'server:app',
        '--host', '0.0.0.0',
        '--port', '8000'
      ], {
        cwd: backendPath,
        env: env
      });

      backendProcess.stdout.on('data', (data) => {
        const message = data.toString();
        log(`Backend: ${message.trim()}`);
        if (message.includes('Uvicorn running') || message.includes('Application startup complete')) {
          log('✅ Backend ready');
          resolve();
        }
      });

      backendProcess.stderr.on('data', (data) => {
        const message = data.toString();
        logError(`Backend stderr: ${message.trim()}`);
      });

      backendProcess.on('error', (error) => {
        logError('Backend failed to start', error);
        reject(error);
      });

      backendProcess.on('exit', (code) => {
        logError(`Backend process exited with code: ${code}`);
      });

      // Timeout für Backend Start
      setTimeout(() => {
        log('Backend timeout reached, assuming it started');
        resolve();
      }, 8000);
    } catch (error) {
      logError('Backend startup error', error);
      reject(error);
    }
  });
}

// Main Window erstellen
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    icon: path.join(__dirname, 'assets', 'logo.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0f172a'
  });

  // Lade React App (läuft auf Port 3000 im Dev oder als statische Files)
  if (isDev) {
    log('🔧 Development Mode - Loading from localhost:3000');
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    const indexPath = path.join(appPath, 'frontend', 'build', 'index.html');
    log(`📦 Production Mode - Loading from: ${indexPath}`);
    
    // Prüfe ob index.html existiert
    if (fs.existsSync(indexPath)) {
      log('✅ index.html found');
      mainWindow.loadFile(indexPath);
    } else {
      logError(`❌ index.html NOT FOUND at: ${indexPath}`);
      const buildPath = path.join(appPath, 'frontend', 'build');
      if (fs.existsSync(buildPath)) {
        log(`Available files: ${fs.readdirSync(buildPath).join(', ')}`);
      } else {
        logError(`❌ Build folder does not exist: ${buildPath}`);
      }
      
      // Zeige Fehlermeldung im Fenster
      mainWindow.loadURL(`data:text/html,
        <html>
          <body style="background:#0f172a;color:white;font-family:Arial;padding:40px;text-align:center;">
            <h1>⚠️ Frontend Build Missing</h1>
            <p>The React frontend was not found in the app package.</p>
            <p style="color:#ef4444;">Expected: ${indexPath}</p>
            <br>
            <p>Please rebuild the app:</p>
            <pre style="background:#1e293b;padding:20px;border-radius:8px;text-align:left;">
cd frontend
yarn build
cd ../electron-app
yarn build:dmg
            </pre>
          </body>
        </html>
      `);
    }
  }

  // Debug: Log WebContents events
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    logError(`Failed to load page: ${errorCode} - ${errorDescription}`);
  });

  mainWindow.webContents.on('did-finish-load', () => {
    log('✅ Page loaded successfully');
  });

  mainWindow.webContents.on('crashed', () => {
    logError('Renderer process crashed!');
  });

  mainWindow.on('unresponsive', () => {
    logError('Window became unresponsive');
  });

  mainWindow.on('closed', () => {
    log('Window closed');
    mainWindow = null;
  });
}

// Global error handlers
process.on('uncaughtException', (error) => {
  logError('Uncaught Exception', error);
});

process.on('unhandledRejection', (reason, promise) => {
  logError(`Unhandled Rejection at: ${promise}, reason: ${reason}`);
});

// App Lifecycle
app.on('ready', async () => {
  try {
    log('🚀 Starting Booner Trade...');
    log(`Electron version: ${process.versions.electron}`);
    log(`Node version: ${process.versions.node}`);
    log(`Platform: ${process.platform} ${process.arch}`);
    
    // 1. Starte MongoDB
    log('📦 Starting MongoDB...');
    await startMongoDB();
    
    // 2. Starte Backend
    log('⚙️  Starting Backend...');
    await startBackend();
    
    // 3. Warte kurz, dann öffne Window
    setTimeout(() => {
      log('🖥️  Opening Window...');
      createWindow();
    }, 2000);
    
  } catch (error) {
    logError('❌ Startup failed', error);
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

// Cleanup beim Beenden
app.on('before-quit', (event) => {
  console.log('🛑 Shutting down...');
  
  if (backendProcess) {
    console.log('Stopping Backend...');
    backendProcess.kill();
  }
  
  if (mongoProcess) {
    console.log('Stopping MongoDB...');
    mongoProcess.kill();
  }
});

// IPC Communication (für Settings, etc.)
ipcMain.handle('get-app-path', () => {
  return app.getPath('userData');
});
