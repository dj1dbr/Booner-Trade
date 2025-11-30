# Booner Trade - macOS Desktop App Download

## 📦 Fertige App (ARM64 - M1/M2/M3 Macs)

**Status:** ✅ Vollständig gebaut und getestet
**Größe:** ~1.4 GB
**Pfad:** `/app/electron-app/dist/mac-arm64/Booner Trade.app`

---

## 🚀 Installation auf Ihrem Mac

### Schritt 1: Download

Die App befindet sich im Emergent-Container. Um sie herunterzuladen:

1. **Öffnen Sie Ihr Emergent Dashboard**
2. **Navigieren Sie zu:** Files → `/app/electron-app/dist/mac-arm64/`
3. **Klicken Sie mit rechts auf:** `Booner Trade.app`
4. **Wählen Sie:** "Download"

**ODER**

Verwenden Sie die Emergent CLI:
```bash
emergent download /app/electron-app/dist/mac-arm64/Booner\ Trade.app ~/Downloads/
```

---

### Schritt 2: Installation

1. Öffnen Sie Finder und gehen Sie zu `~/Downloads/`
2. Ziehen Sie `Booner Trade.app` nach `/Applications/`
3. **Wichtig:** Beim ersten Start wird macOS eine Warnung zeigen (unsignierte App)

**macOS Gatekeeper umgehen:**
```bash
xattr -cr /Applications/Booner\ Trade.app
```

Dann können Sie die App normal öffnen.

---

### Schritt 3: Erster Start

1. **Stoppen Sie Ihre laufende MongoDB:**
   ```bash
   # Prüfen ob MongoDB läuft:
   lsof -i :27017
   
   # Wenn ja, stoppen:
   kill <PID>
   ```

2. **Starten Sie die App:**
   - Doppelklick auf `Booner Trade.app` in Applications
   - ODER: `open /Applications/Booner\ Trade.app`

3. **Logs überprüfen (bei Problemen):**
   ```bash
   tail -f ~/Library/Logs/booner-trade/main.log
   tail -f ~/Library/Logs/booner-trade/error.log
   ```

---

## ✅ Was ist enthalten?

Die App ist **100% eigenständig** und enthält:

- ✅ **Backend:** FastAPI Server (Port 8000)
- ✅ **Frontend:** React Build
- ✅ **MongoDB:** Version 7.0.26 (dynamischer Port, Standard 27017)
- ✅ **Python:** Vollständiges venv mit allen Dependencies:
  - uvicorn
  - fastapi
  - motor
  - metaapi_cloud_sdk
  - und alle anderen aus requirements-desktop.txt

---

## 🔧 Technische Details

### Automatische Port-Auswahl

Wenn MongoDB Port 27017 bereits belegt ist, wählt die App automatisch den nächsten freien Port (27018, 27019, etc.).

Sie können dies in den Logs sehen:
```
MongoDB Port: 27018
Backend will connect to MongoDB at: mongodb://localhost:27018
```

### App-Struktur

```
Booner Trade.app/
└── Contents/
    └── Resources/
        └── app/
            ├── backend/        # FastAPI Backend
            ├── frontend/build/ # React Frontend
            ├── mongodb/        # MongoDB 7.0.26
            └── python/         # Python venv mit allen Packages
                └── bin/
                    ├── python3
                    └── uvicorn ✅
```

---

## ❓ Troubleshooting

### Problem: "App kann nicht geöffnet werden"
```bash
xattr -cr /Applications/Booner\ Trade.app
```

### Problem: MongoDB startet nicht
Prüfen Sie, ob Port 27017 bereits belegt ist:
```bash
lsof -i :27017
# Wenn ja, kill <PID> oder die App wählt automatisch einen anderen Port
```

### Problem: Backend startet nicht
Überprüfen Sie die Logs:
```bash
cat ~/Library/Logs/booner-trade/error.log
```

### Problem: "uvicorn not found"
Das sollte NICHT passieren, da uvicorn jetzt im Python venv enthalten ist!
Wenn doch, überprüfen Sie:
```bash
ls -la /Applications/Booner\ Trade.app/Contents/Resources/app/python/bin/uvicorn
```

---

## 🎉 Fertig!

Ihre App läuft jetzt komplett eigenständig auf Ihrem Mac - ohne Emergent, ohne Docker!

**Datenbank-Speicherort:**
`~/Library/Application Support/booner-trade/database/`

**Logs:**
`~/Library/Logs/booner-trade/`

---

## 📝 Hinweise

- Die App muss **nicht** mit dem Internet verbunden sein (außer für Trading-API-Calls)
- Alle Daten werden lokal gespeichert
- MongoDB und Backend laufen nur, wenn die App geöffnet ist
- Bei App-Schließung werden MongoDB und Backend automatisch gestoppt

Viel Erfolg mit Ihrer Trading-App! 🚀
