# WTI Smart Trader - Desktop App

## 🚀 Installation

### Voraussetzungen
- Python 3.9+
- Node.js 16+
- MongoDB (läuft lokal auf Port 27017)
- Ollama (optional, für lokale KI)

### Desktop App starten

1. **Backend-Dependencies installieren:**
```bash
cd /app/backend
pip install -r requirements.txt
```

2. **Electron App starten:**
```bash
cd /app/electron
yarn install
yarn start
```

Die App startet automatisch das Backend und öffnet das Desktop-Fenster!

---

## 🌐 Web-Version (Browser)

Die Web-Version bleibt weiterhin verfügbar!

### Starten:

1. **Backend starten:**
```bash
cd /app/backend
python server.py
```

2. **Frontend starten (Development):**
```bash
cd /app/frontend
yarn install
yarn start
```

3. **Im Browser öffnen:**
```
http://localhost:3000
```

ODER für Production:
```
https://tradinghelm.preview.emergentagent.com
```

---

## 📦 Desktop App bauen

### macOS:
```bash
cd /app/electron
yarn build:mac
```

Ausgabe: `dist/WTI Smart Trader.dmg`

### Windows:
```bash
yarn build:win
```

Ausgabe: `dist/WTI Smart Trader Setup.exe`

### Linux:
```bash
yarn build:linux
```

Ausgabe: `dist/WTI Smart Trader.AppImage`

---

## 🤖 Ollama Integration (Desktop)

Für lokale KI ohne Internet:

1. **Ollama installieren:**
   - macOS: `brew install ollama`
   - Windows/Linux: https://ollama.ai/download

2. **Model herunterladen:**
```bash
ollama pull llama3
```

3. **In App-Settings einstellen:**
   - AI Provider: "Ollama (Lokal)"
   - Ollama Model: "llama3"
   - Ollama Server URL: "http://localhost:11434"

✅ Fertig! Die App nutzt jetzt lokale KI!

---

## ⚙️ Unterschiede: Desktop vs. Web

| Feature | Desktop App | Web-Version |
|---------|-------------|-------------|
| Installation | Download & Install | Browser öffnen |
| Backend | Automatisch gestartet | Manuell starten |
| Offline-Nutzung | ✅ Ja (mit Ollama) | ❌ Nein |
| Updates | Neue Version installieren | Automatisch |
| Plattform | macOS, Windows, Linux | Alle Browser |

---

## 🔧 Troubleshooting

**Backend startet nicht in Desktop App:**
- Prüfen Sie, ob Python & MongoDB installiert sind
- Prüfen Sie Logs in der Console

**Web-Version lädt nicht:**
- Backend läuft auf Port 8001
- Frontend läuft auf Port 3000
- Prüfen Sie `sudo supervisorctl status`

**Ollama funktioniert nicht:**
- Stellen Sie sicher, dass Ollama läuft: `ollama serve`
- Model muss heruntergeladen sein: `ollama list`

---

## 📊 Features

✅ Multi-Platform Trading (MT5 Libertex, ICMarkets, Libertex REAL)
✅ 14 Rohstoffe (Gold, Silber, Öl, Gas, Agrar-Rohstoffe)
✅ KI-gestützte Trading-Signale (GPT-5, Claude, Gemini, Ollama)
✅ Echtzeit-Charts mit technischen Indikatoren
✅ Auto-Trading & Risk Management
✅ Desktop & Web-Version verfügbar

---

**Version:** 1.0.0
**Lizenz:** MIT
