# 📊 BOONER-TRADE TRADING-STRATEGIEN DOKUMENTATION

> **Vollständige Erklärung aller Indikatoren, Strategien und wie sie zusammenwirken**

---

## 📑 INHALTSVERZEICHNIS

1. [Übersicht der Dual-Trading-Strategie](#übersicht)
2. [Technische Indikatoren erklärt](#technische-indikatoren)
3. [Externe Datenquellen](#externe-datenquellen)
4. [Signal-Generierung & Gewichtung](#signal-generierung)
5. [Risk Management](#risk-management)
6. [Praktische Beispiele](#praktische-beispiele)

---

## 🎯 ÜBERSICHT DER DUAL-TRADING-STRATEGIE {#übersicht}

Booner-Trade nutzt **ZWEI parallel laufende Trading-Strategien**:

### 1. **SWING TRADING** (Langfristig)
- **Zeitrahmen**: Tage bis Wochen
- **Ziel**: Große Trends erfassen
- **Max Positionen**: 5-8 gleichzeitig
- **Risk pro Trade**: 2% des Kapitals
- **Min. Konfidenz**: 60%
- **Analyse-Intervall**: 60 Sekunden

### 2. **DAY TRADING** (Kurzfristig)
- **Zeitrahmen**: Minuten bis Stunden
- **Ziel**: Schnelle Intraday-Bewegungen nutzen
- **Max Positionen**: 10-15 gleichzeitig
- **Risk pro Trade**: 1% des Kapitals
- **Min. Konfidenz**: 40%
- **Analyse-Intervall**: 60 Sekunden

**WICHTIG**: Beide Strategien laufen gleichzeitig, aber mit unterschiedlichen Parametern!

---

## 📈 TECHNISCHE INDIKATOREN ERKLÄRT {#technische-indikatoren}

### 1. RSI (Relative Strength Index)

**Was ist das?**
Der RSI misst die Geschwindigkeit und Stärke von Preisbewegungen auf einer Skala von 0-100.

**Wie wird er berechnet?**
```
RSI = 100 - (100 / (1 + (Durchschnitt Gewinne / Durchschnitt Verluste)))
```

**Interpretation:**
- **RSI > 70**: 🔴 **ÜBERKAUFT** → Verkaufs-Signal (Preis könnte fallen)
- **RSI 60-70**: 🟠 Leicht überkauft → Vorsicht bei Käufen
- **RSI 40-60**: 🟢 **NEUTRAL** → Kein klares Signal
- **RSI 30-40**: 🟡 Leicht überverkauft → Möglicher Einstieg
- **RSI < 30**: 🔵 **ÜBERVERKAUFT** → Kauf-Signal (Preis könnte steigen)

**Beispiel:**
```
GOLD RSI = 72
→ Interpretation: Überkauft! 
→ Empfehlung: Nicht kaufen, evtl. verkaufen
→ Signal-Score: -2.0 (starkes Verkaufssignal)
```

---

### 2. MACD (Moving Average Convergence Divergence)

**Was ist das?**
MACD zeigt die Beziehung zwischen zwei gleitenden Durchschnitten (EMA 12 und EMA 26).

**Komponenten:**
1. **MACD Linie**: EMA(12) - EMA(26)
2. **Signal Linie**: EMA(9) des MACD
3. **MACD Diff (Histogram)**: MACD - Signal Linie

**Interpretation:**
- **MACD Diff > 0**: 🟢 **BULLISH CROSSOVER** → Kaufsignal
  - MACD kreuzt Signal-Linie nach oben
  - Score: +1.5
- **MACD Diff < 0**: 🔴 **BEARISH CROSSOVER** → Verkaufssignal
  - MACD kreuzt Signal-Linie nach unten
  - Score: -1.5
- **MACD Diff = 0**: Neutral

**Beispiel:**
```
GOLD MACD = 16.51
GOLD MACD Signal = 16.88
GOLD MACD Diff = -0.37

→ Bearish Crossover (MACD unter Signal)
→ Score: -1.5 (Verkaufssignal)
```

---

### 3. SMA (Simple Moving Average) - Gleitender Durchschnitt

**Was ist das?**
Durchschnittspreis über die letzten X Tage (z.B. 20 oder 50 Tage).

**Berechnung:**
```
SMA(20) = (Preis Tag 1 + Preis Tag 2 + ... + Preis Tag 20) / 20
```

**Interpretation:**
- **Preis ÜBER SMA**: 🟢 Aufwärtstrend → Kaufsignal
- **Preis UNTER SMA**: 🔴 Abwärtstrend → Verkaufssignal
- **SMA 20 > SMA 50**: 🟢 **GOLDEN CROSS** → Starkes Kaufsignal (Score: +1.5)
- **SMA 20 < SMA 50**: 🔴 **DEATH CROSS** → Starkes Verkaufssignal (Score: -1.5)

**Beispiel:**
```
GOLD Preis = 4203.30
GOLD SMA 20 = 4180.75
GOLD SMA 50 = 4165.20

→ Preis > SMA 20 → Aufwärtstrend (+0.5)
→ SMA 20 > SMA 50 → Golden Cross (+1.5)
→ TOTAL: +2.0 (Starkes Kaufsignal)
```

---

### 4. EMA (Exponential Moving Average)

**Was ist das?**
Wie SMA, aber neuere Preise haben mehr Gewicht → reagiert schneller auf Änderungen.

**Verwendung:**
- **EMA 12 & EMA 26**: Basis für MACD-Berechnung
- **EMA 20**: Alternative zu SMA 20 für schnellere Signale

**Interpretation:** Gleich wie SMA

---

### 5. BOLLINGER BANDS (Volatilitätsbänder)

**Was ist das?**
Drei Linien: Mittelband (SMA 20) + Oberes Band + Unteres Band

**Berechnung:**
```
Mittelband = SMA(20)
Oberes Band = SMA(20) + (2 × Standardabweichung)
Unteres Band = SMA(20) - (2 × Standardabweichung)
```

**Interpretation:**
- **Preis ≤ Unteres Band**: 🔵 **ÜBERVERKAUFT** → Kaufsignal (Score: +1.5)
- **Preis ≥ Oberes Band**: 🔴 **ÜBERKAUFT** → Verkaufssignal (Score: -1.5)
- **Bänder werden enger**: Niedrige Volatilität → Breakout steht bevor
- **Bänder werden breiter**: Hohe Volatilität → Große Bewegung im Gange

**Beispiel:**
```
GOLD Preis = 4155.00
GOLD BB Lower = 4208.70
GOLD BB Middle = 4246.44
GOLD BB Upper = 4284.19

→ Preis unter unterem Band → Überverkauft!
→ Score: +1.5 (Kaufsignal)
```

---

### 6. ATR (Average True Range) - Volatilitätsmaß

**Was ist das?**
Misst die durchschnittliche Preisbewegung über 14 Perioden.

**Verwendung:**
- **Stop Loss Berechnung**: SL = Entry ± (ATR × Multiplikator)
- **Take Profit Berechnung**: TP = Entry ± (ATR × Multiplikator)

**Beispiel:**
```
GOLD Preis = 4200
GOLD ATR = 29.51

Swing Trading (ATR × 2.0 für SL, ATR × 3.0 für TP):
→ BUY Entry: 4200
→ Stop Loss: 4200 - (29.51 × 2.0) = 4140.98
→ Take Profit: 4200 + (29.51 × 3.0) = 4288.53

Day Trading (ATR × 1.0 für SL, ATR × 1.5 für TP):
→ BUY Entry: 4200
→ Stop Loss: 4200 - (29.51 × 1.0) = 4170.49
→ Take Profit: 4200 + (29.51 × 1.5) = 4244.27
```

**Höherer ATR = Höhere Volatilität = Größere SL/TP-Abstände**

---

### 7. STOCHASTIC OSCILLATOR (Momentum-Indikator)

**Was ist das?**
Vergleicht aktuellen Schlusskurs mit der Preisspanne über eine Periode (0-100).

**Komponenten:**
- **%K**: Schnelle Linie
- **%D**: Langsame Linie (Durchschnitt von %K)

**Interpretation:**
- **Stoch > 80**: 🔴 Überkauft → Verkaufssignal (Score: -1.0)
- **Stoch < 20**: 🔵 Überverkauft → Kaufsignal (Score: +1.0)
- **%K kreuzt %D nach oben**: 🟢 Kaufsignal
- **%K kreuzt %D nach unten**: 🔴 Verkaufssignal

---

## 🌐 EXTERNE DATENQUELLEN {#externe-datenquellen}

### 1. NEWS SENTIMENT (Google News RSS)

**Quelle:** Google News RSS (KOSTENLOS, keine API Keys!)

**Funktion:**
1. Sucht nach commodity-spezifischen News (z.B. "crude oil prices")
2. Analysiert Top 15 Artikel
3. Zählt Sentiment-Wörter

**Sentiment-Wörter:**

**BULLISH (Positiv) - Score: +1 pro Wort:**
- surge, rally, rise, gain, up, bullish, high, jump, climb, strong, boost, soar, higher
- demand, shortage, disruption, cut, opec

**BEARISH (Negativ) - Score: -1 pro Wort:**
- fall, drop, decline, loss, down, bearish, low, plunge, weak, crash, slump, tumble, lower
- glut, oversupply, surplus, recession

**EVENT-WÖRTER (Doppeltes Gewicht: ±2):**

**Bullish Events (für Rohstoffe):**
- explosion, attack, war, conflict, strike, hurricane, disaster, sanctions

**Bearish Events:**
- peace, deal, agreement, recovery, resolution

**Berechnung:**
```
Sentiment Score = (Positive Wörter - Negative Wörter) / Anzahl Artikel

Beispiel: 15 Artikel, 8 positive Wörter, 2 negative Wörter
→ Score = (8 - 2) / 15 = 0.40
→ Sentiment: BULLISH (Score > 0.3)
```

**Interpretation:**
- **Score > 0.3**: BULLISH → +1.0 zu Final Score
- **Score < -0.3**: BEARISH → -1.0 zu Final Score
- **-0.3 bis 0.3**: NEUTRAL → 0.0

---

### 2. ECONOMIC CALENDAR (Finnhub API)

**Was es macht:**
Holt wichtige Wirtschafts-Events (Fed-Meetings, Zinsentscheidungen, Arbeitslosenzahlen, etc.)

**Interpretation:**
- **High Impact Events > 0**: ⚠️ VORSICHT! → Reduziert Konfidenz um 10%
  - KI handelt konservativer
  - Vermeidet Trades kurz vor/nach Events
- **Keine Events**: Normale Trading-Bedingungen

**Beispiel:**
```
Heute: Fed Zinsentscheidung (High Impact)
→ Trading-Konfidenz wird von 70% auf 60% reduziert
→ Weniger aggressive Positionen
```

---

### 3. MARKET SENTIMENT (SPY RSI)

**Was es macht:**
Holt RSI des S&P 500 ETF (SPY) als allgemeine Marktstimmung.

**Interpretation:**
- **SPY RSI > 70**: Markt überkauft → Vorsicht (-0.5 Score)
- **SPY RSI < 30**: Markt überverkauft → Kaufchance (+0.5 Score)
- **SPY RSI 30-70**: Neutral (0.0)

**Logik:**
Rohstoffe korrelieren oft mit dem Gesamtmarkt. Wenn S&P 500 überkauft ist, könnte eine Korrektur auch Rohstoffe betreffen.

---

### 4. SUPPORT & RESISTANCE LEVELS

**Was ist das?**
Preisniveaus, an denen historisch viele Käufe/Verkäufe stattfanden.

**Berechnung:**
```
Support = Niedrigster Preis der letzten 20 Perioden
Resistance = Höchster Preis der letzten 20 Perioden
```

**Interpretation:**
- **Preis nahe Support**: 🟢 Kaufgelegenheit (Score: +0.5)
- **Preis nahe Resistance**: 🔴 Verkaufsgelegenheit (Score: -0.5)
- **Preis zwischen Support & Resistance**: Neutral

**Beispiel:**
```
GOLD Support = 4100
GOLD Resistance = 4300
GOLD Preis = 4120

→ Preis nahe Support → Kaufsignal (+0.5)
```

---

## 🎯 SIGNAL-GENERIERUNG & GEWICHTUNG {#signal-generierung}

### WIE ALLE SIGNALE KOMBINIERT WERDEN

Die KI sammelt ALLE Signale und berechnet einen **Total Score**:

```
SIGNAL-KOMPONENTEN:

1. RSI Signal                    (-2.0 bis +2.0)
2. MACD Signal                   (-1.5 bis +1.5)
3. Moving Average Signal         (-1.5 bis +1.5)
4. Bollinger Bands Signal        (-1.5 bis +1.5)
5. Stochastic Signal             (-1.0 bis +1.0)
6. News Sentiment                (-1.0 bis +1.0)
7. Economic Events               (-0.5 bis 0.0) [nur negativ]
8. Market Sentiment (SPY)        (-0.5 bis +0.5)
9. Support/Resistance            (-0.5 bis +0.5)

MAXIMUM POSSIBLE SCORE: +9.5 (extrem bullish)
MINIMUM POSSIBLE SCORE: -11.0 (extrem bearish)
```

### KONFIDENZ-BERECHNUNG

```python
Total Score = Summe aller Signal-Scores

# Normalisiere zu 0-100%
if Total Score > 0:
    Confidence = min(100, (Total Score / 9.5) * 100)
else:
    Confidence = 0

# Nur bei hoher Konfidenz handeln
if Confidence >= Min Konfidenz UND Signal in ['BUY', 'SELL']:
    → Trade ausführen
else:
    → HOLD (kein Trade)
```

### PRAKTISCHES BEISPIEL

**GOLD ANALYSE:**

```
1. RSI = 45 (leicht überverkauft)        → +1.0
2. MACD Diff = +0.18 (Bullish Crossover) → +1.5
3. Preis > SMA 20                        → +0.5
4. SMA 20 > SMA 50 (Golden Cross)        → +1.5
5. Preis nahe BB Lower                   → +1.5
6. Stochastic = 55 (neutral)             → 0.0
7. News Sentiment = BULLISH              → +1.0
8. Economic Events = 0 (keine Events)    → 0.0
9. SPY RSI = 52 (neutral)                → 0.0
10. Preis nahe Support                   → +0.5

TOTAL SCORE = +7.5
CONFIDENCE = (7.5 / 9.5) × 100 = 78.9%

→ SIGNAL: BUY
→ CONFIDENCE: 79%
→ ENTSCHEIDUNG: ✅ TRADE AUSFÜHREN (über 60% Min-Konfidenz)
```

---

## 💰 RISK MANAGEMENT {#risk-management}

### POSITIONSGRÖSSE

**Formel:**
```
Risk Amount = Balance × (Risk Percent / 100)
Position Size = Risk Amount / (SL Distance × 100)

Beispiel (Swing Trading):
Balance = 10,000 EUR
Risk per Trade = 2%
Risk Amount = 10,000 × 0.02 = 200 EUR

Entry = 4200
Stop Loss = 4140 (ATR × 2.0)
SL Distance = 60

Position Size = 200 / (60 × 100) = 0.03 Lots
→ Konservativ: 0.01 Lots (Minimum)
```

### STOP LOSS & TAKE PROFIT

**Swing Trading:**
- **SL**: Entry ± (ATR × 2.0)
- **TP**: Entry ± (ATR × 3.0)
- **Risk:Reward Ratio**: 1:1.5

**Day Trading:**
- **SL**: Entry ± (ATR × 1.0)
- **TP**: Entry ± (ATR × 1.5)
- **Risk:Reward Ratio**: 1:1.5

**WICHTIG:** SL/TP werden NUR in der App gespeichert, NICHT auf MT5!
Die KI überwacht Positionen und schließt sie manuell bei Erreichen der Ziele.

### MAX POSITIONEN & BALANCE-LIMITS

**Pro Plattform (MT5 Libertex oder ICMarkets):**
- **Max Balance-Nutzung**: 20% für BEIDE Strategien zusammen
- **Swing Max Positions**: 5-8
- **Day Max Positions**: 10-15

**Beispiel:**
```
MT5 Libertex Balance: 50,000 EUR
Max Nutzung: 50,000 × 0.20 = 10,000 EUR

Swing Trades: 5 × 0.01 Lots à ~100 EUR = 500 EUR
Day Trades: 10 × 0.01 Lots à ~100 EUR = 1,000 EUR
TOTAL: 1,500 EUR (unter 10,000 EUR Limit) ✅
```

---

## 📝 PRAKTISCHE BEISPIELE {#praktische-beispiele}

### BEISPIEL 1: GOLD KAUFSIGNAL

**Szenario:** Gold in Aufwärtstrend, News über Banken-Krise

**Technische Signale:**
```
RSI = 42 (leicht überverkauft)           → +1.0
MACD Diff = +0.25 (Bullish)              → +1.5
Preis = 4205, SMA 20 = 4180 (darüber)    → +0.5
SMA 20 > SMA 50 (Golden Cross)           → +1.5
BB Lower = 4190, Preis nahe Band         → +1.5
Stochastic = 45 (neutral)                → 0.0
```

**Externe Signale:**
```
News: "Gold surges on banking crisis fears" → BULLISH (+1.0)
Economic Events: Keine High-Impact Events   → 0.0
SPY RSI = 48 (neutral)                      → 0.0
Support = 4100, Preis weit entfernt         → 0.0
```

**ERGEBNIS:**
```
TOTAL SCORE = +7.0
CONFIDENCE = 73%

→ SIGNAL: BUY GOLD
→ STRATEGIE: Swing Trading (langfristig)
→ ENTRY: 4205
→ SL: 4205 - (ATR 30 × 2.0) = 4145
→ TP: 4205 + (ATR 30 × 3.0) = 4295
→ POSITION SIZE: 0.01 Lots
```

---

### BEISPIEL 2: ÖL VERKAUFSSIGNAL

**Szenario:** Öl in Abwärtstrend, OPEC erhöht Produktion

**Technische Signale:**
```
RSI = 68 (leicht überkauft)              → -1.0
MACD Diff = -0.15 (Bearish)              → -1.5
Preis = 58, SMA 20 = 60 (darunter)       → -0.5
SMA 20 < SMA 50 (Death Cross)            → -1.5
BB Upper = 62, Preis nahe Band           → -1.5
Stochastic = 78 (überkauft)              → -1.0
```

**Externe Signale:**
```
News: "OPEC+ announces production increase" → BEARISH (-1.0)
      "oil prices drop on oversupply fears"
Economic Events: Keine                        → 0.0
SPY RSI = 72 (überkauft)                      → -0.5
Resistance = 62, Preis nahe Level             → -0.5
```

**ERGEBNIS:**
```
TOTAL SCORE = -9.0
CONFIDENCE = 82% (invertiert für SELL)

→ SIGNAL: SELL OIL
→ STRATEGIE: Day Trading (kurzfristig)
→ ENTRY: 58.00
→ SL: 58.00 + (ATR 2.0 × 1.0) = 60.00
→ TP: 58.00 - (ATR 2.0 × 1.5) = 55.00
→ POSITION SIZE: 0.01 Lots
```

---

### BEISPIEL 3: HOLD SIGNAL (Kein Trade)

**Szenario:** Gold ohne klaren Trend, gemischte Signale

**Signale:**
```
RSI = 52 (neutral)                       → 0.0
MACD Diff = -0.02 (fast neutral)         → -1.5
Preis nahe SMA 20                        → 0.0
BB Middle, zwischen Bändern              → 0.0
Stochastic = 55                          → 0.0
News: neutral                            → 0.0
Economic Events: Fed Meeting heute!      → -0.5
```

**ERGEBNIS:**
```
TOTAL SCORE = -2.0
CONFIDENCE = 21%

→ SIGNAL: HOLD (unter 60% Min-Konfidenz)
→ KEIN TRADE
→ Grund: Gemischte Signale, zu niedrige Konfidenz
```

---

## 🔄 MONITORING & AUTO-CLOSE

### WIE DER AI BOT POSITIONEN ÜBERWACHT

```
ALLE 30 SEKUNDEN:

1. Hole ALLE offenen Positionen von MT5
2. Für jeden Trade:
   - Hole SL/TP aus trade_settings DB
   - Vergleiche Current Price mit SL/TP
   - Wenn SL erreicht: ❌ CLOSE Trade (Loss)
   - Wenn TP erreicht: ✅ CLOSE Trade (Profit)
3. Logge alle Aktionen
4. Warte 30 Sekunden
5. Wiederhole
```

### AUTO-TP/SL FÜR NEUE TRADES

```
BEIM TRADE-OPENING:

1. Trade wird an MT5 OHNE SL/TP gesendet
2. App berechnet SL/TP basierend auf ATR
3. SL/TP werden in trade_settings DB gespeichert
4. Monitor erkennt Trade und startet Überwachung

FALLBACK (falls Trade keine Settings hat):

1. Monitor erkennt fehlende Settings
2. Berechnet automatisch:
   - SL = Entry × (1 ± stop_loss_percent/100)
   - TP = Entry × (1 ± take_profit_percent/100)
3. Speichert in DB
4. Überwacht ab jetzt
```

---

## 📊 ZUSAMMENFASSUNG

### GEWICHTUNG ALLER FAKTOREN

```
TRADING ENTSCHEIDUNG = 

60% Technische Indikatoren
    - 20% RSI
    - 15% MACD
    - 15% Moving Averages
    - 10% Bollinger Bands
    - 5% Stochastic
    - 5% ATR (für SL/TP)

20% News Sentiment
    - Google News RSS
    - Event-Erkennung (2× Gewicht)

10% Economic Calendar
    - High-Impact Events → Vorsicht

10% Market Sentiment & Support/Resistance
    - SPY RSI
    - S/R Levels
```

### ENTSCHEIDUNGS-PROZESS

```
FÜR JEDEN COMMODITY (alle 60 Sekunden):

1. Hole Preishistorie (100 Datenpunkte)
2. Berechne ALLE technischen Indikatoren
3. Hole News von Google RSS
4. Hole Economic Calendar Events
5. Hole Market Sentiment (SPY)
6. Berechne Support/Resistance
7. Kombiniere alle Signale → Total Score
8. Berechne Konfidenz (0-100%)
9. WENN Konfidenz >= Min Konfidenz:
   → Führe Trade aus
   SONST:
   → HOLD
```

---

## ⚙️ EINSTELLUNGEN ANPASSEN

Sie können alle Parameter in den Settings anpassen:

**Swing Trading:**
- `swing_max_positions`: 5-10
- `swing_min_confidence_score`: 0.5-0.8 (50-80%)
- `swing_risk_per_trade_percent`: 1-5%
- `swing_atr_multiplier_sl`: 1.5-3.0
- `swing_atr_multiplier_tp`: 2.0-4.0

**Day Trading:**
- `day_max_positions`: 10-20
- `day_min_confidence_score`: 0.3-0.6 (30-60%)
- `day_risk_per_trade_percent`: 0.5-2%
- `day_atr_multiplier_sl`: 0.5-1.5
- `day_atr_multiplier_tp`: 1.0-2.5

**Allgemein:**
- `take_profit_percent`: 2-10% (für manuelle Trades)
- `stop_loss_percent`: 1-5% (für manuelle Trades)
- `combined_max_balance_percent_per_platform`: 10-30%

---

## 🎓 GLOSSAR

- **ATR**: Average True Range - Volatilitätsmaß
- **BB**: Bollinger Bands - Volatilitätsbänder
- **EMA**: Exponential Moving Average - Exponentieller gleitender Durchschnitt
- **MACD**: Moving Average Convergence Divergence - Momentum-Indikator
- **RSI**: Relative Strength Index - Momentum-Oszillator
- **SL**: Stop Loss - Verlustbegrenzung
- **SMA**: Simple Moving Average - Einfacher gleitender Durchschnitt
- **S/R**: Support/Resistance - Unterstützung/Widerstand
- **TP**: Take Profit - Gewinnmitnahme
- **Pip**: Smallest price move (0.0001 für meiste Paare)
- **Lot**: Handelseinheit (0.01 = Mini-Lot = 1,000 Einheiten)

---

## 📞 SUPPORT

Bei Fragen zur Trading-Strategie:
- Überprüfen Sie die Logs: `/var/log/supervisor/backend.err.log`
- Schauen Sie sich die Signal-Generierung in `market_analysis.py` an
- Passen Sie Settings in der App an

**WICHTIG:** Dies ist keine Finanzberatung. Trading birgt Risiken. Nutzen Sie Demo-Accounts zum Testen!

---

*Letzte Aktualisierung: November 2025*
*Version: 1.0*
