# Guida Sicura: Setup API Keys su Google Colab

## ⭐ Metodo 1: Secrets di Colab (RACCOMANDATO)

### Vantaggi
- ✅ Massima sicurezza
- ✅ Non appare nel codice
- ✅ Non salvato nel notebook
- ✅ Integrato in Colab

### Setup Passo-Passo

1. **Apri il notebook su Google Colab**

2. **Accedi ai Secrets**
   - Clicca sull'icona della chiave 🔑 nella sidebar sinistra
   - Oppure: `View > Show sidebar > Secrets`

3. **Aggiungi il Secret**
   - Clicca `+ Add a secret`
   - **Name**: `GEMINI_API_KEY`
   - **Value**: La tua API key di Google Gemini
   - **Notebook access**: Toggle su ON (importante!)

4. **Usa nel codice**
```python
from google.colab import userdata

# Leggi la API key
GEMINI_API_KEY = userdata.get('GEMINI_API_KEY')
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
```

### Ottieni la tua Gemini API Key
1. Vai su https://ai.google.dev/
2. Clicca "Get API Key"
3. Accedi con il tuo account Google
4. Crea un nuovo progetto (se necessario)
5. Copia la API key generata

---

## 🔐 Metodo 2: File .env su Google Drive

### Vantaggi
- ✅ Riutilizzabile tra notebook
- ✅ Può contenere multiple API keys
- ✅ Facile da aggiornare

### Setup Passo-Passo

1. **Crea file .env sul tuo computer**
```bash
# Crea il file .env nella root del progetto Papers
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

2. **Carica su Google Drive**
   - Vai su Google Drive
   - Naviga nella cartella `Papers/`
   - Carica il file `.env`

3. **IMPORTANTE: Imposta permessi**
   - Clic destro sul file `.env`
   - Share → Restricted (solo tu)
   - **NON condividere questo file con nessuno**

4. **Usa nel notebook Colab**
```python
# Monta Drive
from google.colab import drive
drive.mount('/content/drive')

# Carica variabili da .env
import os
from pathlib import Path

# Path al tuo .env su Drive
env_path = '/content/drive/MyDrive/Papers/.env'

# Carica le variabili
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    print("✓ API keys caricate da .env")
else:
    print("⚠ File .env non trovato")

# Verifica
print(f"API Key configurata: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
```

---

## 🔒 Metodo 3: Python-dotenv (Più Professionale)

### Setup

1. **Installa python-dotenv nel notebook**
```python
!pip install python-dotenv
```

2. **Carica il .env**
```python
from dotenv import load_dotenv
import os

# Carica .env da Drive
load_dotenv('/content/drive/MyDrive/Papers/.env')

# Usa le variabili
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
```

---

## ⚠️ Metodi da EVITARE

### ❌ MAI mettere API key direttamente nel codice
```python
# ❌ NON FARE COSÌ
GEMINI_API_KEY = "AIzaSyC_vostra_key_qui"  # INSICURO!
```

**Perché è pericoloso:**
- Visibile a chiunque veda il notebook
- Salvato nella cronologia Git
- Condiviso se condividi il notebook
- Potrebbe essere esposto pubblicamente

### ❌ MAI stampare API key negli output
```python
# ❌ NON FARE COSÌ
print(f"API Key: {GEMINI_API_KEY}")  # Visibile nell'output!
```

### ❌ MAI fare commit di .env su Git
```bash
# Assicurati che .env sia nel .gitignore
echo ".env" >> .gitignore
```

---

## 🎯 Best Practices

### 1. Rotazione delle Key
- Rigenera le API key periodicamente
- Revoca quelle vecchie

### 2. Monitora l'uso
- Controlla il dashboard di Google AI Studio
- Imposta limiti di rate/quota
- Ricevi alert per uso anomalo

### 3. Limita i permessi
- Usa API key con permessi minimi necessari
- Considera environment separati (dev/prod)

### 4. Non condividere mai
- Le API key sono personali
- Ogni sviluppatore deve avere la propria
- Non inviarle via email/chat

### 5. Gestisci multiple key
Se hai più API key, usa un file .env strutturato:
```bash
# .env
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
```

---

## 🔍 Verifica Sicurezza

### Checklist
- [ ] API key NON appare nel codice del notebook
- [ ] File .env è nel .gitignore
- [ ] Secrets di Colab configurato correttamente
- [ ] API key NON stampata negli output
- [ ] Permessi file .env su Drive: solo tu
- [ ] API key testata e funzionante

### Test di sicurezza nel notebook
```python
import os

# Verifica che la key sia caricata ma non esposta
api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    # Mostra solo i primi e ultimi caratteri
    masked = f"{api_key[:10]}...{api_key[-4:]}"
    print(f"✓ API Key configurata: {masked}")
else:
    print("⚠ API Key non trovata")
```

---

## 🆘 Cosa fare se la key viene compromessa

1. **Agisci immediatamente**
   - Vai su https://ai.google.dev/
   - Revoca la API key compromessa
   - Genera una nuova key

2. **Aggiorna ovunque**
   - Aggiorna Secrets in Colab
   - Aggiorna file .env
   - Aggiorna variabili d'ambiente locali

3. **Analizza l'uso**
   - Controlla il dashboard per uso anomalo
   - Verifica se ci sono stati addebiti imprevisti

4. **Previeni future esposizioni**
   - Rivedi i tuoi .gitignore
   - Controlla la cronologia Git
   - Migliora le tue pratiche di sicurezza

---

## 📚 Risorse Utili

- [Google AI Studio](https://ai.google.dev/)
- [Colab Secrets Documentation](https://colab.research.google.com/notebooks/secrets.ipynb)
- [Best Practices for API Keys](https://cloud.google.com/docs/authentication/api-keys)
