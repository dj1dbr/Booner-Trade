# Booner Trade - App Crash Debugging Guide

## Problem: App startet kurz und stürzt ab

### Schritt 1: Logs prüfen

```bash
cd /pfad/zu/electron-app
./check-app-logs.sh
```

Dies zeigt:
- main.log - Normales Startup-Log
- error.log - Alle Fehler
- Crash Reports (falls vorhanden)

### Schritt 2: Log-Dateien manuell ansehen

```bash
# macOS Logs:
tail -100 ~/Library/Logs/Booner\ Trade/main.log
tail -100 ~/Library/Logs/Booner\ Trade/error.log

# Oder mit Console.app:
open -a Console
# Filter für: "Booner Trade"
```

### Schritt 3: Häufige Fehlerursachen

#### A) MongoDB fehlt oder startet nicht
**Symptom:** Log zeigt "MongoDB binary not found"
**Fix:**
```bash
# Prüfe ob MongoDB in der App ist:
ls -la "/Applications/Booner Trade.app/Contents/Resources/app/mongodb/bin/"

# Falls leer: MongoDB wurde nicht in DMG gepackt
# Lösung: Rebuild mit MongoDB eingeschlossen
```

#### B) Backend/Python fehlt
**Symptom:** Log zeigt "Backend server.py not found" oder "Uvicorn not found"
**Fix:**
```bash
# Prüfe ob Backend in der App ist:
ls -la "/Applications/Booner Trade.app/Contents/Resources/app/backend/"
ls -la "/Applications/Booner Trade.app/Contents/Resources/app/python/bin/"

# Falls leer: Backend/Python wurde nicht gepackt
```

#### C) Frontend Build fehlt
**Symptom:** Log zeigt "index.html NOT FOUND"
**Fix:**
```bash
# Prüfe Frontend:
ls -la "/Applications/Booner Trade.app/Contents/Resources/app/frontend/build/"

# Falls leer: Frontend Build fehlt
# Rebuild mit: cd frontend && yarn build
```

#### D) Port 8000 bereits belegt
**Symptom:** Backend startet nicht, "Address already in use"
**Fix:**
```bash
# Finde Prozess auf Port 8000:
lsof -ti:8000

# Beende Prozess:
lsof -ti:8000 | xargs kill -9
```

#### E) Berechtigungen fehlen
**Symptom:** "Permission denied" Fehler
**Fix:**
```bash
# Entferne Quarantine Flag:
xattr -cr "/Applications/Booner Trade.app"

# Gib Ausführungsrechte:
chmod +x "/Applications/Booner Trade.app/Contents/MacOS/Booner Trade"
```

### Schritt 4: App im Terminal starten (mehr Output)

```bash
# Starte App direkt im Terminal für vollständiges Logging:
open -a "Booner Trade" --wait-apps --args --enable-logging

# Oder direkt die Binary:
"/Applications/Booner Trade.app/Contents/MacOS/Booner Trade"
```

### Schritt 5: Package.json Build-Konfiguration prüfen

Die DMG sollte diese Ressourcen enthalten:
```json
"extraResources": [
  { "from": "../backend", "to": "app/backend" },
  { "from": "../frontend/build", "to": "app/frontend/build" },
  { "from": "./mongodb-mac", "to": "app/mongodb" },
  { "from": "./python-env", "to": "app/python" }
]
```

### Schritt 6: Manueller Test der Komponenten

**MongoDB Test:**
```bash
cd "/Applications/Booner Trade.app/Contents/Resources/app/mongodb/bin"
./mongod --version
```

**Python Test:**
```bash
cd "/Applications/Booner Trade.app/Contents/Resources/app/python/bin"
./python3 --version
```

**Backend Test:**
```bash
cd "/Applications/Booner Trade.app/Contents/Resources/app/backend"
ls -la server.py
```

### Schritt 7: Neuinstallation

Falls nichts hilft:
```bash
# 1. App komplett löschen
rm -rf "/Applications/Booner Trade.app"
rm -rf ~/Library/Application\ Support/Booner\ Trade
rm -rf ~/Library/Logs/Booner\ Trade

# 2. DMG neu öffnen und installieren
open "dist/Booner Trade-1.0.0*.dmg"
```

## Bekannte Probleme & Lösungen

### Problem: "Python embedded nicht verfügbar"
**Ursache:** Python Portable/Embedded wurde nicht erstellt
**Lösung:** 
- Verwende system Python (nicht empfohlen für Distribution)
- Oder erstelle Python Embedded Environment

### Problem: "MongoDB funktioniert nicht auf Apple Silicon"
**Ursache:** MongoDB Binary ist für falsche Architektur
**Lösung:**
- Download ARM64 MongoDB für Apple Silicon
- Oder baue Universal Binary

### Problem: "App öffnet sich und schließt sofort"
**Ursache:** Kritischer Fehler beim Startup (MongoDB/Backend)
**Lösung:**
- Siehe Logs in ~/Library/Logs/Booner Trade/
- Prüfe ob alle Ressourcen gepackt wurden
- Starte App im Terminal für mehr Output

## Debug-Build erstellen

Für besseres Debugging, erstelle Development-Build:
```bash
# In electron-app/main.js setze:
const isDev = true;

# Dann rebuild:
yarn build:dmg
```

Dies aktiviert:
- Developer Tools im Browser
- Ausführlicheres Logging
- Console-Output

## Support-Informationen sammeln

Wenn du Hilfe brauchst, sammle:
```bash
# 1. Logs
cp ~/Library/Logs/Booner\ Trade/*.log ~/Desktop/

# 2. System Info
system_profiler SPSoftwareDataType > ~/Desktop/system-info.txt

# 3. Crash Reports
cp ~/Library/Logs/DiagnosticReports/*Booner* ~/Desktop/ 2>/dev/null

# 4. App-Inhalt prüfen
ls -laR "/Applications/Booner Trade.app/Contents/Resources/" > ~/Desktop/app-contents.txt
```
