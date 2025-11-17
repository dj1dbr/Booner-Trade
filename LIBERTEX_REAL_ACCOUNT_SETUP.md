# 💰 Libertex Real Account einrichten

## Problem

Der Libertex Real Account kann nicht automatisch zu MetaAPI hinzugefügt werden.

**Fehler:** "We were not able to retrieve server settings using credentials provided"

**Grund:** MetaAPI kann die Server-Verbindung nicht automatisch verifizieren.

---

## ✅ Lösung: Manuelles Hinzufügen

### Schritt 1: Server-Namen prüfen

Öffnen Sie Ihr **MT5-Terminal** (auf Ihrem Computer oder App) und prüfen Sie:

1. Login drücken oder zu Account-Einstellungen gehen
2. Notieren Sie den **EXAKTEN** Server-Namen

**Beispiele:**
- ❌ `LibertexCom-MT5 Real Server` (falsch - hat Leerzeichen)
- ✅ `LibertexCom-MT5Real` (richtig)
- ✅ `Libertex-Real` (richtig)
- ✅ `LibertexCom-Real22` (richtig - mit Server-Nummer)

Der Server-Name ist **case-sensitive** und darf **keine Leerzeichen** haben!

---

### Schritt 2: Bei MetaAPI manuell hinzufügen

1. **Öffnen Sie:** https://app.metaapi.cloud/accounts

2. **Login mit Ihrem MetaAPI Account** (gleicher wie die Trading-App)

3. **Klicken Sie auf:** "Add Account" oder "+ New Account"

4. **Füllen Sie das Formular aus:**
   
   ```
   Name: Libertex Real Account
   Platform: MT5
   Type: Cloud
   
   Login: 560031700
   Password: uIYTxb1{
   Server: [EXAKTER Server-Name aus MT5]
   ```

5. **Klicken Sie:** "Add Account" oder "Create"

6. **Warten Sie:** MetaAPI versucht, die Verbindung herzustellen (kann 1-2 Minuten dauern)

---

### Schritt 3: Account ID in App eintragen

Wenn der Account erfolgreich hinzugefügt wurde:

1. **Kopieren Sie die Account ID** (eine UUID wie `abc123...`)
   - Zu finden in der Account-Liste bei MetaAPI
   - Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

2. **Öffnen Sie:** `/app/backend/.env`

3. **Fügen Sie hinzu:**
   ```bash
   METAAPI_LIBERTEX_REAL_ACCOUNT_ID=<Ihre-UUID-hier>
   ```

4. **Backend neu starten:**
   ```bash
   sudo supervisorctl restart backend
   ```

5. **Fertig!** Der Real Account erscheint jetzt in der App! 💰

---

## 🔧 Troubleshooting

### Problem: "Invalid credentials"

**Ursache:** Login/Password/Server stimmen nicht

**Lösung:**
1. Prüfen Sie die Zugangsdaten in Ihrem MT5-Terminal
2. Testen Sie, ob Sie sich mit diesen Daten im MT5 einloggen können
3. Achten Sie auf Groß-/Kleinschreibung

---

### Problem: "Server not found"

**Ursache:** Server-Name ist falsch

**Häufige Fehler:**
- ❌ `LibertexCom-MT5 Real Server` (zu viele Leerzeichen)
- ❌ `LibertexCom-MT5RealServer` (kein Bindestrich)
- ❌ `libertexcom-mt5real` (Kleinschreibung)

**Lösung:**
1. Öffnen Sie MT5
2. Gehen Sie zu "Tools" → "Options" → "Server"
3. Kopieren Sie den Server-Namen **EXAKT**

---

### Problem: "Connection timeout"

**Ursache:** MetaAPI kann den Server nicht erreichen

**Mögliche Gründe:**
- Broker erlaubt keine API-Verbindungen
- Server ist offline
- Firewall blockiert

**Lösung:**
1. Kontaktieren Sie Libertex Support
2. Fragen Sie: "Ist MetaAPI-Integration möglich?"
3. Wenn nein: Real Account kann leider nicht über API gehandelt werden

---

## 📊 Alternative: Lokal handeln

Wenn MetaAPI nicht funktioniert, können Sie:

1. **MT5-Terminal auf Ihrem Computer** verwenden
2. **Trades manuell kopieren** von der App
3. **Nur Demo-Accounts** in der App verwenden (als Signale)

Die App funktioniert weiterhin perfekt mit den **2 Demo-Accounts**! ✅

---

## ✅ Nach erfolgreicher Einrichtung

Wenn der Real Account in der App erscheint:

### In den Einstellungen:

1. Öffnen Sie **⚙️ Einstellungen**
2. Sie sehen jetzt **3 Account-Cards**:
   - MT5 Libertex Demo ✅
   - MT5 ICMarkets Demo ✅
   - 💰 MT5 Libertex REAL 💰 ✅

3. **Wichtig:** 
   - Setzen Sie Häkchen bei den Accounts, die Sie nutzen möchten
   - Real Account = Echtes Geld! Vorsicht! ⚠️

### Trading:

- Alle aktivierten Accounts erhalten **gleichzeitig** Trades
- Wenn Real Account aktiv: **Echtes Geld wird verwendet!** 💰
- Sie können jederzeit in Settings zwischen Demo/Real wechseln

---

## ⚠️ WICHTIG: Real Account Trading

### Sicherheits-Checkliste:

- [ ] Account wurde erfolgreich zu MetaAPI hinzugefügt
- [ ] Verbindung wurde getestet (grüner Status)
- [ ] Sie verstehen die Risiken von Echtgeld-Trading
- [ ] Stop-Loss-Einstellungen sind konfiguriert
- [ ] Portfolio-Risk ist unter 20% eingestellt
- [ ] Sie haben die Demo-Accounts ausgiebig getestet

### Empfehlung:

1. **Testen Sie ZUERST ausgiebig mit Demo-Accounts** 
2. **Starten Sie mit KLEINEN Positionen** im Real Account
3. **Überwachen Sie die ersten Trades genau**
4. **Erhöhen Sie schrittweise das Volumen**

---

## 📞 Support

**MetaAPI Support:**
- Website: https://metaapi.cloud/docs
- Email: support@metaapi.cloud

**Libertex Support:**
- Website: https://libertex.com/support

**Trading-App:**
- Logs: `/var/log/supervisor/backend.err.log`
- Settings: `/app/backend/.env`

---

## 🎯 Zusammenfassung

**Was funktioniert:**
✅ 2 Demo-Accounts (Libertex, ICMarkets)
✅ Alle Trading-Features
✅ KI-Analysen
✅ Charts & Indikatoren

**Was für Real Account nötig ist:**
1. Manuelles Hinzufügen bei MetaAPI
2. Exakter Server-Name
3. Gültige API-Verbindung vom Broker

**Status:** 
- Demo-Accounts: **100% funktionsfähig** ✅
- Real Account: **Manuelle Einrichtung erforderlich** ⚠️

---

**Viel Erfolg beim Trading! 📈💰**
