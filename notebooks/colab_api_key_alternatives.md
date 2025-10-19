# Alternative per configurare API Key su Colab

## Opzione nel Notebook

Aggiungi questa cella ALTERNATIVA alla cella 4 del notebook:

```python
"""
OPZIONE 1: Secrets di Colab (RACCOMANDATO - già nel notebook)
"""
from google.colab import userdata
import os

try:
    GEMINI_API_KEY = userdata.get('GEMINI_API_KEY')
    os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
    print("✓ API key caricata da Colab Secrets")
except Exception as e:
    print(f"⚠ Secrets non configurato: {e}")
    print("Configura GEMINI_API_KEY nei secrets di Colab (icona 🔑)")
```

```python
"""
OPZIONE 2: File .env su Google Drive
"""
import os
from pathlib import Path

# Path al file .env su Drive
env_path = os.path.join(PROJECT_PATH, '.env')

if os.path.exists(env_path):
    # Carica manualmente da .env
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

    # Verifica
    if os.getenv('GEMINI_API_KEY'):
        print("✓ API key caricata da .env su Drive")
        # Mostra key mascherata
        key = os.getenv('GEMINI_API_KEY')
        print(f"  Key: {key[:10]}...{key[-4:]}")
    else:
        print("⚠ GEMINI_API_KEY non trovata in .env")
else:
    print(f"⚠ File .env non trovato in {env_path}")
    print("Carica un file .env nella root del progetto su Drive")
```

```python
"""
OPZIONE 3: Con python-dotenv (più pulito)
"""
# Prima installa
!pip install -q python-dotenv

from dotenv import load_dotenv
import os

# Carica .env
env_path = os.path.join(PROJECT_PATH, '.env')
if load_dotenv(env_path):
    print("✓ API key caricata con python-dotenv")
    # Verifica senza esporre
    if os.getenv('GEMINI_API_KEY'):
        key = os.getenv('GEMINI_API_KEY')
        print(f"  Key: {key[:10]}...{key[-4:]}")
else:
    print(f"⚠ Impossibile caricare .env da {env_path}")
```

## Confronto Metodi

| Metodo | Sicurezza | Facilità | Riutilizzo | Consigliato |
|--------|-----------|----------|------------|-------------|
| Colab Secrets | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ SI |
| .env su Drive | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ SI |
| python-dotenv | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ SI |
| Hardcoded | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ❌ NO |

## Esempio di file .env

Crea questo file nella root del progetto su Drive:

```bash
# .env
# API Keys per ReWTS-LLM-RL

# Google Gemini (obbligatorio)
GEMINI_API_KEY=AIzaSyC_your_actual_key_here

# Altre API (opzionali)
# OPENAI_API_KEY=sk-your_key_here
# ALPACA_API_KEY=your_alpaca_key
# ALPACA_SECRET_KEY=your_alpaca_secret
```

## Workflow Consigliato

### Per uso personale:
**→ Usa Colab Secrets** (più veloce, built-in)

### Per team/condivisione:
**→ Usa .env su Drive** (ogni membro ha il suo .env)

### Per produzione:
**→ Usa python-dotenv + CI/CD secrets**
