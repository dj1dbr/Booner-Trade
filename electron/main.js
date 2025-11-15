const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

// Backend starten
function startBackend() {
  console.log('🚀 Starting Backend Server...');
  
  // Start FastAPI backend
  backendProcess = spawn('python', [
    path.join(__dirname, '../backend/server.py')
  ], {
    cwd: path.join(__dirname, '../backend'),
    env: { ...process.env }
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.log(`[Backend Error] ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

// Hauptfenster erstellen
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true
    },
    backgroundColor: '#0f172a',
    title: 'WTI Smart Trader',
    show: false
  });

  // Menü entfernen (optional - für cleaner Look)
  Menu.setApplicationMenu(null);

  // Warte bis Backend bereit ist (5 Sekunden - Backend braucht Zeit zum Starten)
  setTimeout(() => {
    // Lade die React-App vom lokalen Backend-Server
    // Das Backend liefert das Frontend aus (siehe server.py - Static Files)
    const appURL = 'http://localhost:8001';
    
    console.log(`📱 Loading App from: ${appURL}`);
    mainWindow.loadURL(appURL);
    
    // Zeige Fenster wenn fertig geladen
    mainWindow.once('ready-to-show', () => {
      mainWindow.show();
      console.log('✅ App is ready!');
    });

    // DevTools nur in Entwicklung öffnen
    if (process.env.ELECTRON_DEV || process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  }, 3000);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App bereit
app.on('ready', () => {
  console.log('🎯 Electron App Starting...');
  startBackend();
  
  // Warte 5 Sekunden damit Backend vollständig starten kann
  setTimeout(createWindow, 5000);
});

// Alle Fenster geschlossen
app.on('window-all-closed', () => {
  // Backend beenden
  if (backendProcess) {
    console.log('🛑 Stopping Backend...');
    backendProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// App wird beendet
app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
