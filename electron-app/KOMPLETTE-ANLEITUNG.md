# Booner Trade Desktop App - Komplette Build-Anleitung

## Problem behoben: MongoDB/Python fehlen

Die App stürzt ab weil MongoDB und Python nicht in der DMG sind.

## Lösung: Ressourcen vorbereiten

### Schritt 1: Ressourcen vorbereiten

```bash
cd /pfad/zu/electron-app
./prepare-resources.sh
```

Das Script macht:
1. ✅ Prüft/fordert MongoDB Download
2. ✅ Erstellt Python Environment
3. ✅ Prüft Backend
4. ✅ Baut Frontend (falls nötig)

### Schritt 2: MongoDB manuell herunterladen

**Wichtig:** MongoDB kann nicht automatisch heruntergeladen werden (Lizenz).

1. Gehe zu: https://www.mongodb.com/try/download/community

2. Wähle:
   - **Version:** 7.0.x (aktuell)
   - **Platform:** macOS
   - **Package:** TGZ
   - **Architecture:** arm64 (Apple Silicon) oder x64 (Intel)

3. Download und entpacken:
   ```bash
   cd ~/Downloads
   tar -xzf mongodb-macos-arm64-7.0.*.tgz
   ```

4. Kopiere nach electron-app:
   ```bash
   mkdir -p /pfad/zu/electron-app/mongodb-mac/bin
   cp mongodb-macos-*/bin/* /pfad/zu/electron-app/mongodb-mac/bin/
   ```

5. Teste:
   ```bash
   /pfad/zu/electron-app/mongodb-mac/bin/mongod --version
   ```

### Schritt 3: Python Environment

Das Script erstellt automatisch ein Python Environment.

**Option A: System Python (einfach)**
- Verwendet dein macOS Python
- ⚠️ Nicht portabel (funktioniert nur auf deinem Mac)

**Option B: Virtual Environment (empfohlen)**
- Erstellt eigenständiges Python
- ✅ Portabel (funktioniert auf anderen Macs)

### Schritt 4: Build ausführen

```bash
./build.sh
```

Das Script:
1. Baut Frontend
2. Installiert Electron Dependencies
3. Packt ALLE Ressourcen in DMG:
   - MongoDB
   - Python
   - Backend
   - Frontend

### Schritt 5: Testen

```bash
open "dist/Booner Trade-1.0.0*.dmg"
```

Installiere und starte die App.

**Wenn sie abstürzt:**
```bash
"/Applications/Booner Trade.app/Contents/MacOS/Booner Trade"
```

Zeigt Fehler direkt im Terminal.

## Was wird gepackt

Die fertige DMG enthält:

```
Booner Trade.app/
└── Contents/
    ├── MacOS/
    │   └── Booner Trade (Electron Binary)
    └── Resources/
        └── app/
            ├── backend/ (FastAPI Server)
            ├── frontend/build/ (React App)
            ├── mongodb/bin/ (MongoDB Binary)
            └── python/bin/ (Python + uvicorn)
```

**Alles läuft lokal - keine Emergent-Abhängigkeiten!**

## Verzeichnis-Struktur vor Build

```
Booner-Trade/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── public/
│   ├── build/ ← Muss existieren!
│   └── package.json
└── electron-app/
    ├── mongodb-mac/ ← Muss vorbereitet werden!
    │   └── bin/
    │       └── mongod
    ├── python-env/ ← Wird automatisch erstellt
    │   └── bin/
    │       ├── python3
    │       └── uvicorn
    ├── build.sh
    ├── prepare-resources.sh
    └── package.json
```

## Troubleshooting

### "MongoDB binary not found"
```bash
# Prüfe:
ls -la electron-app/mongodb-mac/bin/mongod

# Falls fehlt:
# Siehe Schritt 2 (MongoDB Download)
```

### "Backend server.py not found"
```bash
# Prüfe:
ls -la backend/server.py

# Falls fehlt:
# Stelle sicher, dass du das komplette Projekt hast
```

### "Frontend build not found"
```bash
# Baue Frontend:
cd frontend
yarn build
```

### "Python/Uvicorn not found"
```bash
# Erstelle Python Env neu:
rm -rf electron-app/python-env
./prepare-resources.sh
```

### App startet aber Backend funktioniert nicht
```bash
# Prüfe Backend-Port:
lsof -ti:8000

# Falls belegt:
lsof -ti:8000 | xargs kill -9
```

## Größe der fertigen DMG

**Erwartete Größe:** ~500MB - 1GB

- MongoDB: ~200MB
- Python + Dependencies: ~100-200MB
- Frontend Build: ~5MB
- Backend: ~10MB
- Electron: ~100MB

## Nach dem ersten erfolgreichen Build

Nachfolgende Builds sind schneller, weil MongoDB/Python bereits vorbereitet sind.

Nur neu bauen wenn:
- Frontend Code ändert
- Backend Code ändert
- MongoDB/Python updaten willst

## Unterschiede zur Emergent-Version

| Feature | Emergent | Desktop |
|---------|----------|---------|
| Backend Port | 8001 | 8000 |
| MongoDB | Cloud | Embedded |
| Python | System | Embedded |
| Updates | Auto | Manuell |
| Emergent LLM Key | ✅ | ❌ |

## Lizenz-Hinweise

- **MongoDB:** Server Side Public License (SSPL)
- Nur für private Nutzung OK
- Für kommerzielle Distribution: MongoDB Atlas verwenden
