# Booner Trade - macOS Desktop App

## Schnellstart

### App bauen
```bash
cd /app/electron-app
./build.sh
```

### DMG installieren
Die fertige `Booner Trade-1.0.0*.dmg` findest du in `dist/`

## Wichtige Unterschiede zur Emergent-Version

| Feature | Emergent (Web) | Desktop App |
|---------|----------------|-------------|
| Backend Port | 8001 | **8000** |
| Emergent LLM Key | ✅ | ❌ Nicht verfügbar |
| MongoDB | Cloud | **Embedded/Local** |
| Python Env | System | **Embedded** |
| Updates | Automatisch | Manuell |

## Konfiguration

### Backend Port
Die Desktop-App verwendet **Port 8000** (statt 8001).

Dies ist hart-kodiert in:
- `main.js` - Backend Startup
- `frontend/.env` (während Build)

**WICHTIG:** Port 8000 wird NUR in der Desktop-App verwendet.
Die Web-Version (Emergent) verwendet weiterhin Port 8001.

### AI/LLM Integration
Die Desktop-App kann **KEINE** Emergent LLM Keys verwenden.

Für AI-Features musst du eigene API Keys konfigurieren:
- OpenAI API Key
- Gemini API Key  
- Anthropic API Key
- Oder lokales Ollama

### Datenbank
MongoDB läuft embedded in der Desktop-App.
Daten werden gespeichert in:
```
~/Library/Application Support/Booner Trade/database/
```

## Build-Prozess Details

Das `build.sh` Script:
1. Konfiguriert Frontend für Port 8000
2. Baut React Production Build
3. Erstellt DMG mit electron-builder
4. Stellt original .env wieder her

**Build-Zeit:** ~10-15 Minuten

## Assets

### Automatisch erstellt:
- `dmg-background.png` (660x400)
- `logo.png` (1024x1024)

### Für bessere Qualität:
Siehe `CREATE-ASSETS.md` für Anleitung zur manuellen Erstellung mit:
- ImageMagick
- Inkscape
- Online-Tools

## Troubleshooting

### "App kann nicht geöffnet werden"
```bash
# macOS Sicherheit:
xattr -cr "/Applications/Booner Trade.app"
```

### "Port 8000 already in use"
```bash
# Finde Prozess auf Port 8000
lsof -ti:8000 | xargs kill -9
```

### "MongoDB failed to start"
```bash
# Lösche Database und starte neu
rm -rf ~/Library/Application\ Support/Booner\ Trade/database/
```

## Entwicklung

### Lokales Testen (ohne DMG Build)
```bash
cd /app/electron-app
yarn start
```

Dies startet die App im Development-Mode ohne Full-Build.

### Build ohne DMG (schneller)
```bash
yarn pack
```

Erstellt nur App-Bundle ohne DMG-Verpackung.

## Distribution

Die DMG-Datei kann direkt verteilt werden:
- Keine Code-Signierung (für private Nutzung OK)
- macOS zeigt Sicherheitswarnung
- User muss: Rechtsklick → Öffnen

Für öffentliche Distribution empfohlen:
- Apple Developer Account
- Code Signing
- Notarisierung

## Support

Bei Problemen:
1. Prüfe BUILD-ANLEITUNG.md
2. Prüfe TROUBLESHOOTING.md  
3. Logs in: ~/Library/Logs/Booner Trade/
