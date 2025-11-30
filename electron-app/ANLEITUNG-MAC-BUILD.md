# Booner Trade - macOS Desktop App Build Anleitung

## 🎯 EINFACHE LÖSUNG - Alles auf Ihrem Mac bauen

**Problem bisher:** Der Build im Container erstellt Linux-Python → funktioniert nicht auf macOS.

**Neue Lösung:** Alles wird DIREKT auf Ihrem Mac gebaut → 100% kompatibel!

---

## ✅ Voraussetzungen

Bitte installieren Sie folgendes auf Ihrem Mac:

1. **Node.js** (v18+)  
   Download: https://nodejs.org/

2. **Python 3.9+**  
   Überprüfen: `python3 --version`  
   (Sollte bereits auf macOS installiert sein)

3. **Yarn** (wird automatisch installiert falls fehlend)

---

## 📦 Schritt 1: Repository auf Ihren Mac klonen

```bash
# Falls Sie das Repo noch nicht lokal haben:
git clone <YOUR_REPO_URL> ~/Booner-Trade
cd ~/Booner-Trade
```

**ODER** wenn Sie es schon haben:

```bash
cd ~/mein_python_projekt/Rohstofftrader/Booner-Trade
git pull origin main
```

---

## 🚀 Schritt 2: Build-Script ausführen

```bash
cd electron-app
./BUILD-MAC-LOKAL.sh
```

**Das Script macht automatisch:**
1. ✅ Prüft Ihr System (macOS, Node, Python)
2. ✅ Lädt MongoDB für Ihren Mac herunter (ARM64 oder Intel)
3. ✅ Installiert Python Packages **lokal** (nicht als venv!)
4. ✅ Erstellt Python Launcher
5. ✅ Kopiert Backend
6. ✅ Baut Frontend
7. ✅ Bereitet Assets vor
8. ✅ Baut die Electron App / DMG

**Dauer:** ~10-15 Minuten

---

## 📦 Schritt 3: App installieren

Nach erfolgreichem Build:

### **Falls DMG erstellt wurde:**
```bash
open dist/*.dmg
```

Dann:
1. Ziehen Sie "Booner Trade" nach Applications
2. Terminal öffnen:
   ```bash
   xattr -cr "/Applications/Booner Trade.app"
   ```
3. App starten!

### **Falls nur .app erstellt wurde:**
```bash
cp -r dist/mac*/Booner\ Trade.app /Applications/
xattr -cr "/Applications/Booner Trade.app"
open "/Applications/Booner Trade.app"
```

---

## 🔧 Was ist anders?

### **Vorher (Container-Build):**
- ❌ Python venv auf Linux erstellt
- ❌ Symlinks zeigen auf `/usr/local/bin/` (Linux)
- ❌ Funktioniert nicht auf macOS

### **Jetzt (Lokaler Mac-Build):**
- ✅ Python Packages direkt in `python-packages/` Ordner
- ✅ System-Python mit `PYTHONPATH` Trick
- ✅ Alle Pfade relativ und macOS-kompatibel
- ✅ Keine Symlinks auf fremde Systeme

---

## ❓ Troubleshooting

### Problem: "Node.js nicht gefunden"
```bash
# Installieren:
brew install node
# ODER von https://nodejs.org/
```

### Problem: "Python nicht gefunden"
```bash
# macOS hat Python3 vorinstalliert:
python3 --version

# Falls nicht:
brew install python@3.11
```

### Problem: "Build failed"
```bash
# Alte Dateien löschen und neu starten:
cd ~/Booner-Trade/electron-app
rm -rf node_modules dist mongodb-mac python-packages python-launcher backend frontend
./BUILD-MAC-LOKAL.sh
```

### Problem: App startet nicht
```bash
# Logs checken:
tail -f ~/Library/Logs/booner-trade/error.log
tail -f ~/Library/Logs/booner-trade/main.log
```

---

## 📝 Wichtige Hinweise

1. **Das Script muss auf Ihrem Mac laufen**, nicht im Container!
2. **Brew** ist hilfreich für Node.js Installation: https://brew.sh/
3. Die App wird für **Ihre Architektur** gebaut (ARM64 oder Intel)
4. MongoDB wird automatisch für Ihren Mac heruntergeladen
5. **Keine Emergent-Dependencies** - alles standalone!

---

## 🎉 Fertig!

Nach erfolgreicher Installation haben Sie eine **vollständig funktionierende** Desktop-App:

- ✅ MongoDB (Port 27017 oder dynamisch)
- ✅ FastAPI Backend (Port 8000)
- ✅ React Frontend
- ✅ Vollständig eigenständig
- ✅ Keine Internet-Verbindung nötig (außer für Trading APIs)

**Datenbank:** `~/Library/Application Support/booner-trade/database/`  
**Logs:** `~/Library/Logs/booner-trade/`

---

Viel Erfolg! 🚀
