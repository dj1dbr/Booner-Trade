# 🔧 Fix: Schwarzer Bildschirm beim App-Start

## ❌ Problem
Die App startet, Backend läuft, aber das Fenster zeigt nur einen schwarzen/dunklen Bildschirm.

**Ursache:** Das React-Frontend wurde nicht korrekt in die App gepackt.

---

## ✅ Lösung 1: Diagnose (30 Sekunden)

Zuerst prüfen wir, ob das Frontend überhaupt in der App ist:

```bash
cd /Users/dj1dbr/mein_python_projekt/Rohstofftrader/Booner-Trade/electron-app

# Debug-Script ausführen
./debug-app-contents.sh
```

**Was zeigt das Script?**
- ✅ "Frontend build folder exists" + "index.html exists" → **Gehe zu Lösung 3**
- ❌ "Frontend build folder MISSING!" oder "index.html MISSING!" → **Gehe zu Lösung 2**

---

## ✅ Lösung 2: Frontend korrekt bauen & neu packen (5-10 Min)

```bash
cd /Users/dj1dbr/mein_python_projekt/Rohstofftrader/Booner-Trade

# 1. Frontend bauen
cd frontend
yarn install  # Falls node_modules fehlt
yarn build

# 2. Prüfe ob Build erfolgreich
ls -la build/
# Sollte zeigen:
# - index.html
# - static/
# - asset-manifest.json

# 3. Alte App löschen
rm -rf /Applications/Booner\ Trade.app

# 4. Zurück zu electron-app
cd ../electron-app

# 5. Dist-Ordner löschen (wichtig!)
rm -rf dist

# 6. App NEU bauen mit Frontend
yarn build:dmg

# 7. DMG installieren
open dist/Booner\ Trade-1.0.0-arm64.dmg

# 8. App in Applications ziehen (ersetze alte Version)
# 9. App starten
```

---

## ✅ Lösung 3: Backend-URL Problem (falls Frontend da ist)

Wenn das Frontend existiert, aber trotzdem nichts angezeigt wird, könnte es ein Backend-URL Problem sein:

### Prüfe Electron Console (für Experten):

1. **App mit DevTools starten:**
```bash
# Alte App schließen
killall "Booner Trade" 2>/dev/null

# App im Terminal starten (zeigt Logs)
/Applications/Booner\ Trade.app/Contents/MacOS/Booner\ Trade
```

2. **Schaue nach Fehlern** in der Terminal-Ausgabe:
   - `❌ index.html NOT FOUND` → Zurück zu Lösung 2
   - `Failed to load` → Frontend-Build-Problem
   - `Network error` → Backend-URL-Problem

---

## ✅ Lösung 4: Dev-Mode Test (schnellste Diagnose)

Teste die App im Development-Mode ohne zu builden:

### Terminal 1: Backend
```bash
cd /Users/dj1dbr/mein_python_projekt/Rohstofftrader/Booner-Trade/backend
python3 server.py
```

### Terminal 2: Frontend
```bash
cd /Users/dj1dbr/mein_python_projekt/Rohstofftrader/Booner-Trade/frontend
yarn start
```

Warte bis Browser sich öffnet. Wenn die App im Browser **funktioniert**, ist das Problem beim Electron-Packaging.

---

## 🐛 Häufige Probleme

### Problem: "yarn build" schlägt fehl
```bash
cd frontend
rm -rf node_modules
yarn install
yarn build
```

### Problem: "Out of memory" beim Build
```bash
# Memory Limit erhöhen
export NODE_OPTIONS="--max-old-space-size=4096"
cd frontend
yarn build
```

### Problem: App zeigt "Loading..." aber lädt nie
→ Backend-URL ist falsch konfiguriert

**Fix:**
```bash
# Prüfe Frontend .env
cat frontend/.env
# Sollte zeigen: REACT_APP_BACKEND_URL=http://localhost:8001

# Falls falsch/fehlt:
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > frontend/.env
cd frontend
yarn build
```

### Problem: MongoDB startet nicht
```bash
# Prüfe ob Port 27017 frei ist
lsof -i :27017

# Falls belegt, stoppe andere MongoDB
brew services stop mongodb-community
pkill -f mongod
```

---

## 📊 Checkliste für erfolgreichen Build

Vor dem Build prüfen:
- [ ] `frontend/build/` existiert und enthält `index.html`
- [ ] `frontend/.env` existiert mit `REACT_APP_BACKEND_URL=http://localhost:8001`
- [ ] `electron-app/assets/dmg-background.png` existiert
- [ ] `electron-app/assets/logo.png` oder `logo.icns` existiert

Nach dem Build prüfen:
- [ ] DMG wurde erstellt: `electron-app/dist/Booner Trade-1.0.0-arm64.dmg`
- [ ] App zeigt kein "File not found" beim Öffnen

Nach der Installation prüfen:
- [ ] `/Applications/Booner Trade.app` existiert
- [ ] `debug-app-contents.sh` zeigt alle Komponenten als ✅

---

## 🚀 Komplett-Neustart (wenn alles fehlschlägt)

```bash
cd /Users/dj1dbr/mein_python_projekt/Rohstofftrader/Booner-Trade

# 1. Alles aufräumen
rm -rf electron-app/dist
rm -rf electron-app/mongodb-mac
rm -rf electron-app/python-env
rm -rf frontend/build
rm -rf /Applications/Booner\ Trade.app

# 2. Frontend bauen
cd frontend
yarn install
yarn build

# 3. Zurück zu electron-app
cd ../electron-app

# 4. Komplett-Rebuild
./fix-and-rebuild.sh

# 5. Installieren
open dist/Booner\ Trade-1.0.0-arm64.dmg
```

⏱️ Dauer: ~15-20 Minuten

---

## 💡 Nach dem Fix

Wenn die App korrekt läuft, solltest du sehen:
1. **MongoDB startet** (Terminal-Log: "MongoDB ready")
2. **Backend startet** (Terminal-Log: "Starting Backend...")
3. **Fenster öffnet sich** mit der Booner Trade UI
4. **Dashboard wird geladen** mit Marktdaten

Wenn du weiterhin einen schwarzen Bildschirm siehst:
→ Führe `debug-app-contents.sh` aus und schicke mir die Ausgabe!
