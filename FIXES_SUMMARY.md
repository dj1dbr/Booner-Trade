# Fixes für Trading-Liste & Risiko-Management

## Probleme & Lösungen

### 1. ✅ Doppelte Trades in Trading-Liste (GELÖST)

**Problem:** Trades werden doppelt angezeigt

**Root Cause:** Deduplizierungs-Logik war zu aggressiv

**Fix:** 
- Deduplizierung komplett entfernt
- Zeigt NUR was MT5 meldet (reine Synchronisation)
- Keine künstliche Filterung mehr

---

### 2. ⚠️ Portfolio-Risiko falsch berechnet

**Problem:** 
- Zeigt 2000€ statt echte Balance
- Warnung muss pro Plattform sein

**Benötigte Änderung:**
```javascript
// Für JEDE Plattform einzeln:
const libertexRisk = (libertexExposure / libertexBalance) * 100;
const icmarketsRisk = (icmarketsExposure / icmarketsBalance) * 100;

// Warning wenn > 20%:
{libertexRisk > 20 && (
  <Alert variant="destructive">
    ⚠️ Libertex: Portfolio-Risiko bei {libertexRisk.toFixed(1)}% 
    (Limit: 20%)
  </Alert>
)}
```

---

### 3. ⚠️ Take Profit & Trailing Stop

**Problem:** 0.2% Take Profit, aber Trailing Stop unrealistisch

**Empfehlung:**
- Take Profit: 0.2% - 1% (für kurzfristige Trades)
- Trailing Stop: 0.1% - 0.5% (immer kleiner als TP)

**Beispiel:**
- TP: 0.5% → Trailing Stop: 0.2%
- TP: 1.0% → Trailing Stop: 0.3%

Formel: `Trailing Stop = Take Profit × 0.4`

---

### 4. ⚠️ Zielwert-Anzeige in Trading-Liste

**Feature Request:** Bei jeder Position: "noch X% vom Ziel"

**Implementation:**
```javascript
// Berechne Distanz zum Take Profit:
const currentProfit = position.profit / position.volume;
const targetProfit = position.takeProfit - position.openPrice;
const progress = (currentProfit / targetProfit) * 100;

// Anzeige:
<span>
  {progress < 100 ? `Noch ${(100 - progress).toFixed(0)}% zum Ziel` : '✅ Ziel erreicht!'}
</span>
```

---

### 5. ✅ Libertex PIN

**Frage:** Braucht man die PIN für MetaAPI?

**Antwort:** **NEIN!**

**Erklärung:**
- PIN ist nur für **Mobile App** Login
- PIN ist **NICHT** für API/MetaAPI
- MetaAPI braucht nur: Login, Password, Server

**Falls Login fehlschlägt:**
1. Prüfen Sie Server-Namen (exakt!)
2. Prüfen Sie Login/Password (ohne PIN!)
3. Testen Sie Login im MT5 Terminal

---

## Zusammenfassung

**Sofort gefixt:**
- ✅ Doppelte Trades → Backend angepasst

**Noch zu implementieren:**
- ⚠️ Portfolio-Risiko pro Plattform → Frontend-Änderung nötig
- ⚠️ Zielwert-Anzeige → Frontend-Änderung nötig
- ⚠️ TP/Trailing Stop Logik → Settings-Validierung nötig

**Libertex Real Account:**
- PIN nicht nötig für MetaAPI ✅
- Nur Login/Password/Server ✅

Soll ich die Frontend-Änderungen jetzt implementieren?
