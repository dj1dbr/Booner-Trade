# 🎯 Dual Trading Strategy - Dokumentation

## Übersicht

Ihr Trading-Bot unterstützt jetzt **zwei parallele Trading-Strategien**, die gleichzeitig und unabhängig voneinander laufen können:

1. **Swing Trading** (Langfristig) - Standard aktiviert
2. **Day Trading** (Kurzfristig / Hochfrequenz) - Optional

---

## ✨ Neue Features

### 1. Swing Trading (Standard)
**Profil:** Konservativ, längerfristige Positionen mit größeren Gewinnzielen

- ✅ **Standardmäßig aktiviert**
- **Min. Confidence:** 60% (nur starke Signale)
- **Stop Loss:** 2.0% (normaler Schutz)
- **Take Profit:** 4.0% (größeres Gewinnziel)
- **Max Positionen:** 5 gleichzeitig
- **Balance-Limit:** 80% der Gesamt-Balance
- **Max Haltezeit:** 7 Tage
- **Analyse-Intervall:** Alle 10 Minuten

**Ideal für:** Stabile Marktbedingungen, Trendfolge-Strategien

---

### 2. Day Trading (NEU!)
**Profil:** Aggressiv, schnelle In-and-Out Trades mit kleinen Gewinnen

- ⚠️ **Standardmäßig DEAKTIVIERT** (muss aktiviert werden)
- **Min. Confidence:** 40% (niedrigere Schwelle = mehr Trades)
- **Stop Loss:** 0.5% (enger Schutz)
- **Take Profit:** 0.8% (kleineres Gewinnziel)
- **Max Positionen:** 10 gleichzeitig
- **Balance-Limit:** 20% der Gesamt-Balance
- **Max Haltezeit:** 2 Stunden (automatisches Schließen!)
- **Analyse-Intervall:** Jede Minute

**Ideal für:** Volatile Märkte, schnelle Scalping-Chancen

**⚠️ WICHTIG:** Day-Trading-Positionen werden automatisch nach 2 Stunden geschlossen, auch wenn SL/TP nicht erreicht wurden!

---

## 🌍 Neue Assets

### Forex-Paar hinzugefügt:
- **EUR/USD** - Das meistgehandelte Währungspaar der Welt

**Jetzt handelbar:**
- 14 Rohstoffe (Gold, Silber, WTI, Brent, Gas, Agrar-Rohstoffe, etc.)
- 1 Forex-Paar (EUR/USD)

---

## ⚙️ Konfiguration

### Via API (POST `/api/settings`)

```json
{
  "swing_trading_enabled": true,
  "day_trading_enabled": false,
  
  "swing_min_confidence_score": 0.6,
  "swing_stop_loss_percent": 2.0,
  "swing_take_profit_percent": 4.0,
  "swing_max_positions": 5,
  "swing_max_balance_percent": 80.0,
  
  "day_min_confidence_score": 0.4,
  "day_stop_loss_percent": 0.5,
  "day_take_profit_percent": 0.8,
  "day_max_positions": 10,
  "day_max_balance_percent": 20.0
}
```

### Via MongoDB

```javascript
db.trading_settings.updateOne(
  { id: "trading_settings" },
  { 
    $set: {
      "day_trading_enabled": true  // Day Trading aktivieren
    }
  }
)
```

---

## 📊 Strategie-Vergleich

| Feature | Swing Trading | Day Trading |
|---------|--------------|-------------|
| **Confidence** | 60% | 40% |
| **Stop Loss** | 2.0% | 0.5% |
| **Take Profit** | 4.0% | 0.8% |
| **Max Positions** | 5 | 10 |
| **Balance** | 80% | 20% |
| **Haltezeit** | 7 Tage | 2 Stunden |
| **Analyse** | 10 Min | 1 Min |
| **Risk/Reward** | 1:2 | 1:1.6 |

---

## 🔍 Wie es funktioniert

### Parallele Ausführung

Der Bot führt in jeder Iteration (alle 10 Sekunden) folgende Schritte aus:

1. **Marktdaten aktualisieren** (alle Assets)
2. **Positionen überwachen** (beide Strategien)
3. **Swing Trading analysieren** (wenn aktiviert)
4. **Day Trading analysieren** (wenn aktiviert)
5. **Abgelaufene Day-Trades schließen** (Time-Based Exit)

### Balance-Management

- **Swing Trading:** Nutzt max. 80% der Gesamt-Balance
- **Day Trading:** Nutzt max. 20% der Gesamt-Balance
- **Zusammen:** Können theoretisch 100% der Balance nutzen

### Position-Tracking

Jede Position erhält ein `strategy`-Tag in der Datenbank:
- `"strategy": "swing"` - Swing Trading Position
- `"strategy": "day"` - Day Trading Position

Dies ermöglicht getrennte Analyse und Reporting.

---

## 🚀 Day Trading aktivieren

### Methode 1: API Call

```bash
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{"day_trading_enabled": true}'
```

### Methode 2: MongoDB

```javascript
use test_database
db.trading_settings.updateOne(
  { id: "trading_settings" },
  { $set: { day_trading_enabled: true } }
)
```

### Methode 3: Frontend (zukünftig)

Ein Toggle im Settings-Panel wird hinzugefügt.

---

## 📈 Monitoring

### Bot-Status prüfen

```bash
curl http://localhost:8001/api/bot/status
```

### Settings prüfen

```bash
curl http://localhost:8001/api/settings | jq '.swing_trading_enabled, .day_trading_enabled'
```

### Backend-Logs

```bash
tail -f /var/log/supervisor/backend.err.log | grep -E "Swing|Day"
```

**Erwartete Log-Ausgaben:**
```
🧠 KI analysiert Markt für neue Swing Trading Möglichkeiten...
🧠 KI analysiert Markt für neue Day Trading Möglichkeiten...
🎯 Swing Trading Signal: GOLD BUY (Konfidenz: 65%)
⏰ Schließe abgelaufenen Day-Trade: EURUSD (Ticket: 12345, Alter: 125 Min)
```

---

## ⚠️ Wichtige Hinweise

### Day Trading Risiken

1. **Höhere Frequenz = Höhere Gebühren**
   - Day Trading öffnet viele Positionen
   - Spreads und Kommissionen können sich summieren

2. **Time-Based Exit**
   - Positionen werden nach 2h automatisch geschlossen
   - Kann zu Verlusten führen, wenn der Markt sich noch nicht bewegt hat

3. **Geringere Confidence = Mehr False Positives**
   - 40% Schwelle bedeutet mehr Trades, aber niedrigere Trefferquote

### Empfehlungen

- **Start:** Beginnen Sie nur mit Swing Trading
- **Testing:** Aktivieren Sie Day Trading mit kleinen Beträgen
- **Monitoring:** Überwachen Sie die Performance beider Strategien
- **Balance:** Passen Sie die Balance-Limits nach Bedarf an

---

## 🛠️ Fehlerbehebung

### Problem: Day Trading öffnet keine Positionen

**Lösungen:**
1. Prüfen Sie: `day_trading_enabled: true`
2. Prüfen Sie: Balance-Limit nicht erreicht
3. Prüfen Sie: Backend-Logs für Fehler
4. Reduzieren Sie `day_min_confidence_score` auf 0.3 für mehr Signale

### Problem: Zu viele Day-Trades

**Lösungen:**
1. Erhöhen Sie `day_min_confidence_score` auf 0.5
2. Reduzieren Sie `day_max_positions`
3. Verringern Sie `day_max_balance_percent`

---

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfen Sie die Backend-Logs
2. Testen Sie mit einem kleinen Balance-Limit
3. Kontaktieren Sie den Support mit Log-Auszügen

---

**Version:** 1.0  
**Datum:** 18. November 2025  
**Status:** ✅ Implementiert und funktionsfähig
