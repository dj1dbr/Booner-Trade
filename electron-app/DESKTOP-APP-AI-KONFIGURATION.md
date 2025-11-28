# 🤖 Desktop-App: AI/LLM Konfiguration

## ℹ️ Wichtiger Hinweis

Wenn du diese Warnung siehst:
```
ℹ️  Desktop-App Mode: Using Fallback (direct API keys)
```

**Das ist NORMAL und KORREKT!** ✅

---

## 🔍 Warum kein emergentintegrations?

**`emergentintegrations` funktioniert NUR auf der Emergent Plattform**, nicht in Standalone-Apps!

Die Desktop-App verwendet stattdessen **direkten API-Zugriff** (Fallback-Mode):
- ✅ OpenAI direkt
- ✅ Anthropic direkt  
- ✅ Google Gemini direkt
- ✅ Ollama (lokal)

**Vorteile:**
- Keine Abhängigkeit von Emergent-Servern
- Funktioniert offline (mit Ollama)
- Du kontrollierst deine API-Keys

**Nachteile:**
- ❌ Kein Emergent Universal Key
- ❌ Musst eigene API-Keys verwalten

---

## ⚙️ AI-Konfiguration in der Desktop-App

### Option 1: OpenAI (empfohlen)

1. Hole dir einen API-Key: https://platform.openai.com/api-keys
2. Öffne Booner Trade App
3. Gehe zu **Settings**
4. Wähle **AI Provider: OpenAI**
5. Gib deinen **OpenAI API Key** ein
6. Wähle **Model: gpt-4** oder **gpt-3.5-turbo**
7. Speichern

**Kosten:** ~$0.01-0.10 pro Trading-Signal (je nach Model)

### Option 2: Anthropic Claude

1. Hole dir einen API-Key: https://console.anthropic.com/
2. Settings → **AI Provider: Anthropic**
3. Gib deinen **Anthropic API Key** ein
4. Wähle **Model: claude-3-opus** oder **claude-3-sonnet**
5. Speichern

**Kosten:** ~$0.015-0.075 pro Trading-Signal

### Option 3: Google Gemini

1. Hole dir einen API-Key: https://makersuite.google.com/app/apikey
2. Settings → **AI Provider: Google**
3. Gib deinen **Gemini API Key** ein
4. Wähle **Model: gemini-pro**
5. Speichern

**Kosten:** Oft kostenlos (Free Tier)

### Option 4: Ollama (komplett offline & kostenlos!)

**Beste Option wenn du keine API-Keys verwalten willst!**

1. Installiere Ollama: https://ollama.ai/
   ```bash
   brew install ollama
   ```

2. Lade ein Model:
   ```bash
   ollama pull llama2
   # Oder für bessere Qualität:
   ollama pull mistral
   ```

3. Starte Ollama:
   ```bash
   ollama serve
   ```

4. Booner Trade App:
   - Settings → **AI Provider: Ollama**
   - **Model: llama2** (oder mistral)
   - **Base URL: http://localhost:11434**
   - Speichern

**Vorteile:**
- ✅ 100% kostenlos
- ✅ Keine API-Keys nötig
- ✅ Funktioniert offline
- ✅ Deine Daten bleiben lokal

**Nachteile:**
- Etwas langsamer als Cloud-APIs
- Benötigt ~4-8GB RAM

---

## 🧪 Testen der AI-Integration

### 1. AI Chat testen

1. Öffne **AI Chat** in der App
2. Sende eine Nachricht: "Analysiere GOLD"
3. Du solltest eine AI-generierte Antwort erhalten

### 2. AI Trading Bot testen

1. Settings → **Auto Trading: EIN**
2. Settings → **Use AI Analysis: EIN**
3. Prüfe Logs:
   ```bash
   /Applications/Booner\ Trade.app/Contents/MacOS/Booner\ Trade
   ```
4. Du solltest sehen: "AI-Signal generiert für [COMMODITY]"

---

## 🔧 Troubleshooting

### "Invalid API Key"

→ Prüfe deinen API-Key in den Settings
→ Prüfe ob du Guthaben hast (bei OpenAI/Anthropic)

### "Connection refused" (Ollama)

→ Ollama läuft nicht:
```bash
ollama serve
```

→ Falsche URL in Settings:
Sollte sein: `http://localhost:11434`

### AI Chat antwortet nicht

1. Prüfe welcher Provider aktiviert ist (Settings)
2. Prüfe API-Key
3. Prüfe Logs für Fehlermeldungen

### "Rate limit exceeded"

→ Zu viele Anfragen an API
→ Warte ein paar Minuten oder wechsle zu anderem Provider

---

## 💰 Kosten-Vergleich

| Provider | Model | Kosten/1000 Signale | Empfehlung |
|----------|-------|---------------------|------------|
| **Ollama** | Llama2/Mistral | **€0** | ⭐⭐⭐⭐⭐ Beste für Hobby |
| **Google** | Gemini Pro | **€0-5** | ⭐⭐⭐⭐ Free Tier! |
| **OpenAI** | GPT-3.5-turbo | **€10-50** | ⭐⭐⭐ Gut & schnell |
| **OpenAI** | GPT-4 | **€100-500** | ⭐⭐ Teuer aber beste Qualität |
| **Anthropic** | Claude Sonnet | **€15-75** | ⭐⭐⭐ Gute Balance |

**Empfehlung für Anfänger:**
1. Starte mit **Ollama** (kostenlos, lokal)
2. Wenn du mehr Qualität willst → **Google Gemini** (kostenlos/günstig)
3. Für beste AI-Trading → **OpenAI GPT-4** (teuer aber sehr gut)

---

## 📊 Welcher Provider für welchen Use-Case?

### Hobby-Trader (wenig Trading)
→ **Ollama** (kostenlos, ausreichend)

### Semi-Professional (täglich Trading)
→ **Google Gemini** oder **OpenAI GPT-3.5**

### Professional (High-Frequency Trading)
→ **OpenAI GPT-4** oder **Anthropic Claude Opus**

### Privacy-First (Daten bleiben lokal)
→ **Ollama** (100% offline)

---

## 🆘 Support

Bei Problemen mit AI-Integration:

1. Prüfe Logs:
   ```bash
   tail -f ~/Library/Application\ Support/booner-trade/logs/ai.log
   ```

2. Teste API-Key manuell:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

3. Prüfe ob Model verfügbar ist

---

## ✅ Best Practices

1. **Speichere API-Keys sicher** - Sie sind in der App verschlüsselt
2. **Setze Spending-Limits** bei OpenAI/Anthropic
3. **Starte mit Ollama** zum Testen (kostenlos)
4. **Wechsle Provider** wenn Rate-Limits erreicht sind
5. **Überwache Kosten** regelmäßig

Die Desktop-App ist so konzipiert, dass sie **ohne Cloud-Abhängigkeiten** funktioniert. Der Fallback-Mode ist kein Bug, sondern ein **Feature** für maximale Flexibilität! 🎯
