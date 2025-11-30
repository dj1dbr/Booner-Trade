# 🚀 Booner Trade - Finale Desktop Build Anleitung

**Stand:** November 2025  
**Version:** 2.0 (Nach Backend Refactoring)

---

## ✅ Was wurde verbessert?

### Architektur-Änderungen:
- **Backend aufgeteilt:** API-Server + Worker-Prozess
- **Server (Port 8001):** Leichtgewichtige API für Frontend
- **Worker (Hintergrund):** AI Trading Bot, MetaAPI Monitoring, Scheduler
- **Performance:** Schnellerer Start, keine Timeouts mehr
- **Stabilität:** UI blockiert nicht mehr bei Background-Tasks

---

## 📋 Voraussetzungen

### Auf Ihrem Mac (macOS):
1. **Xcode Command Line Tools** installiert
2. **Python 3.11+** installiert
3. **Node.js 18+** und **Yarn** installiert
4. **Git** installiert

### Prüfen Sie Ihre Installation:
```bash
python3 --version    # Sollte 3.11.x oder höher sein
node --version       # Sollte v18.x oder höher sein
yarn --version       # Sollte installiert sein
git --version        # Sollte installiert sein
```

---

## 🔧 Schritt 1: Projekt von Emergent herunterladen

### Option A: Über Emergent Web Interface
1. Gehen Sie zu Ihrem Emergent Projekt
2. Klicken Sie auf "Save to Github" oder "Download"
3. Entpacken Sie das Projekt in: `/Users/<IhrUsername>/Desktop/Electrontrader`

### Option B: Via Git (falls Repository verbunden)
```bash
cd ~/Desktop
git clone <IHR-REPOSITORY-URL> Electrontrader
cd Electrontrader
```

---

## 🔧 Schritt 2: MetaAPI Account-Konfiguration

**WICHTIG:** Die korrekten MetaAPI Account IDs sind essentiell!

### 2.1 Account IDs herausfinden:
```bash
cd ~/Desktop/Electrontrader/backend
python3 list_metaapi_accounts.py
```

**Output zeigt Ihre Accounts:**
```
📊 ACCOUNT #1
Account ID: d2605e89-7bc2-4144-9f7c-951edd596c39
Login: 52565616
Server: ICMarketsEU-Demo
→ ICMarkets Account

📊 ACCOUNT #2
Account ID: 5cc9abd1-671a-447e-ab93-5abbfe0ed941
Login: 510038543
Server: LibertexCom-MT5 Demo Server
→ Libertex Account
```

### 2.2 `.env` Datei aktualisieren:
Öffnen Sie `backend/.env` und aktualisieren Sie:

```bash
# VORHER (falsch):
METAAPI_ACCOUNT_ID=ai-trading-refactor
METAAPI_ICMARKETS_ACCOUNT_ID=ai-trading-refactor

# NACHHER (korrekt - Ihre IDs verwenden!):
METAAPI_ACCOUNT_ID=5cc9abd1-671a-447e-ab93-5abbfe0ed941
METAAPI_ICMARKETS_ACCOUNT_ID=d2605e89-7bc2-4144-9f7c-951edd596c39
```

**⚠️ Wichtig:** Verwenden Sie IHRE Account IDs aus dem Script!

---

## 🔧 Schritt 3: Frontend Build erstellen

### 3.1 Frontend-Abhängigkeiten installieren:
```bash
cd ~/Desktop/Electrontrader/frontend
yarn install
```

### 3.2 Production Build erstellen:
```bash
yarn build
```

**Erwartete Ausgabe:**
```
Creating an optimized production build...
✓ Compiled successfully
File sizes after gzip:
  build/static/js/main.xxxxx.js  (xxx kB)
  ...
```

### 3.3 Build verifizieren:
```bash
ls -la build/
# Sollte zeigen: index.html, static/, manifest.json, etc.
```

---

## 🔧 Schritt 4: Python Backend für Electron vorbereiten

### 4.1 Electron-App Verzeichnis wechseln:
```bash
cd ~/Desktop/Electrontrader/electron-app
```

### 4.2 Build-Script ausführen:
```bash
./BUILD-MAC-LOKAL.sh
```

**Das Script macht folgendes:**
1. Erstellt portable Python-Installation
2. Installiert alle Backend-Dependencies für macOS ARM64
3. Kompiliert native Module (pydantic_core, etc.)
4. Kopiert MongoDB-Binaries
5. Erstellt Electron `.app` und `.dmg`

**Erwartete Dauer:** 5-10 Minuten

### 4.3 Build-Output prüfen:
```bash
ls -la dist/
# Sollte zeigen: Booner Trade-1.0.0-arm64.dmg
```

---

## 🔧 Schritt 5: Desktop-App installieren

### 5.1 Alte Installation entfernen (falls vorhanden):
```bash
rm -rf "/Applications/Booner Trade.app"
```

### 5.2 DMG öffnen und App installieren:
```bash
open "dist/Booner Trade-1.0.0-arm64.dmg"
```

**Manuell:**
1. Warten Sie, bis das DMG-Fenster erscheint
2. Ziehen Sie "Booner Trade.app" in den Applications-Ordner
3. Schließen Sie das DMG-Fenster
4. Werfen Sie das DMG aus (Rechtsklick → Auswerfen)

### 5.3 Quarantäne-Attribute entfernen:
```bash
xattr -cr "/Applications/Booner Trade.app"
```

**⚠️ Wichtig:** Dieser Schritt verhindert "App kann nicht geöffnet werden"-Fehler!

---

## 🚀 Schritt 6: App starten

### 6.1 App starten:
```bash
open "/Applications/Booner Trade.app"
```

**Oder:** Doppelklick im Applications-Ordner

### 6.2 Startup-Prozess (Logs prüfen):
```bash
tail -f ~/Library/Logs/booner-trade/main.log
```

**Erwartete Startup-Sequenz:**
```
[INFO] === Booner Trade Starting ===
[INFO] Starting MongoDB from: ...
[INFO] ✅ MongoDB ready on port: 27017
[INFO] ⚙️  Starting Backend API...
[INFO] Backend is ready and responding!
[INFO] ⚙️  Starting MetaApi Worker...
[INFO] ✅ Worker started in background
[INFO] 🖥️  Opening Window...
[INFO] ✅ Page loaded successfully
```

**Startup-Zeit:** 8-15 Sekunden

---

## 🔍 Schritt 7: Funktionstest

### 7.1 Überprüfen Sie im Dashboard:
- ✅ **Balance:** Beide MT5 Accounts zeigen Werte an (nicht €0.00)
- ✅ **Platform Status:** Beide Plattformen "connected=true"
- ✅ **Market Data:** Live-Preise für Gold, Silber, WTI, etc.
- ✅ **Trades:** Trades-Tab lädt ohne Timeout

### 7.2 Einstellungen öffnen:
1. Klicken Sie auf "Einstellungen" Button
2. Modal öffnet sich ohne Fehler
3. Ändern Sie "Auto Trading" Toggle
4. Klicken Sie "Einstellungen speichern"
5. **Erwartung:** "Einstellungen gespeichert" (nicht Timeout!)

### 7.3 Trade ausführen testen (optional):
1. Wählen Sie ein Rohstoff (z.B. Gold)
2. Klicken Sie "Kaufen"
3. Geben Sie Menge ein (z.B. 0.01)
4. Klicken Sie "Trade ausführen"
5. **Erwartung:** Trade erscheint in Trades-Liste

---

## 📊 Erfolgreiche Installation - Checkliste

- [ ] Frontend Build existiert (`frontend/build/`)
- [ ] Electron Build erfolgreich (`electron-app/dist/*.dmg`)
- [ ] App in `/Applications/` installiert
- [ ] Quarantäne-Attribute entfernt (`xattr -cr`)
- [ ] App startet ohne Fehler
- [ ] MongoDB startet (Logs zeigen "MongoDB ready")
- [ ] Backend API startet (Logs zeigen "Backend is ready")
- [ ] Worker startet (Logs zeigen "Worker started")
- [ ] Dashboard lädt mit Live-Daten
- [ ] Plattformen zeigen Balances an (nicht €0.00)
- [ ] Einstellungen können gespeichert werden
- [ ] Keine Timeout-Fehler

---

## ❌ Fehlerbehandlung

### Problem: "App kann nicht geöffnet werden"
**Lösung:**
```bash
xattr -cr "/Applications/Booner Trade.app"
sudo spctl --master-disable  # Falls macOS Gatekeeper aktiviert
```

### Problem: "ModuleNotFoundError: No module named 'pydantic_core'"
**Ursache:** Native Module nicht korrekt kompiliert  
**Lösung:**
```bash
cd electron-app
./BUILD-MAC-LOKAL.sh  # Script neu ausführen
```

### Problem: "MongoDB failed to start"
**Lösung:**
1. Prüfen Sie Logs: `~/Library/Logs/booner-trade/error.log`
2. Port 27017 bereits belegt?
   ```bash
   lsof -i :27017
   # Falls belegt, MongoDB-Prozess beenden
   ```

### Problem: "Backend timeout" oder "Platform connected=false"
**Ursache:** Falsche MetaAPI Account IDs  
**Lösung:**
1. Führen Sie `list_metaapi_accounts.py` aus
2. Aktualisieren Sie `backend/.env` mit korrekten IDs
3. Rebuild mit `./BUILD-MAC-LOKAL.sh`

### Problem: Frontend zeigt "Netzwerkfehler"
**Ursache:** Backend läuft nicht  
**Lösung:**
```bash
# Prüfen Sie Backend-Logs
tail -50 ~/Library/Logs/booner-trade/error.log

# Prüfen Sie ob Backend-Prozess läuft
ps aux | grep uvicorn
```

---

## 🔧 Entwicklungsmodus (für Debugging)

### Backend separat starten:
```bash
cd ~/Desktop/Electrontrader/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend separat starten:
```bash
cd ~/Desktop/Electrontrader/frontend
yarn start
```

### Worker separat starten:
```bash
cd ~/Desktop/Electrontrader/backend
python3 worker.py
```

---

## 📝 Wichtige Dateien

### Konfiguration:
- `backend/.env` - Backend-Konfiguration (MetaAPI Keys, etc.)
- `frontend/.env.production` - Frontend Production URL
- `electron-app/package.json` - Electron App Metadaten

### Build-Scripts:
- `electron-app/BUILD-MAC-LOKAL.sh` - Haupt-Build-Script
- `frontend/package.json` - Frontend Build-Config

### Logs (nach Installation):
- `~/Library/Logs/booner-trade/main.log` - Haupt-Log
- `~/Library/Logs/booner-trade/error.log` - Fehler-Log

---

## 🎯 Performance-Erwartungen

### Startup-Zeiten:
- **MongoDB:** 2-3 Sekunden
- **Backend API:** 3-5 Sekunden
- **Worker:** 2-3 Sekunden
- **UI Ready:** 1-2 Sekunden
- **Gesamt:** ~8-15 Sekunden

### Memory-Verwendung:
- **MongoDB:** ~150 MB
- **Backend:** ~80-120 MB
- **Worker:** ~100-150 MB
- **Electron Frontend:** ~100-150 MB
- **Gesamt:** ~450-550 MB

### Disk Space:
- **App Bundle:** ~400-500 MB
- **User Data:** ~50-100 MB (MongoDB Daten)

---

## ✨ Architektur-Überblick

```
┌─────────────────────────────────────────┐
│     Booner Trade.app (Electron)         │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │  Frontend   │  │  Backend        │  │
│  │  (React)    │←─│  FastAPI Server │  │
│  │  Port: UI   │  │  Port: 8001     │  │
│  └─────────────┘  └─────────────────┘  │
│                          ↑              │
│                          │              │
│                   ┌──────┴──────┐       │
│                   │             │       │
│            ┌──────┴──────┐ ┌───┴────┐  │
│            │  MongoDB    │ │ Worker │  │
│            │  Port: 27017│ │Process │  │
│            └─────────────┘ └────────┘  │
│                                         │
│            Worker Tasks:                │
│            - AI Trading Bot             │
│            - MetaAPI Monitoring         │
│            - Background Scheduler       │
│            - Position Management        │
└─────────────────────────────────────────┘
```

---

## 🎉 Fertig!

Ihre Booner Trade Desktop-App ist jetzt installiert und läuft!

**Bei Problemen:**
1. Prüfen Sie die Logs: `~/Library/Logs/booner-trade/`
2. Führen Sie `list_metaapi_accounts.py` aus
3. Kontaktieren Sie Support mit Log-Dateien

**Viel Erfolg beim Trading! 📈**
