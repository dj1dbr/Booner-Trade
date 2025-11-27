# 📦 Booner Trade - Installation auf dem Mac

## ✅ Schritt-für-Schritt Anleitung

### 1️⃣ Projekt auf deinen Mac übertragen

Du hast mehrere Möglichkeiten:

**Option A: Git Clone (empfohlen)**
```bash
# Falls das Projekt auf GitHub liegt
git clone https://github.com/dein-repo/booner-trade.git
cd booner-trade
```

**Option B: ZIP Download**
- Lade den `/app` Ordner als ZIP herunter
- Entpacke ihn auf deinem Mac
- Öffne Terminal und navigiere zum Ordner

### 2️⃣ Voraussetzungen installieren

Öffne Terminal und führe aus:

```bash
# Homebrew (Package Manager für Mac)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Node.js & Yarn
brew install node yarn

# Python 3.11
brew install python@3.11

# Icon-Konvertierungs-Tools
brew install librsvg

# Optional: Prüfe Installationen
node --version    # sollte v18+ zeigen
python3 --version # sollte 3.11+ zeigen
yarn --version    # sollte 1.22+ zeigen
```

### 3️⃣ Build ausführen

```bash
# Navigiere zum electron-app Ordner
cd /pfad/zu/deinem/projekt/electron-app

# Mache Build-Script ausführbar
chmod +x build-app.sh

# Starte Build-Prozess
./build-app.sh
```

**Was passiert beim Build?**
```
🔨 Build-Prozess läuft...
├─ 📦 React Frontend wird gebaut (~2-3 Min)
├─ 🐍 Python Environment wird erstellt (~3-5 Min)
├─ 📊 MongoDB wird heruntergeladen (~2 Min)
├─ 🎨 Logo wird konvertiert (~10 Sek)
└─ 📦 DMG wird erstellt (~2-3 Min)

⏱️  Gesamtzeit: ~10-15 Minuten
```

### 4️⃣ Installation

Nach erfolgreichem Build:

```bash
# DMG-Datei öffnen
open dist/Booner\ Trade-1.0.0.dmg
```

Ein Fenster öffnet sich mit:
- **Linke Seite**: Booner Trade App Icon
- **Rechte Seite**: Applications-Ordner Link

**Ziehe das App-Icon in den Applications-Ordner** 🖱️

### 5️⃣ App starten

**Erster Start:**
```bash
# Via Terminal (empfohlen für ersten Start)
/Applications/Booner\ Trade.app/Contents/MacOS/Booner\ Trade
```

**Danach:**
- Öffne Launchpad
- Suche nach "Booner Trade"
- Klicke zum Starten

**Beim ersten Start:**
1. ⏱️  MongoDB startet (5-10 Sekunden)
2. ⏱️  Backend startet (5-10 Sekunden)
3. 🚀 App-Fenster öffnet sich

## ⚙️ Konfiguration

### MetaAPI Credentials anpassen

Die App hat bereits deine Standard-Credentials eingebaut:
- Libertex Demo: `5cc9abd1-671a-447e-ab93-5abbfe0ed941`
- ICMarkets Demo: `d2605e89-7bc2-4144-9f7c-951edd596c39`

**Um sie zu ändern:**
1. Starte die App
2. Gehe zu **Settings** (⚙️ Icon)
3. Scrolle zu "MetaAPI Konfiguration"
4. Klicke auf "Erweitern"
5. Ändere Account IDs/Token
6. Klicke "Speichern"
7. App startet automatisch neu

## 🛠️ Troubleshooting

### ❌ "App kann nicht geöffnet werden" (Gatekeeper)

Mac blockiert manchmal Apps von unbekannten Entwicklern:

```bash
# Erlaubnis geben
sudo xattr -rd com.apple.quarantine /Applications/Booner\ Trade.app
```

Oder: **Systemeinstellungen** → **Sicherheit** → "Trotzdem öffnen"

### ❌ App startet nicht / bleibt beim Logo hängen

**Logs überprüfen:**
```bash
# Terminal öffnen und App mit Logs starten
/Applications/Booner\ Trade.app/Contents/MacOS/Booner\ Trade 2>&1 | tee ~/booner-trade.log
```

**Häufige Probleme:**
1. **MongoDB startet nicht**: Port 27017 bereits belegt
   ```bash
   # Prüfe, ob MongoDB schon läuft
   lsof -i :27017
   # Stoppe andere MongoDB-Instanzen
   pkill -f mongod
   ```

2. **Backend startet nicht**: Port 8001 bereits belegt
   ```bash
   # Prüfe Port 8001
   lsof -i :8001
   # Stoppe Prozess falls nötig
   kill -9 <PID>
   ```

### ❌ Build-Fehler

**Fehler: "command not found"**
→ Installiere fehlende Tools (siehe Schritt 2)

**Fehler: "Permission denied"**
```bash
chmod +x build-app.sh
```

**Fehler: "MongoDB download failed"**
→ Prüfe Internetverbindung oder lade MongoDB manuell:
```bash
cd electron-app
curl -O https://fastdl.mongodb.org/osx/mongodb-macos-arm64-7.0.4.tgz
tar -zxvf mongodb-macos-arm64-7.0.4.tgz
mv mongodb-macos-arm64-7.0.4 mongodb-mac
```

## 📍 Datei-Speicherorte

**App-Dateien:**
```
/Applications/Booner Trade.app/
├── Contents/
│   ├── MacOS/         # Ausführbare Datei
│   └── Resources/
│       └── app/
│           ├── mongodb/    # MongoDB Binary
│           ├── python/     # Python + Dependencies
│           ├── backend/    # FastAPI Backend
│           └── frontend/   # React Build
```

**User-Daten:**
```
~/Library/Application Support/booner-trade/
├── database/     # MongoDB Datenbank
└── logs/         # App Logs
```

## 🗑️ Deinstallation

```bash
# App löschen
rm -rf /Applications/Booner\ Trade.app

# User-Daten löschen (optional)
rm -rf ~/Library/Application\ Support/booner-trade

# Cache löschen (optional)
rm -rf ~/Library/Caches/booner-trade
```

## 🔄 Updates

Für Updates:
1. Lade neue Version herunter
2. Führe Build erneut aus
3. Installiere neue DMG (überschreibt alte Version)
4. Deine Daten bleiben erhalten!

## 📞 Support

Bei Problemen:
1. Überprüfe Logs: `~/Library/Application Support/booner-trade/logs/`
2. Führe App mit Logs aus: `/Applications/Booner\ Trade.app/Contents/MacOS/Booner\ Trade`
3. Kontaktiere Support mit Log-Dateien

## ✨ Features der Desktop-App

✅ **Komplett Standalone** - Keine externen Dependencies
✅ **Offline-fähig** - Läuft ohne Internet (außer Trading)
✅ **Schneller Start** - Optimiert für Mac
✅ **Auto-Updates** - Über Update-Funktion in Settings
✅ **Natives Look & Feel** - Mac-optimiertes UI
✅ **Sicher** - Sandboxed mit Entitlements
✅ **Performance** - Native M1/M2 Support

Viel Erfolg beim Trading! 🚀📈
