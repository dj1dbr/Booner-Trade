# Emergent Dependencies - Desktop vs Web

## Problem

Die Desktop-App darf **KEINE** Emergent-spezifischen Dependencies verwenden:

❌ `emergentintegrations==0.1.0` - Nur für Emergent Platform

## Lösung

### Für Desktop-App

Verwende: `backend/requirements-desktop.txt`

Dieses File hat:
- ✅ Alle normalen Dependencies
- ❌ KEINE emergentintegrations

### Für Emergent Web-App

Verwende: `backend/requirements.txt` (original)

Dieses File hat:
- ✅ Alle Dependencies
- ✅ emergentintegrations (funktioniert nur in Emergent)

## Was das prepare-resources.sh Script macht

Das Script:
1. Prüft ob `requirements-desktop.txt` existiert
2. Falls ja: Verwendet Desktop-Version
3. Falls nein: Filtert `emergentintegrations` aus normalem requirements.txt

## Manuelle Installation (falls nötig)

```bash
# Desktop Python Environment:
cd electron-app/python-env
source bin/activate

# Installiere Desktop Requirements:
pip install -r ../../backend/requirements-desktop.txt

# Oder manuell filtern:
grep -v "emergentintegrations" ../../backend/requirements.txt | pip install -r /dev/stdin
```

## Wichtig für Backend-Code

Der Backend-Code muss auch ohne `emergentintegrations` laufen:

```python
# RICHTIG: Conditional Import
try:
    from emergentintegrations import get_llm_key
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    
# FALSCH: Direct Import
from emergentintegrations import get_llm_key  # ❌ Bricht Desktop-App!
```

## Was bedeutet das für Features?

### Funktioniert in BEIDEN Versionen:
- ✅ Trading Bot (MetaAPI)
- ✅ Alle Broker-Funktionen
- ✅ MongoDB
- ✅ AI mit eigenen API Keys

### Funktioniert NUR in Emergent Web:
- ❌ Emergent LLM Universal Key
- ❌ Emergent-spezifische Features

## Unterschiede zusammengefasst

| Feature | Desktop App | Emergent Web |
|---------|-------------|--------------|
| Trading Bot | ✅ | ✅ |
| MetaAPI | ✅ | ✅ |
| OpenAI (eigener Key) | ✅ | ✅ |
| Anthropic (eigener Key) | ✅ | ✅ |
| Google AI (eigener Key) | ✅ | ✅ |
| Emergent LLM Key | ❌ | ✅ |
| MongoDB | ✅ Embedded | ✅ Cloud |
| Python | ✅ Embedded | ✅ System |

## Troubleshooting

### "emergentintegrations not found" Fehler

**Ursache:** Script hat normales requirements.txt verwendet

**Lösung:**
```bash
cd electron-app/python-env
source bin/activate
pip uninstall emergentintegrations -y
pip install -r ../../backend/requirements-desktop.txt
deactivate
```

### "No module named emergentintegrations" beim App-Start

**Ursache:** Backend-Code importiert emergentintegrations direkt

**Lösung:** Backend-Code muss conditional imports verwenden (siehe oben)

### Requirements neu installieren

```bash
# Lösche Python Environment
rm -rf electron-app/python-env

# Erstelle neu mit Desktop Requirements
cd electron-app
./prepare-resources.sh
```

## Für Entwickler

Wenn du neue Dependencies hinzufügst:

1. Füge zu `backend/requirements.txt` hinzu (für Emergent)
2. Füge zu `backend/requirements-desktop.txt` hinzu (für Desktop)
3. Stelle sicher, dass Desktop-Version KEINE Emergent-Dependencies hat

## Support

Bei Fragen zu Dependencies:
- Web-Version: Verwende Emergent Support
- Desktop-Version: Prüfe requirements-desktop.txt
