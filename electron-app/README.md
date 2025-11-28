# 🚀 Booner Trade - Mac Desktop App

## 📋 Vorbereitung (auf deinem Mac)

### Voraussetzungen installieren:
```bash
# Homebrew (falls noch nicht installiert)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Node.js & Yarn
brew install node yarn

# Python 3
brew install python@3.11

# Icon-Tools (für Logo-Konvertierung)
brew install librsvg
```

## 🔨 Build-Prozess

### 1. Dateien auf deinen Mac übertragen

Kopiere den gesamten `/app` Ordner auf deinen Mac.

### 2. Build ausführen

```bash
cd /pfad/zu/app/electron-app
chmod +x build-app.sh
./build-app.sh
```

Der Build-Prozess:
1. ✅ Baut das React Frontend
2. ✅ Erstellt Python Virtual Environment mit allen Dependencies
3. ✅ Lädt MongoDB für macOS herunter
4. ✅ Konvertiert das Logo in ein Mac Icon (.icns)
5. ✅ Erstellt die .dmg Installation Datei

### 3. Installation testen

Nach erfolgreichem Build:

```bash
# DMG öffnen
open dist/Booner\ Trade-1.0.0.dmg
```

Ziehe "Booner Trade" in den Applications-Ordner.

## 🎯 Was die App enthält

✅ **Standalone MongoDB** - Keine zusätzliche Installation nötig
✅ **Python Backend** - FastAPI mit allen Dependencies
✅ **React Frontend** - Komplette UI
✅ **MetaAPI Credentials** - Fest eingebaut, aber änderbar über Settings
✅ **AI Trading Bot** - Vollautomatisch
✅ **Icon & Branding** - "BT" Logo mit Finanz-Symbolen

## ⚙️ Konfiguration

### MetaAPI Credentials ändern

Die App hat deine MetaAPI Credentials bereits eingebaut:
- **Libertex Demo**: `5cc9abd1-671a-447e-ab93-5abbfe0ed941`
- **ICMarkets Demo**: `d2605e89-7bc2-4144-9f7c-951edd596c39`

Du kannst diese jederzeit in den **Settings** der App ändern:
1. App starten
2. Zu Settings navigieren
3. "MetaAPI Konfiguration" erweitern
4. Account IDs und Token ändern
5. Speichern → App startet neu mit neuen Credentials

## 📦 Technische Details

**App-Größe**: ~300-500MB (inkl. MongoDB & Python)

**Komponenten**:
- Electron 28.x
- MongoDB 7.0.4 (embedded)
- Python 3.11 (portable virtual environment)
- React Frontend (built)
- FastAPI Backend

**Speicherorte**:
- App: `/Applications/Booner Trade.app`
- Datenbank: `~/Library/Application Support/booner-trade/database`
- Logs: `~/Library/Application Support/booner-trade/logs`

## 🐛 Troubleshooting

### App startet nicht
```bash
# Logs prüfen
tail -f ~/Library/Application\ Support/booner-trade/logs/app.log
```

### MongoDB startet nicht
```bash
# Manuell starten zum Testen
/Applications/Booner\ Trade.app/Contents/Resources/app/mongodb/bin/mongod \
  --dbpath ~/Library/Application\ Support/booner-trade/database
```

### Backend startet nicht
```bash
# Python Dependencies prüfen
/Applications/Booner\ Trade.app/Contents/Resources/app/python/bin/python3 -m pip list
```

## 🤖 AI/LLM Konfiguration

**WICHTIG:** Diese Desktop-App verwendet **NICHT** `emergentintegrations`!

Die Warnung beim Start ist **NORMAL**:
```
ℹ️  Desktop-App Mode: Using Fallback (direct API keys)
```

**Warum?** `emergentintegrations` funktioniert nur auf der Emergent Plattform.

**Die Desktop-App nutzt stattdessen:**
- ✅ Direkten API-Zugriff (OpenAI, Anthropic, Google)
- ✅ Oder Ollama (komplett offline & kostenlos)

**Detaillierte Anleitung:** Siehe `DESKTOP-APP-AI-KONFIGURATION.md`

## 🔄 Updates

Um ein Update zu erstellen:
1. Code ändern
2. Version in `package.json` erhöhen
3. Build erneut ausführen
4. Neue DMG an Nutzer verteilen

## 📄 Lizenz

Privat / Kommerziell - Alle Rechte vorbehalten.
