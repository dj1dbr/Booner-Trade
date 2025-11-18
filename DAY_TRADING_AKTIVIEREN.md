# 🚀 Day Trading Aktivieren - Anleitung

## Aktueller Status
- **Swing Trading:** ✅ AKTIV (Standard)
- **Day Trading:** ❌ DEAKTIVIERT (muss aktiviert werden)

---

## Methode 1: Via API Call (EMPFOHLEN)

### Day Trading einschalten:

```bash
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "day_trading_enabled": true,
    "swing_trading_enabled": true
  }'
```

### Day Trading ausschalten:

```bash
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "day_trading_enabled": false
  }'
```

### Status prüfen:

```bash
curl -s http://localhost:8001/api/settings | grep -E "trading_enabled"
```

Sollte zeigen:
```
"swing_trading_enabled": true,
"day_trading_enabled": true,
```

---

## Methode 2: Via MongoDB direkt

### Mit mongo Shell:

```javascript
use test_database

// Day Trading aktivieren
db.trading_settings.updateOne(
  { id: "trading_settings" },
  { 
    $set: {
      day_trading_enabled: true
    }
  }
)

// Status prüfen
db.trading_settings.findOne(
  { id: "trading_settings" },
  { 
    swing_trading_enabled: 1, 
    day_trading_enabled: 1 
  }
)
```

### Mit Python:

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client['test_database']

# Day Trading aktivieren
await db.trading_settings.update_one(
    {"id": "trading_settings"},
    {"$set": {"day_trading_enabled": True}}
)
```

---

## Methode 3: Settings komplett anpassen

Alle Day-Trading-Parameter auf einmal setzen:

```bash
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "day_trading_enabled": true,
    "day_min_confidence_score": 0.35,
    "day_stop_loss_percent": 0.3,
    "day_take_profit_percent": 0.6,
    "day_max_positions": 15,
    "day_max_balance_percent": 25.0
  }'
```

**Hinweis:** Diese Werte sind aggressiver als die Defaults!

---

## Überprüfung ob Day Trading läuft

### 1. Backend-Logs prüfen:

```bash
tail -f /var/log/supervisor/backend.err.log | grep -E "Day Trading"
```

**Erwartete Ausgabe wenn aktiv:**
```
🧠 KI analysiert Markt für neue Day Trading Möglichkeiten...
🎯 Day Trading Signal: EURUSD BUY (Konfidenz: 45%)
⏰ Schließe abgelaufenen Day-Trade: GOLD (Ticket: 12345)
```

### 2. Via API prüfen:

```bash
curl -s http://localhost:8001/api/settings | python3 -m json.tool | grep -A 15 "day_trading"
```

### 3. Aktive Positionen nach Strategie filtern:

```bash
curl -s http://localhost:8001/api/trades/list | python3 -m json.tool | grep "strategy"
```

Sollte zeigen:
- `"strategy": "swing"` - Swing Trading Positionen
- `"strategy": "day"` - Day Trading Positionen

---

## SCHNELL-AKTIVIERUNG (Copy & Paste)

```bash
# Day Trading einschalten
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{"day_trading_enabled": true}'

# Warte 5 Sekunden
sleep 5

# Prüfen ob aktiv
echo "=== Settings Check ==="
curl -s http://localhost:8001/api/settings | grep "day_trading_enabled"

echo ""
echo "=== Backend Logs (letzte 20 Zeilen) ==="
tail -n 20 /var/log/supervisor/backend.err.log | grep -E "Day Trading|Swing Trading"
```

---

## Erwartetes Verhalten nach Aktivierung

### Sofort (innerhalb 10 Sekunden):
- Backend-Logs zeigen: `🧠 KI analysiert Markt für neue Day Trading Möglichkeiten...`
- Bot analysiert JEDE MINUTE statt alle 10 Minuten
- Niedrigere Confidence-Schwelle (40% statt 60%)

### Nach einigen Minuten:
- Erste Day-Trades könnten eröffnet werden (wenn Signale stark genug)
- Max. 10 Day-Trades gleichzeitig möglich
- Nutzt maximal 20% der Balance

### Nach 2 Stunden:
- Alte Day-Trades werden automatisch geschlossen (Time-Based Exit)
- Log: `⏰ Schließe abgelaufenen Day-Trade`

---

## Troubleshooting

### Problem: Day Trading wird nicht aktiv

**Lösung 1:** Backend neu starten
```bash
sudo supervisorctl restart backend
sleep 5
tail -n 50 /var/log/supervisor/backend.err.log | grep "Day Trading"
```

**Lösung 2:** Settings komplett neu laden
```bash
curl -X POST http://localhost:8001/api/settings/reset
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{"day_trading_enabled": true, "auto_trading": true}'
```

### Problem: Zu viele Day-Trades

**Lösung:** Confidence erhöhen oder Max-Positionen reduzieren
```bash
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "day_min_confidence_score": 0.5,
    "day_max_positions": 5
  }'
```

### Problem: Keine Day-Trades werden eröffnet

**Mögliche Ursachen:**
1. Balance-Limit erreicht (20% bereits genutzt)
2. Keine Signale mit 40%+ Confidence
3. Auto-Trading deaktiviert

**Lösung:**
```bash
# Auto-Trading prüfen
curl -s http://localhost:8001/api/settings | grep "auto_trading"

# Falls false, aktivieren:
curl -X POST http://localhost:8001/api/settings \
  -H "Content-Type: application/json" \
  -d '{"auto_trading": true, "day_trading_enabled": true}'
```

---

## Zusammenfassung

✅ **Day Trading ist IMPLEMENTIERT** aber standardmäßig deaktiviert
✅ **Aktivierung:** Einfach `day_trading_enabled: true` setzen
✅ **Logs checken:** `tail -f /var/log/supervisor/backend.err.log | grep Day`
✅ **Frontend:** UI für Day Trading wird im Dashboard hinzugefügt (TODO)

**Empfehlung:** Starten Sie mit Day Trading aktiviert aber konservativen Parametern, beobachten Sie 1-2 Stunden, dann anpassen!
