# ✅ Router-Fix und Rebuild-Anleitung

## Problem gelöst:
Das Frontend zeigte einen schwarzen Bildschirm wegen eines React Router Fehlers.
**Fix:** BrowserRouter → HashRouter (Electron-kompatibel)

---

## 🚀 Schritte zum Rebuild:

### 1. Frontend neu bauen
```bash
cd /Users/dj1dbr/Desktop/Electrontrader/frontend
yarn build
```

### 2. Electron App neu bauen
```bash
cd /Users/dj1dbr/Desktop/Electrontrader/electron-app
./BUILD-MAC-LOKAL.sh
```

### 3. Die neue `.dmg` Datei installieren
Die neue DMG-Datei findest du unter:
```
/Users/dj1dbr/Desktop/Electrontrader/electron-app/dist/Booner Trade-1.0.0-arm64.dmg
```

### 4. Installation
1. Alte App löschen (falls vorhanden)
2. Neue `.dmg` öffnen
3. **Booner Trade** in den Programme-Ordner ziehen
4. **Gatekeeper umgehen** (falls nötig):
   ```bash
   xattr -cr "/Applications/Booner Trade.app"
   ```
5. App starten

---

## ✅ Was wurde geändert?
- **`frontend/src/App.js`**: `BrowserRouter` → `HashRouter`
- **Grund:** BrowserRouter funktioniert nicht mit `file://` URLs in Electron

---

## 📝 Nach dem Start prüfen:
Die App sollte jetzt das Dashboard anzeigen statt einem schwarzen Bildschirm.

**Logs zum Debuggen:**
```bash
tail -f ~/Library/Logs/booner-trade/main.log
tail -f ~/Library/Logs/booner-trade/error.log
```
