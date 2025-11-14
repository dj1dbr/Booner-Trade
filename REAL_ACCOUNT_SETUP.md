# 🔴 Libertex Real Account Setup - Anleitung

## ⚠️ WICHTIG: REAL MONEY ACCOUNT!

Dieser Account verwendet **echtes Geld**! Sei vorsichtig!

---

## Schritt 1: MetaAPI Account erstellen

### 1.1 Login bei MetaAPI
1. Gehe zu: **https://app.metaapi.cloud/**
2. Login:
   - **Email:** dj1dbr@yahoo.de
   - **Passwort:** Sina1234

### 1.2 Neuen Account hinzufügen
1. Klicke auf **"Add Account"** (oben rechts)
2. Wähle **"MetaTrader 5"**

### 1.3 Account-Details eintragen
Trage folgendes ein:

```
Name:           Libertex Real
Platform:       MetaTrader 5
Server:         LibertexCom-MT5 Real Server
Login:          560031700
Password:       uIYTxb1{
Region:         London (oder deine Region)
```

### 1.4 Account deployen
1. Klicke **"Deploy"**
2. Warte bis Status = **"Connected"** (grün, ca. 1-2 Minuten)
3. **Kopiere die Account-ID** (UUID Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - Findest du oben unter dem Account-Namen
   - Beispiel: `5cc9abd1-671a-447e-ab93-5abbfe0ed941`

---

## Schritt 2: Account-ID in die App eintragen

### Option A: Cloud-Version (Emergent)
**NICHT SELBST MACHEN!** Sage mir die Account-ID und ich trage sie ein.

### Option B: Lokale Mac-Version
Öffne die Datei:
```
~/mein_python_projekt/Rohstofftrader/Booner-Trade/backend/.env
```

Ersetze die Zeile:
```bash
METAAPI_LIBERTEX_REAL_ACCOUNT_ID=PLACEHOLDER_REAL_ACCOUNT_ID
```

Mit:
```bash
METAAPI_LIBERTEX_REAL_ACCOUNT_ID=DEINE_ECHTE_ACCOUNT_ID_HIER
```

**Speichern!**

---

## Schritt 3: Backend neu starten

### Cloud-Version:
**Passiert automatisch** nach dem Eintragen

### Mac-Version:
```bash
cd ~/mein_python_projekt/Rohstofftrader/Booner-Trade/backend
source ../venv/bin/activate

# Stoppe das Backend (Strg+C im laufenden Terminal)

# Starte neu
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

---

## Schritt 4: In der App verwenden

### Im Dashboard:
1. Öffne die App
2. Du siehst jetzt **3 Plattform-Karten**:
   - 🔵 **MT5 Libertex Demo** (Demo-Geld)
   - 🟣 **MT5 ICMarkets Demo** (Demo-Geld)
   - 🔴 **MT5 Libertex REAL** (ECHTES GELD!)

### In den Settings:
1. Klicke auf **"Einstellungen"**
2. Scrolle zu **"Standard-Plattform für neue Trades"**
3. Du kannst wählen zwischen:
   - 🌐 Alle Plattformen gleichzeitig
   - 🔵 MT5 Libertex Demo
   - 🟣 MT5 ICMarkets Demo
   - 🔴 MT5 Libertex REAL ⚠️

---

## ⚠️ SICHERHEITSHINWEISE:

### Trading mit Real Account:
- **Immer** in Settings prüfen, welche Plattform aktiv ist!
- **Nie** Auto-Trading mit Real Account aktivieren ohne Test!
- **Immer** erst auf Demo testen, dann auf Real!
- **Stop-Loss** IMMER setzen!

### Auto-Trading Warnung:
Ich habe Auto-Trading **deaktiviert**! 

Wenn du es aktivieren willst:
1. **NUR** auf Demo-Accounts testen!
2. **Klein** anfangen (0.01 Lots)
3. **Stop-Loss** setzen!
4. **Nie** mehr als 2% pro Trade riskieren!

---

## Schritt 5: Testen

### Sicherheitstest:
1. Wähle in Settings: **MT5 Libertex Demo**
2. Führe einen Test-Trade aus (Gold, 0.01 Lots)
3. Prüfe ob er auf **Demo** platziert wird (nicht Real!)
4. Trade schließen
5. **Erst dann** mit Real Account arbeiten!

---

## Pincode Info:

Der **Pincode: xXuItA8=** ist wahrscheinlich für:
- **Read-Only Zugriff** (nur Lesen, nicht Trading)
- **Investor-Passwort** (für Freunde/Familie zum Anschauen)
- **Nicht für Trading** benötigt

Wir verwenden das **Trading-Passwort: uIYTxb1{** für Orders.

---

## Troubleshooting:

### "Account not found" Fehler:
- Prüfe ob Account-ID korrekt ist
- Prüfe ob Account auf MetaAPI "Connected" ist (grün)
- Warte 2-3 Minuten nach Deploy

### Balance zeigt €0.00:
- Account braucht Zeit zum Verbinden (1-2 Minuten)
- Prüfe auf MetaAPI ob Status = "Connected"
- Backend neu starten

### "Unauthorized" Fehler:
- MetaAPI Token abgelaufen? (sehr selten)
- Account-Passwort falsch?
- Server-Name korrekt? "LibertexCom-MT5 Real Server"

---

## NEXT STEPS:

Wenn alles funktioniert:
1. ✅ Real Account connected
2. ✅ Balance wird angezeigt
3. ✅ Test-Trade auf Demo erfolgreich
4. **DANN:** Electron Desktop-App erstellen!

---

**Bei Problemen:** Sag mir die Account-ID und ich helfe dir!
