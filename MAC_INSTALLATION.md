# Mac Installation Guide - Rohstoff Trader

Diese Anleitung hilft Ihnen, die Trading-App auf Ihrem Mac zu installieren und zu betreiben.

## Problem: `emergentintegrations` auf dem Mac

Die App nutzt normalerweise `emergentintegrations` für LLM-Integration. Diese Bibliothek ist jedoch **nur in der Emergent Cloud verfügbar** und nicht für lokale Macs.

**Wichtig:** Der `EMERGENT_LLM_KEY` (sk-emergent-...) funktioniert **NUR** mit der `emergentintegrations` Bibliothek in der Cloud. Auf dem Mac brauchen Sie:
- ✅ Ollama (kostenlos, lokal) **← EMPFOHLEN**
- ✅ Echten OpenAI API-Key
- ✅ Anthropic Claude API-Key
- ✅ Google Gemini API-Key

### ✅ Lösung: Automatischer Fallback

Wir haben einen **automatischen Fallback** implementiert, der die Standard-SDKs verwendet:

```
emergentintegrations nicht verfügbar
    ↓
Automatischer Fallback zu:
    • OpenAI SDK (braucht echten OpenAI-Key!)
    • Anthropic SDK (braucht Claude-Key!)
    • Google Generative AI SDK (braucht Gemini-Key!)
    • Ollama (LOKAL - kein Key nötig!) ⭐
```

## Installation

### 1. Python-Abhängigkeiten installieren

Für die AI-Features benötigen Sie die entsprechenden SDKs:

```bash
cd /pfad/zum/trader/backend

# Basis-Installation (ohne AI)
pip install -r requirements.txt

# OPTIONAL: AI-Features aktivieren
# Wählen Sie, was Sie brauchen:

# Für OpenAI GPT-4/5
pip install openai

# Für Anthropic Claude
pip install anthropic

# Für Google Gemini
pip install google-generativeai

# Alle AI-Provider
pip install openai anthropic google-generativeai
```

### 2. API-Keys konfigurieren

Fügen Sie Ihren API-Key in `backend/.env` hinzu:

```bash
# Für Emergent Universal Key (funktioniert mit allen Providern)
EMERGENT_LLM_KEY=sk-emergent-...

# ODER für direkten OpenAI Zugriff
OPENAI_API_KEY=sk-...

# ODER für Claude
ANTHROPIC_API_KEY=sk-ant-...

# ODER für Gemini
GOOGLE_API_KEY=...
```

### 3. Backend starten

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Frontend starten

```bash
cd frontend
yarn install
yarn start
```

## AI-Provider Auswahl

In den Einstellungen können Sie wählen:

1. **Emergent LLM Key** (Universal) - Funktioniert mit allen Providern
2. **OpenAI** - Direkter OpenAI Zugriff
3. **Anthropic Claude** - Direkter Claude Zugriff
4. **Google Gemini** - Direkter Gemini Zugriff
5. **Ollama** - Lokal auf Ihrem Mac (100% kostenlos!)

### ⭐ Empfehlung für Mac: Ollama

Ollama ist die **beste Option** für lokale Entwicklung:

```bash
# 1. Ollama installieren
brew install ollama

# 2. Ollama starten (eigenes Terminal)
ollama serve

# 3. Modell herunterladen
ollama pull llama3

# 4. In der Trading-App Settings:
#    KI Provider: "Ollama"
#    KI Modell: "llama3"
#    API-Key: (leer lassen oder beliebiger Text)
```

**Vorteile:**
- ✅ **Komplett kostenlos** (keine API-Kosten!)
- ✅ **Keine API-Keys nötig** (läuft lokal)
- ✅ **Datenschutz** (keine Daten in Cloud)
- ✅ **Schnell genug** für Trading-Analysen
- ✅ **Kein Emergent LLM Key Problem**

**Verfügbare Modelle:**
```bash
ollama pull llama3         # Empfohlen (7-70B)
ollama pull mistral        # Alternative
ollama pull codellama      # Für Code-Analysen
```

## Technische Details

### Wie funktioniert der Fallback?

Die App prüft automatisch, ob `emergentintegrations` verfügbar ist:

```python
# In llm_fallback.py
try:
    from emergentintegrations.llm.chat import LlmChat
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    # Nutze Standard-SDKs
```

### Unterstützte Provider im Fallback

| Provider | Lokale Installation | Cloud API |
|----------|---------------------|-----------|
| OpenAI | `pip install openai` | ✅ |
| Anthropic | `pip install anthropic` | ✅ |
| Google Gemini | `pip install google-generativeai` | ✅ |
| Ollama | `brew install ollama` | ❌ (lokal) |

## Fehlerbehebung

### "emergentintegrations not found"

**Normal!** Das ist kein Fehler. Die App nutzt automatisch den Fallback.

### "OpenAI SDK nicht installiert"

Installieren Sie das benötigte SDK:
```bash
pip install openai
```

### "API Key ungültig"

Prüfen Sie Ihre API Keys in `backend/.env`:
```bash
cat backend/.env | grep API_KEY
```

## Migration von Emergent Cloud zu Mac

Wenn Sie die App von Emergent Cloud auf Ihren Mac verschieben:

1. ✅ **Code funktioniert ohne Änderungen**
2. ✅ **Automatischer Fallback** zu Standard-SDKs
3. ⚠️ **API-Keys**: Müssen in `.env` konfiguriert werden
4. ⚠️ **MetaTrader**: Funktioniert nur über MetaAPI (Cloud)

## Performance-Vergleich

| Provider | Geschwindigkeit | Kosten | Datenschutz |
|----------|----------------|--------|-------------|
| Emergent Cloud | ⚡⚡⚡ Sehr schnell | 💰 Pay-per-use | ☁️ Cloud |
| OpenAI direkt | ⚡⚡ Schnell | 💰💰 Teurer | ☁️ Cloud |
| Ollama lokal | ⚡ Mittel | 🆓 Kostenlos | 🔒 Lokal |

## Zusätzliche Ressourcen

- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic Claude Docs](https://docs.anthropic.com)
- [Google Gemini Docs](https://ai.google.dev/docs)
- [Ollama](https://ollama.ai)

## Support

Bei Problemen:
1. Prüfen Sie Backend-Logs: `tail -f /var/log/supervisor/backend.*.log`
2. Prüfen Sie Browser-Konsole (F12)
3. Testen Sie die API: `curl http://localhost:8001/api/market/all`

---

**Wichtig:** Diese App ist für den persönlichen Gebrauch bestimmt. Trading birgt Risiken!
