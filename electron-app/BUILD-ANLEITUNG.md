# Booner Trade Desktop App - Build Anleitung

## Vollständiger Build-Prozess

### Voraussetzungen

1. **Node.js** (v18 oder höher)
2. **Yarn** Package Manager
3. **macOS** (für macOS Build)

### Build-Schritte

```bash
cd /app/electron-app
./build.sh
```

Das Script führt automatisch aus:
1. ✅ Dependency-Check (Node.js, Yarn)
2. ✅ Frontend .env Konfiguration (Port 8000)
3. ✅ React Production Build
4. ✅ Electron Dependencies Installation
5. ✅ DMG Background PNG Erstellung
6. ✅ macOS DMG Erstellung
7. ✅ DMG-Datei finden und anzeigen
8. ✅ Original .env wiederherstellen

### Build-Ausgabe

Die fertige DMG-Datei findest du in:
```
/app/electron-app/dist/
```

Mögliche Dateinamen:
- `Booner Trade-1.0.0.dmg` (Universal)
- `Booner Trade-1.0.0-x64.dmg` (Intel Mac)
- `Booner Trade-1.0.0-arm64.dmg` (Apple Silicon)

Das build.sh Script findet automatisch die erstellte DMG-Datei.

### Wichtige Konfigurationen

#### Backend Port
Der Desktop-App Backend läuft auf **Port 8000** (nicht 8001 wie in Emergent).

Dies ist in folgenden Dateien konfiguriert:
- `main.js` (Zeile 79, 88)
- `frontend/.env` (während Build)

#### Ohne Emergent-Funktionen
Die Desktop-App enthält KEINE Emergent-spezifischen Features:
- Keine Emergent LLM Key Integration
- Keine Emergent-Only Dependencies
- Läuft komplett standalone

#### Assets
- `dmg-background.png` - Automatisch erstellt
- `logo.png` - Automatisch erstellt
- Für bessere Qualität: Siehe `CREATE-ASSETS.md`

### Troubleshooting

#### "DMG not found"
```bash
# Prüfe dist/ Verzeichnis
ls -la /app/electron-app/dist/
```

#### "Frontend build failed"
```bash
cd /app/frontend
rm -rf node_modules build
yarn install
yarn build
```

#### "Electron dependencies missing"
```bash
cd /app/electron-app
rm -rf node_modules
yarn install
```

### Manuelle Build-Schritte

Falls das automatische Script fehlschlägt:

#### 1. Frontend bauen
```bash
cd /app/frontend
cat > .env << EOF
PUBLIC_URL=.
REACT_APP_BACKEND_URL=http://localhost:8000
EOF
yarn build
```

#### 2. Electron App bauen
```bash
cd /app/electron-app
yarn install
yarn build:dmg
```

#### 3. DMG finden
```bash
find /app/electron-app/dist -name "*.dmg"
```

### DMG Installation

1. DMG-Datei öffnen:
   ```bash
   open dist/Booner\ Trade-1.0.0*.dmg
   ```

2. App nach `/Applications` ziehen

3. App öffnen:
   - Beim ersten Start: Rechtsklick → Öffnen
   - macOS Sicherheitswarnung bestätigen

### Was ist in der DMG?

Die Desktop-App enthält:
- ✅ React Frontend (Production Build)
- ✅ FastAPI Backend (Python)
- ✅ MongoDB (Embedded)
- ✅ Alle Dependencies
- ✅ Python Environment

Alles läuft lokal - keine Internetverbindung nötig (außer für MetaAPI).

### Build-Zeit

Erwartete Dauer:
- Frontend Build: 2-3 Minuten
- Electron Build: 5-10 Minuten
- **Gesamt: ~10-15 Minuten**

### Nach dem Build

Die Original `frontend/.env` wird automatisch wiederhergestellt,
sodass die Emergent-Umgebung weiter funktioniert.
