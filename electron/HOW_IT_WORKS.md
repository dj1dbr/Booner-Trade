# 🔧 Wie die Desktop-App funktioniert

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────┐
│        WTI Smart Trader Desktop App             │
│                 (Electron)                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │   Electron Window (Native)               │  │
│  │   ├─ Keine Browser-Tabs                  │  │
│  │   ├─ Native Menüs & Dialoge              │  │
│  │   └─ System-Integration                  │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   React Frontend (localhost:8001)        │  │
│  │   ├─ Production Build (eingebaut)        │  │
│  │   ├─ Wird vom Backend ausgeliefert       │  │
│  │   └─ Alle Assets lokal                   │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   FastAPI Backend (Port 8001)            │  │
│  │   ├─ Auto-Start beim App-Start           │  │
│  │   ├─ Läuft im Hintergrund                │  │
│  │   ├─ Liefert Frontend aus                │  │
│  │   └─ API Endpoints (/api/*)              │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   MongoDB (localhost:27017)              │  │
│  │   ├─ Läuft lokal auf dem System          │  │
│  │   ├─ Speichert Trades & Settings         │  │
│  │   └─ Muss manuell gestartet sein         │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   MetaAPI (Internet)                     │  │
│  │   ├─ MT5 Libertex Demo                   │  │
│  │   ├─ MT5 ICMarkets Demo                  │  │
│  │   └─ MT5 Libertex REAL                   │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   KI Integration                         │  │
│  │   ├─ Emergent LLM Key (Cloud)            │  │
│  │   ├─ OpenAI/Gemini/Claude (Internet)     │  │
│  │   └─ Ollama (Lokal, localhost:11434)     │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Startup-Ablauf

### Was passiert beim App-Start?

```
1. 🚀 Electron-App gestartet (Doppelklick auf Icon)
   ├─ main.js wird ausgeführt
   └─ Electron Main Process läuft

2. 🐍 Backend automatisch starten
   ├─ Python server.py wird gestartet
   ├─ Port 8001 wird geöffnet
   ├─ MongoDB-Verbindung wird aufgebaut
   ├─ MetaAPI SDK verbindet sich
   └─ Warte 5 Sekunden (Backend-Init)

3. 🪟 Fenster erstellen
   ├─ Native App-Fenster öffnet sich
   ├─ Lädt http://localhost:8001
   ├─ Backend liefert React-App aus
   └─ Warte auf "ready-to-show"

4. ✅ App ist bereit!
   ├─ Frontend geladen
   ├─ Backend läuft im Hintergrund
   ├─ Verbindungen zu MT5-Plattformen
   └─ KI ist bereit

Total: ~8-10 Sekunden von Klick bis Ready
```

---

## Was ist EINGEBAUT?

### In der .app/.exe Datei:

```
WTI Smart Trader.app/
├── Contents/
│   ├── MacOS/
│   │   └── WTI Smart Trader     ← Executable
│   ├── Resources/
│   │   ├── app.asar             ← Electron Code + Frontend
│   │   ├── icon.icns            ← App Icon
│   │   └── backend/             ← Python Backend
│   │       ├── server.py
│   │       ├── requirements.txt
│   │       └── ...
│   └── Frameworks/              ← Electron Framework
```

### Was wird beim Build NICHT eingebaut:

- ❌ Python (muss installiert sein)
- ❌ MongoDB (muss installiert sein)
- ❌ Ollama (optional)
- ❌ Node.js (nur für Build benötigt)

---

## Unterschied: Development vs. Production

### Development (Terminal-Start):

```bash
./start-app.sh
```

- Backend läuft separat
- Live-Reload möglich
- DevTools verfügbar
- Logs sichtbar

### Production (Installed App):

```
Doppelklick auf Icon
```

- Alles eingebaut
- Backend startet automatisch
- Keine Logs (außer Console)
- Wie jede normale App

---

## Backend im Hintergrund

### Wie läuft das Backend?

```javascript
// In main.js:
backendProcess = spawn('python', ['server.py']);
```

- Backend läuft als Child-Process
- Unsichtbar für User
- Wird bei App-Ende automatisch beendet
- Logs gehen an Electron Console

### Port-Nutzung:

- **8001**: Backend API & Frontend
- **27017**: MongoDB (extern)
- **11434**: Ollama (extern, optional)

---

## Offline-Fähigkeit

### Was funktioniert OFFLINE?

Mit **Ollama installiert**:
- ✅ KI Trading-Analyse (lokal)
- ✅ Charts & Indikatoren (gecacht)
- ✅ Historische Daten (in DB)
- ✅ App-Navigation

### Was braucht INTERNET?

- ❌ Live MT5 Trading (MetaAPI)
- ❌ Echtzeit-Marktdaten (MetaAPI)
- ❌ Cloud-KI (OpenAI, Gemini, Claude)
- ❌ Emergent LLM Key

---

## Warum diese Architektur?

### Vorteile:

1. **Bekannte Technologien**
   - React (Frontend) - wie gewohnt
   - FastAPI (Backend) - Python-Power
   - Electron (Wrapper) - Cross-Platform

2. **Code-Wiederverwendung**
   - Gleicher Code wie Web-Version
   - Ein Codebase, zwei Versionen
   - Updates gleichzeitig

3. **Flexibilität**
   - Lokale KI (Ollama)
   - Cloud-KI (Emergent/OpenAI)
   - Beide gleichzeitig möglich

4. **Native Feel**
   - Kein Browser-Frame
   - System-Menüs
   - Spotlight/Start-Menü Integration

### Nachteile:

- Backend muss lokal laufen
- Python & MongoDB erforderlich
- Größerer Download (~200MB)
- Setup-Aufwand für User

---

## Debugging

### Development:

```bash
# Terminal 1: Backend manuell
cd /app/backend
python server.py

# Terminal 2: Electron
cd /app/electron
ELECTRON_DEV=1 yarn start
```

### Logs ansehen:

```bash
# Backend Logs
tail -f /var/log/supervisor/backend.*.log

# Electron Console
# Öffnet sich automatisch im Dev-Mode
```

---

## Updates

### Wie wird die App aktualisiert?

**Aktuell**: Manuelle Neuinstallation
1. Neue Version bauen
2. Neuen Installer verteilen
3. User installiert Update

**Zukünftig**: Auto-Update
- Electron-Updater einbauen
- GitHub Releases nutzen
- Automatische Downloads

---

**Version**: 1.0.0  
**Architektur**: Electron + React + FastAPI + MongoDB
