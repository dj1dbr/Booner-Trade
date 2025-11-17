# 🤖 Ollama Setup - Schritt für Schritt

## Problem: "Keine Verbindung zu Ollama"

Wenn Sie diese Meldung sehen, bedeutet das: **Ollama läuft nicht!**

---

## ✅ Lösung in 3 Schritten:

### Schritt 1: Ollama starten

Öffnen Sie ein Terminal und geben Sie ein:

```bash
ollama serve
```

**Lassen Sie dieses Terminal-Fenster OFFEN!** Ollama läuft jetzt im Hintergrund.

Sie sollten sehen:
```
time=... level=INFO source=... msg="Listening on 127.0.0.1:11434..."
```

---

### Schritt 2: Model herunterladen (falls noch nicht geschehen)

Öffnen Sie ein **ZWEITES** Terminal und geben Sie ein:

```bash
# Empfohlen: Llama 3 (4GB)
ollama pull llama3

# ODER andere Models:
ollama pull mistral      # 4GB
ollama pull phi          # 1.5GB (klein & schnell)
ollama pull codellama    # 7GB (für Code)
```

Prüfen Sie installierte Models:
```bash
ollama list
```

---

### Schritt 3: In App-Settings konfigurieren

1. Öffnen Sie die Trading-App
2. Klicken Sie auf **⚙️ Einstellungen**
3. Bei **"KI Provider"** wählen Sie: **Ollama (Lokal)**
4. Bei **"Ollama Model"** wählen Sie Ihr installiertes Model (z.B. `llama3`)
5. **"Einstellungen speichern"** klicken

---

## ✅ Testen

1. Gehen Sie zum **Chat-Tab**
2. Schreiben Sie eine Nachricht, z.B.: "Wie sieht Gold aus?"
3. Die KI sollte jetzt antworten! 🎉

---

## 🔧 Troubleshooting

### Problem: "Model nicht gefunden"

**Lösung:**
```bash
ollama pull llama3
```

Dann in App-Settings den richtigen Model-Namen eingeben (genau wie bei `ollama list` angezeigt).

---

### Problem: "Connection refused"

**Mögliche Ursachen:**

1. **Ollama läuft nicht**
   ```bash
   # Starten Sie Ollama:
   ollama serve
   ```

2. **Falscher Port**
   - Standard ist: `http://localhost:11434`
   - Prüfen Sie in App-Settings unter "Ollama Server URL"

3. **Ollama läuft auf anderem Port**
   ```bash
   # Prüfen Sie, auf welchem Port Ollama läuft:
   lsof -i :11434
   ```

---

### Problem: "Ollama antwortet sehr langsam"

**Ursachen:**
- Ihr Mac braucht mehr RAM/CPU
- Das Model ist zu groß

**Lösung:**
```bash
# Verwenden Sie ein kleineres Model:
ollama pull phi  # Nur 1.5GB, sehr schnell!
```

Dann in App-Settings auf `phi` umstellen.

---

## 📊 Verfügbare Models

| Model | Größe | Geschwindigkeit | Qualität |
|-------|-------|-----------------|----------|
| **phi** | 1.5GB | ⚡⚡⚡ Sehr schnell | ⭐⭐ Gut |
| **llama3** | 4GB | ⚡⚡ Schnell | ⭐⭐⭐⭐ Sehr gut |
| **mistral** | 4GB | ⚡⚡ Schnell | ⭐⭐⭐⭐ Sehr gut |
| **codellama** | 7GB | ⚡ Mittel | ⭐⭐⭐⭐⭐ Exzellent (Code) |
| **mixtral** | 26GB | 🐢 Langsam | ⭐⭐⭐⭐⭐ Top |

**Empfehlung für Trading-App:** `llama3` (bester Kompromiss)

---

## 🚀 Automatischer Start (optional)

Damit Ollama automatisch beim Mac-Start läuft:

```bash
# LaunchAgent erstellen
brew services start ollama
```

Dann läuft Ollama immer im Hintergrund! ✅

---

## 💡 Vorteile von Ollama

✅ **Kostenlos** - keine API-Kosten!
✅ **Privat** - Daten verlassen Ihren Mac nicht
✅ **Offline** - funktioniert ohne Internet
✅ **Schnell** - keine API-Latenz
✅ **Unbegrenzt** - keine Rate-Limits

---

## 🔄 Zwischen Cloud & Lokal wechseln

Sie können jederzeit zwischen verschiedenen KI-Providern wechseln:

1. **Ollama (Lokal)** - für Privatsphäre & kostenlos
2. **Emergent LLM Key** - für beste Ergebnisse (GPT-5, Claude)
3. **Eigene API Keys** - OpenAI, Gemini, Claude

Einfach in den Einstellungen umstellen! 🎯

---

**Fragen?** Siehe `/app/electron/README.md` für mehr Details.
