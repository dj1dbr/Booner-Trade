# 🔑 API-KEYS SETUP - 5 Minuten Guide

## 🎯 Ziel: Maximale Trading-Intelligenz durch News & Economic Data

Der AI Trading Bot kann **kostenlose APIs** nutzen für:
- 📰 Real-time Commodities News
- 📅 Economic Calendar (Fed-Entscheidungen, etc.)
- 🌍 Market Sentiment Analysis

**Alles kostenlos! Keine Kreditkarte nötig!**

---

## 🚀 SCHNELLSTART (empfohlen: Finnhub)

### Option 1: Nur Finnhub (beste Option)

**Warum Finnhub?**
- ✅ Meiste Features (News + Economic Calendar)
- ✅ 60 API calls/min (sehr großzügig)
- ✅ Keine Kreditkarte nötig
- ✅ 1 Minute Setup

**Setup:**

1. **Registrieren:**
   ```
   https://finnhub.io/register
   ```
   - Email + Name eingeben
   - Account erstellen

2. **API Key kopieren:**
   - Nach Registrierung direkt sichtbar
   - Oder: Dashboard → API Key

3. **In .env eintragen:**
   ```bash
   # Öffne .env Datei
   nano /app/backend/.env
   
   # Füge hinzu:
   FINNHUB_API_KEY=dein_key_hier
   
   # Speichern: Ctrl+O, Enter, Ctrl+X
   ```

4. **Backend neu starten:**
   ```bash
   sudo supervisorctl restart backend
   ```

5. **Fertig!** ✅

---

## 📊 ALLE 3 APIS (Maximum Intelligence)

### 1. Finnhub (Priorität 1)
```
URL: https://finnhub.io/register
Features: News + Economic Calendar
Limit: 60 calls/min
Setup: 1 Minute
```

### 2. NewsAPI (Priorität 2)
```
URL: https://newsapi.org/register
Features: 100+ News-Quellen
Limit: 100 calls/day
Setup: 1 Minute
```

### 3. Alpha Vantage (Priorität 3)
```
URL: https://www.alphavantage.co/support/#api-key
Features: Sentiment Scores
Limit: 500 calls/day
Setup: 30 Sekunden (nur Email)
```

---

## 📝 .ENV Konfiguration

**Vollständige .env Datei:**

```bash
# ══════════════════════════════════════════════
# Trading Bot APIs
# ══════════════════════════════════════════════

# Finnhub - News & Economic Calendar (EMPFOHLEN)
FINNHUB_API_KEY=

# NewsAPI - Multi-Source News (OPTIONAL)
NEWS_API_KEY=

# Alpha Vantage - Sentiment Analysis (OPTIONAL)
ALPHA_VANTAGE_KEY=

# ══════════════════════════════════════════════
# MongoDB & Server (NICHT ÄNDERN)
# ══════════════════════════════════════════════
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
# ... rest bleibt gleich
```

---

## ✅ VERIFIZIERUNG

### 1. Backend-Logs prüfen:

```bash
tail -f /var/log/supervisor/backend.err.log | grep "News\|Economic"
```

**Mit API-Keys:**
```
📰 Finnhub News für GOLD: 15 Artikel, Sentiment: bullish
📅 Economic Calendar: 8 Events, 2 High-Impact
```

**Ohne API-Keys:**
```
ℹ️  Keine News-Daten für GOLD verfügbar
```

### 2. Bot-Status prüfen:

```bash
curl http://localhost:8001/api/bot/status
```

**Sollte zeigen:** `"running": true`

---

## ❓ FAQ

### Brauche ich alle 3 APIs?
**Nein!** Bot funktioniert mit:
- ✅ Alle 3 = Maximum (empfohlen)
- ✅ Nur Finnhub = 90% Features
- ✅ Keine = Nur technische Analyse

### Kosten die APIs Geld?
**Nein!** Alle 3 haben großzügige kostenlose Tiers:
- Finnhub: 60 calls/min
- NewsAPI: 100 calls/day
- Alpha Vantage: 500 calls/day

**Der Bot cached Daten, nutzt also sehr wenig API-Calls!**

### Wie lange dauert Setup?
- **Finnhub:** 1 Minute
- **NewsAPI:** 1 Minute
- **Alpha Vantage:** 30 Sekunden

**Gesamt: ~3 Minuten für alle 3!**

### Was passiert ohne API-Keys?
Bot funktioniert normal, nutzt aber nur:
- Technische Indikatoren (RSI, MACD, etc.)
- Support/Resistance Levels

**Fehlt:** News-Sentiment, Economic Events

### Kann ich die Keys später hinzufügen?
**Ja!** Einfach:
1. Keys in .env eintragen
2. Backend neu starten
3. Bot nutzt sie automatisch

---

## 🎯 EMPFEHLUNG

**Für beste Ergebnisse:**

1. **Registriere ALLE 3 APIs** (5 Minuten)
2. **Trage Keys in .env ein**
3. **Starte Backend neu**
4. **Beobachte Bot-Logs** → Sieh wie Bot News nutzt!

**Der Bot wird dadurch deutlich intelligenter! 🧠**

---

## 📋 CHECKLISTE

- [ ] Finnhub Account erstellt
- [ ] Finnhub API Key in .env eingetragen
- [ ] (Optional) NewsAPI Account erstellt
- [ ] (Optional) NewsAPI Key in .env eingetragen
- [ ] (Optional) Alpha Vantage Key geholt
- [ ] (Optional) Alpha Vantage Key in .env eingetragen
- [ ] Backend neu gestartet: `sudo supervisorctl restart backend`
- [ ] Logs geprüft: `tail -f /var/log/supervisor/backend.err.log`
- [ ] Bot nutzt News & Events ✅

---

## 🚀 FERTIG!

**In 5 Minuten hast du deinem Bot maximale Trading-Intelligenz gegeben!**

Der Bot analysiert jetzt:
- ✅ Technische Indikatoren
- ✅ Real-time News
- ✅ Economic Calendar
- ✅ Market Sentiment
- ✅ Support/Resistance

**= Viel bessere Trading-Entscheidungen! 💰🤖**

---

## 📞 Support

Wenn etwas nicht funktioniert:

1. **Prüfe .env Datei:** Keys richtig eingetragen?
2. **Backend-Logs:** `tail -f /var/log/supervisor/backend.err.log`
3. **Bot-Status:** `curl http://localhost:8001/api/bot/status`

**Bot funktioniert auch ohne APIs, aber mit APIs ist er viel besser!**
