# WTI Smart Trader - Deployment Guide

## 📋 Übersicht

Die App ist jetzt in **zwei Versionen** verfügbar:

### 1. 🌐 Web-Version (Browser)
- **URL**: https://smarttrade-hub-33.preview.emergentagent.com
- **Zugriff**: Über jeden modernen Browser (Chrome, Safari, Firefox)
- **Vorteil**: Keine Installation nötig, immer aktuell
- **Nutzung**: Überall verfügbar mit Internetverbindung

### 2. 💻 Desktop-App (Electron)
- **Plattformen**: macOS, Windows, Linux
- **Vorteil**: Native App, läuft lokal, Ollama-Integration
- **Nutzung**: Installierte App auf dem Computer

---

## 🚀 Desktop-App nutzen

### Voraussetzungen

Installieren Sie folgende Software:

1. **Python 3.9+**
   - macOS: `brew install python3`
   - Windows: https://www.python.org/downloads/
   - Linux: `sudo apt install python3 python3-pip`

2. **Node.js 16+**
   - macOS: `brew install node`
   - Windows/Linux: https://nodejs.org

3. **MongoDB**
   - macOS: `brew install mongodb-community`
   - Windows/Linux: https://www.mongodb.com/try/download/community

4. **Ollama (optional, für lokale KI)**
   - macOS: `brew install ollama`
   - Alle: https://ollama.ai/download

### App starten (Development)

```bash
# 1. Terminal öffnen
cd /app/electron

# 2. Dependencies installieren (nur beim ersten Mal)
yarn install

# 3. Backend-Dependencies (nur beim ersten Mal)
cd ../backend
pip install -r requirements.txt
cd ../electron

# 4. MongoDB starten
brew services start mongodb-community

# 5. Ollama starten (optional)
ollama serve

# 6. App starten!
./start-app.sh
```

Die App startet automatisch:
- ✅ Backend-Server (Port 8001)
- ✅ Desktop-Fenster mit der App

### App bauen (Production)

Erstellen Sie installierbare Versionen:

```bash
cd /app/electron

# macOS (.dmg Installer)
yarn build:mac

# Windows (.exe Installer)
yarn build:win

# Linux (.AppImage)
yarn build:linux
```

Ausgabe: `/app/electron/dist/`

---

## 🌐 Web-Version nutzen (Browser)

Die Web-Version läuft bereits auf:
**https://smarttrade-hub-33.preview.emergentagent.com**

### Lokale Entwicklung

```bash
# Backend starten
cd /app/backend
sudo supervisorctl restart backend

# Frontend starten (Development)
cd /app/frontend
yarn start
```

Dann öffnen: http://localhost:3000

### Production Deployment

Die App ist bereits deployed und läuft auf Kubernetes:
- **Frontend**: React-App wird ausgeliefert
- **Backend**: FastAPI auf `/api/*` Routen
- **Datenbank**: MongoDB

---

## 🤖 Ollama einrichten (Desktop-App)

Für KI **ohne Internet** und **ohne API-Kosten**:

### 1. Ollama installieren

```bash
# macOS
brew install ollama

# Windows/Linux
# Download von https://ollama.ai/download
```

### 2. Model herunterladen

```bash
# Llama 3 (empfohlen, 4GB)
ollama pull llama3

# Oder andere Models:
ollama pull mistral      # 4GB
ollama pull codellama    # 7GB
ollama pull phi          # 1.5GB (klein & schnell)
```

### 3. Ollama starten

```bash
ollama serve
```

### 4. In App-Settings konfigurieren

1. Öffnen Sie die App
2. Klicken Sie auf "⚙️ Einstellungen"
3. Bei "KI Provider" wählen: **Ollama (Lokal)**
4. Bei "Ollama Model" wählen: **llama3**
5. "Einstellungen speichern" klicken

✅ Fertig! Die App nutzt jetzt Ihre lokale KI!

---

## ⚙️ Beide Versionen parallel nutzen

Sie können **Desktop-App UND Web-Version** gleichzeitig verwenden:

| Szenario | Empfehlung |
|----------|------------|
| Unterwegs, schneller Zugriff | 🌐 Web-Version im Browser |
| Am Schreibtisch, volle Power | 💻 Desktop-App |
| Ohne Internet, mit Ollama | 💻 Desktop-App |
| Mehrere Geräte | 🌐 Web-Version |

**Wichtig**: Beide greifen auf die **gleiche Datenbank** zu (wenn Backend läuft)!

---

## 📊 Architektur

```
┌─────────────────────────────────────────┐
│         WTI Smart Trader                │
├─────────────────────────────────────────┤
│                                         │
│  🌐 Web-Version (Browser)              │
│  ├─ React Frontend (Port 3000)         │
│  ├─ FastAPI Backend (Port 8001)        │
│  └─ MongoDB (Port 27017)                │
│                                         │
│  💻 Desktop-App (Electron)             │
│  ├─ Electron Main Process              │
│  ├─ Embedded Backend (Port 8001)       │
│  ├─ Frontend (Production Build)        │
│  └─ MongoDB (lokal)                     │
│                                         │
│  🤖 KI Integration                     │
│  ├─ Emergent LLM Key (Cloud)           │
│  ├─ OpenAI / Gemini / Claude (APIs)    │
│  └─ Ollama (Lokal, Desktop-App)        │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Desktop-App startet nicht

**Problem**: "Backend konnte nicht gestartet werden"
- Lösung: Python & MongoDB installiert? `python3 --version` und `mongod --version`

**Problem**: "Port 8001 bereits belegt"
- Lösung: Stoppen Sie andere Backend-Instanzen: `sudo supervisorctl stop backend`

**Problem**: "Fenster bleibt weiß"
- Lösung: Warten Sie 5-10 Sekunden (Backend braucht Zeit zum Starten)

### Web-Version lädt nicht

**Problem**: "ERR_CONNECTION_REFUSED"
- Lösung: Backend läuft nicht. Starten: `sudo supervisorctl restart backend`

**Problem**: "Keine Daten werden angezeigt"
- Lösung: MongoDB läuft nicht. Starten: `brew services start mongodb-community`

### Ollama funktioniert nicht

**Problem**: "Connection refused to localhost:11434"
- Lösung: Ollama läuft nicht. Starten: `ollama serve`

**Problem**: "Model not found"
- Lösung: Model nicht installiert. Herunterladen: `ollama pull llama3`

---

## 📱 Features

### ✅ Beide Versionen

- Multi-Platform Trading (3 MT5 Accounts)
- 14 Rohstoffe (Gold, Silber, Öl, Gas, Agrar)
- KI Trading-Signale
- Echtzeit-Charts & Technische Indikatoren
- Auto-Trading & Risk Management
- Trade-History & Analytics

### ✅ Nur Desktop-App

- **Offline-Nutzung** (mit Ollama)
- **Native Performance**
- **System-Integration**
- **Keine Browser-Tabs**

### ✅ Nur Web-Version

- **Kein Download nötig**
- **Automatische Updates**
- **Von überall zugreifbar**
- **Cross-Device-Sync**

---

## 🎯 Nächste Schritte

### Für Desktop-App:

1. ✅ App-Icon erstellen (`/app/electron/icon.png`)
2. ✅ App für Ihre Plattform bauen (`yarn build:mac`)
3. ✅ Installer testen
4. ✅ In `/Applications` installieren
5. ✅ Ollama einrichten (optional)

### Für Web-Version:

1. ✅ Browser-Bookmark anlegen
2. ✅ Als PWA installieren (Chrome: "Installieren" Button)

---

**Version**: 1.0.0  
**Support**: Siehe README.md im jeweiligen Verzeichnis  
**Updates**: Automatisch für Web, manuell für Desktop
