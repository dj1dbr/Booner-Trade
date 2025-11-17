const { app, BrowserWindow } = require('electron');

app.on('ready', () => {
  console.log('✅ Electron ready!');
  
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false
    }
  });
  
  console.log('Loading: http://localhost:8001');
  win.loadURL('http://localhost:8001');
  
  win.webContents.on('did-finish-load', () => {
    console.log('✅ Page loaded!');
  });
  
  win.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`❌ Failed to load: ${errorCode} - ${errorDescription}`);
  });
});
