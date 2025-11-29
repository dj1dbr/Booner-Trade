# Booner Trade - Lokale Installation & Build (macOS)

## Voraussetzungen

1. **Node.js** (v18 oder höher)
   ```bash
   # Check Version:
   node -v
   
   # Falls nicht installiert:
   # Download von https://nodejs.org/
   ```

2. **Yarn** Package Manager
   ```bash
   # Check Version:
   yarn -v
   
   # Falls nicht installiert:
   npm install -g yarn
   ```

3. **Projekt herunterladen**
   ```bash
   # Von Emergent exportieren oder Git Clone
   # Stelle sicher, dass du folgende Struktur hast:
   
   Booner-Trade/
   ├── backend/
   ├── frontend/
   └── electron-app/
   ```

## Build-Prozess

### Schritt 1: In electron-app Verzeichnis wechseln
```bash
cd /pfad/zu/Booner-Trade/electron-app
```

### Schritt 2: Build-Readiness Check (optional)
```bash
./test-build.sh
```

Dies prüft:
- ✅ Node.js & Yarn installiert
- ✅ Frontend & Backend Verzeichnisse vorhanden
- ✅ Electron App Dateien vorhanden
- ✅ Assets vorhanden
- ✅ Ausreichend Speicherplatz

### Schritt 3: Build ausführen
```bash
./build.sh
```

**Das Script macht automatisch:**
1. ✅ Konfiguriert Frontend für Port 8000
2. ✅ Baut React Production Build (~2-3 Min)
3. ✅ Installiert Electron Dependencies
4. ✅ Erstellt DMG-Hintergrund (falls nötig)
5. ✅ Baut macOS DMG (~5-10 Min)
6. ✅ Stellt original .env wieder her

**Gesamtdauer:** ~10-15 Minuten

### Schritt 4: DMG finden
```bash
# Die fertige DMG ist in:
ls -lh dist/*.dmg
```

Mögliche Namen:
- `Booner Trade-1.0.0.dmg` (Universal)
- `Booner Trade-1.0.0-arm64.dmg` (Apple Silicon)
- `Booner Trade-1.0.0-x64.dmg` (Intel)

## Installation der App

### DMG öffnen und installieren
```bash
# DMG öffnen:
open "dist/Booner Trade-1.0.0*.dmg"
```

1. Drag & Drop die App nach `/Applications`
2. App öffnen (Rechtsklick → Öffnen beim ersten Mal)
3. macOS Sicherheitswarnung akzeptieren

### Sicherheitswarnung umgehen
Falls macOS die App blockiert:
```bash
xattr -cr "/Applications/Booner Trade.app"
```

## Troubleshooting

### "bash: ./build.sh: Permission denied"
```bash
chmod +x build.sh
chmod +x test-build.sh
./build.sh
```

### "Node.js not found"
Installiere Node.js von: https://nodejs.org/

### "Yarn not found"
```bash
npm install -g yarn
```

### "Frontend build failed"
```bash
cd ../frontend
rm -rf node_modules build
yarn install
yarn build
cd ../electron-app
```

### "Electron-builder failed"
```bash
cd electron-app
rm -rf node_modules dist
yarn install
yarn build:dmg
```

### "Port 8000 already in use"
```bash
# Finde und beende Prozess auf Port 8000
lsof -ti:8000 | xargs kill -9
```

### DMG-Hintergrund fehlt
Das Script erstellt automatisch ein einfaches PNG.
Für bessere Qualität siehe: `CREATE-ASSETS.md`

## Wichtige Unterschiede zur Emergent-Version

| Feature | Emergent (Web) | Desktop App |
|---------|----------------|-------------|
| Backend Port | 8001 | **8000** |
| URL | Preview-URL | localhost:8000 |
| .env | REACT_APP_BACKEND_URL leer | http://localhost:8000 |
| Emergent LLM Key | ✅ Verfügbar | ❌ Nicht verfügbar |

## Nach dem Build

Das Script stellt automatisch die original `.env` wieder her,
sodass die Emergent-Web-Version weiter funktioniert.

## Logs bei Problemen

Build-Logs werden in der Konsole angezeigt.
Bei Fehlern siehe:
- Frontend Build: `../frontend/npm-debug.log`
- Electron Build: `./dist/.build/build.log`

## Support

Bei persistenten Problemen:
1. Prüfe `test-build.sh` Output
2. Stelle sicher, dass alle Verzeichnisse vorhanden sind
3. Prüfe Node.js & Yarn Versionen
4. Lösche `node_modules` und installiere neu
