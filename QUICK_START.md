# 🚀 Quick Start Guide - WTI Smart Trader

## Zwei Versionen verfügbar:

### 🌐 Web-Version (SOFORT NUTZEN)
Keine Installation nötig!

**URL öffnen:**
```
https://tradinghelm.preview.emergentagent.com
```

✅ Fertig! Läuft im Browser.

---

### 💻 Desktop-App (INSTALLIEREN)

#### Option 1: Fertige App installieren (EMPFOHLEN)

1. **App bauen** (einmalig):
```bash
cd /app/electron
./build-app.sh
```

2. **Installer finden:**
- **macOS**: `dist/WTI Smart Trader.dmg`
- **Windows**: `dist/WTI Smart Trader Setup.exe`
- **Linux**: `dist/WTI Smart Trader.AppImage`

3. **Installieren:**
- **macOS**: .dmg öffnen → App nach `/Applications` ziehen
- **Windows**: .exe ausführen → Setup folgen
- **Linux**: Rechtsklick → Ausführbar → Doppelklick

4. **Starten:**
- Doppelklick auf App-Icon in Applications/Startmenü
- KEIN Terminal, KEIN Browser nötig!
- App startet automatisch Backend im Hintergrund

---

#### Option 2: Development-Version (Terminal)

Nur für Entwicklung/Testing:

```bash
cd /app/electron
./start-app.sh
```

---

## 🤖 Ollama einrichten (Desktop-App)

Für **kostenlose lokale KI** ohne Internet:

```bash
# 1. Ollama installieren
brew install ollama  # macOS

# 2. Model herunterladen
ollama pull llama3   # 4GB

# 3. Starten
ollama serve

# 4. In App: Einstellungen → KI Provider → "Ollama"
```

✅ Fertig! KI läuft lokal!

---

## 📋 Was braucht die Desktop-App?

**Auf Ihrem Computer muss installiert sein:**
- ✅ Python 3.9+ (`python3 --version`)
- ✅ MongoDB (`mongod --version`)
- ⭐ Ollama (optional, für lokale KI)

**Installation:**
```bash
# macOS
brew install python3 mongodb-community ollama

# Nach Installation MongoDB starten:
brew services start mongodb-community
```

---

## 🎯 Empfehlung

| Situation | Nutzen Sie |
|-----------|------------|
| Schneller Trading-Zugriff | 🌐 Web-Version |
| Volle Leistung am Desktop | 💻 Desktop-App |
| Offline/Lokale KI | 💻 Desktop-App + Ollama |
| Unterwegs/mehrere Geräte | 🌐 Web-Version |

**Tipp**: Beide Versionen können parallel laufen!

---

## ❓ Hilfe

**Desktop-App startet nicht?**
- Python installiert? → `python3 --version`
- MongoDB läuft? → `brew services start mongodb-community`

**Web-Version lädt nicht?**
- Backend läuft? → `sudo supervisorctl restart backend`

**Ollama funktioniert nicht?**
- Läuft Ollama? → `ollama serve`
- Model installiert? → `ollama list`

---

## 📚 Mehr Details

- **Vollständige Anleitung**: `/app/electron/README.md`
- **Deployment Guide**: `/app/DEPLOYMENT_GUIDE.md`
- **Electron Details**: `/app/electron/`

**Support**: Siehe README.md Dateien

---

**Version**: 1.0.0  
**Update**: Nov 2025
