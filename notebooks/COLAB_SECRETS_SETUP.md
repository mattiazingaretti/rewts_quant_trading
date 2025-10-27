# Google Colab Secrets - Setup Guide

Guida rapida per configurare le API keys come secrets in Google Colab.

---

## 🔑 Perché Usare Colab Secrets?

**Vantaggi**:
- ✅ **Più sicuro**: API keys non visibili nel codice
- ✅ **Più comodo**: Non devi inserirle ogni volta
- ✅ **Persistente**: Salvate nel tuo account Colab
- ✅ **Condivisibile**: Puoi condividere il notebook senza esporre keys

**vs Environment Variables**:
- Environment variables: Devi inserirle ad ogni sessione
- Secrets: Configurati una volta, disponibili sempre

**vs Getpass**:
- Getpass: Devi inserire manualmente ogni volta
- Secrets: Automatico dopo setup

---

## 📋 Setup Passo-Passo

### 1. Apri il Notebook su Colab

```
https://colab.research.google.com
→ Upload notebook (train_rewts_complete.ipynb o train_rewts_deepseek.ipynb)
```

### 2. Accedi alla Sezione Secrets

Nella **sidebar sinistra**, clicca sull'icona **🔑 Secrets** (chiave).

Oppure:
1. Clicca sull'icona **📁 Files** nella sidebar
2. In alto vedrai **🔑 Secrets**

### 3. Aggiungi Nuovo Secret

**Per Gemini**:
```
1. Click "+ Add new secret"
2. Name:  GEMINI_API_KEY
3. Value: AIzaSy... (la tua API key completa)
4. Toggle ON "Notebook access"
5. Click "OK"
```

**Per DeepSeek**:
```
1. Click "+ Add new secret"
2. Name:  DEEPSEEK_API_KEY
3. Value: sk-... (la tua API key completa)
4. Toggle ON "Notebook access"
5. Click "OK"
```

### 4. Verifica

Il secret dovrebbe apparire nella lista:

```
🔑 Secrets
  ├─ GEMINI_API_KEY    [Notebook access: ON]
  └─ DEEPSEEK_API_KEY  [Notebook access: ON]
```

### 5. Restart Runtime (Importante!)

```
Runtime → Restart runtime
```

Oppure: `Ctrl+M` poi `.`

### 6. Esegui il Notebook

Ora quando esegui la cella di API Configuration, vedrai:

```
✓ Using GEMINI_API_KEY from Colab Secrets
✓ API key configured!
```

**Nessun input manuale richiesto!** 🎉

---

## 🔄 Come Funziona nel Notebook

### Ordine di Priorità

I notebook provano 3 metodi in ordine:

```python
# 1. Colab Secrets (preferito su Colab)
try:
    from google.colab import userdata
    API_KEY = userdata.get('GEMINI_API_KEY')
    print("✓ Using from Colab Secrets")
except:
    pass

# 2. Environment Variables (locale)
if API_KEY is None:
    API_KEY = os.getenv('GEMINI_API_KEY')
    print("✓ Using from environment")

# 3. Manual Input (fallback)
if API_KEY is None:
    API_KEY = getpass('Enter API Key: ')
    print("✓ Entered manually")
```

### Output Previsto

**Con Secrets configurati**:
```
✓ Using GEMINI_API_KEY from Colab Secrets
✓ API key configured!
```

**Senza Secrets**:
```
ℹ️  Colab Secrets not configured: Secret GEMINI_API_KEY not found
   You can add secrets at: Runtime → Manage secrets → Add secret

Enter your Gemini API Key (input will be hidden)
Gemini API Key: ········
✓ API key entered manually
✓ API key configured!
```

---

## 🔧 Gestione Secrets

### Modificare un Secret

```
1. Click sul secret nella lista
2. Click "Edit"
3. Modifica il valore
4. Click "OK"
5. Restart runtime
```

### Eliminare un Secret

```
1. Click sul secret nella lista
2. Click "Delete"
3. Conferma
```

### Disabilitare per un Notebook

```
1. Click sul secret nella lista
2. Toggle OFF "Notebook access"
```

Il notebook userà il fallback (getpass).

---

## 📱 Screenshot Guida (Posizioni)

### 1. Sidebar Secrets
```
┌─────────────────┐
│ Files           │ ← Apri questa tab
│   📁 sample_data│
│   🔑 Secrets    │ ← Click qui
└─────────────────┘
```

### 2. Add Secret
```
┌──────────────────────────────┐
│ 🔑 Secrets                   │
│                              │
│ [+ Add new secret]           │ ← Click
└──────────────────────────────┘
```

### 3. Secret Form
```
┌──────────────────────────────┐
│ Add a new secret             │
│                              │
│ Name:  GEMINI_API_KEY        │ ← Inserisci nome
│ Value: AIzaSy...             │ ← Inserisci key
│                              │
│ ☑ Notebook access            │ ← Toggle ON
│                              │
│ [Cancel]  [OK]               │ ← Click OK
└──────────────────────────────┘
```

---

## 🧪 Test

### Verifica Manuale

Esegui in una cella:

```python
# Test Gemini
from google.colab import userdata
gemini_key = userdata.get('GEMINI_API_KEY')
print(f"✓ Gemini API Key: {gemini_key[:10]}...{gemini_key[-4:]}")
```

Output:
```
✓ Gemini API Key: AIzaSyCdEf...xyz9
```

### Test DeepSeek

```python
from google.colab import userdata
deepseek_key = userdata.get('DEEPSEEK_API_KEY')
print(f"✓ DeepSeek API Key: {deepseek_key[:10]}...{deepseek_key[-4:]}")
```

---

## ⚠️ Troubleshooting

### "Secret not found"

**Causa**: Secret non configurato o Notebook access disabilitato

**Soluzione**:
1. Verifica che il nome sia esatto: `GEMINI_API_KEY` (case-sensitive)
2. Verifica che "Notebook access" sia ON
3. Restart runtime

### "userdata has no attribute 'get'"

**Causa**: Non sei su Google Colab

**Soluzione**:
- Se locale: Usa environment variables
- Se Colab: Aggiorna google-colab package

### "Permission denied"

**Causa**: Notebook access non abilitato

**Soluzione**:
1. Click sul secret
2. Toggle ON "Notebook access"
3. Restart runtime

### API Key non funziona

**Causa**: Key invalida o scaduta

**Soluzione**:
1. Verifica key sul provider:
   - Gemini: https://makersuite.google.com/app/apikey
   - DeepSeek: https://platform.deepseek.com
2. Rigenera se necessario
3. Aggiorna secret in Colab

---

## 🔒 Sicurezza

### Best Practices

✅ **Fai**:
- Usa secrets per API keys
- Abilita "Notebook access" solo quando necessario
- Rigenera keys periodicamente
- Non condividere screenshots con keys visibili

❌ **Non fare**:
- Hardcode API keys nel codice
- Committi API keys in git
- Condividi notebooks con keys embedded
- Lasci keys in variabili globali

### Note di Sicurezza

- **Secrets sono privati**: Solo tu puoi vederli
- **Non in notebooks condivisi**: Quando condividi, secrets NON sono inclusi
- **Per utente**: Ogni utente deve configurare i propri secrets
- **Encrypted**: Google li cripta at-rest

---

## 📚 Risorse

- **Google Colab Docs**: https://colab.research.google.com/notebooks/secrets.ipynb
- **Gemini API**: https://makersuite.google.com/app/apikey
- **DeepSeek API**: https://platform.deepseek.com
- **Notebook Guide**: `NOTEBOOKS_GUIDE.md`

---

## 💡 Tips

1. **Setup una volta**: Secrets persistono tra sessioni
2. **Più notebooks**: Stesso secret funziona per tutti i tuoi notebooks
3. **Condivisione**: Quando condividi, altri devono configurare le loro keys
4. **Testing**: Testa sempre dopo setup con una chiamata API semplice
5. **Backup**: Salva keys in un password manager

---

**🎉 Setup completato! Ora i notebook possono usare le API keys automaticamente.**
