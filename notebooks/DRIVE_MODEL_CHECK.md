# Google Drive Model Check - Guide

Guida alla nuova funzionalità di verifica modelli su Google Drive.

---

## 🎯 Funzionalità

I notebook ora verificano se i modelli esistono già prima di trainare:

1. ✅ **Check locale**: `models/{ticker}_rewts_ensemble.pkl`
2. ✅ **Check Google Drive**: `/content/drive/MyDrive/rewts_models/{ticker}_rewts_ensemble.pkl`
3. ✅ **Skip automatico**: Se trovato in uno dei due posti
4. ✅ **Copy automatico**: Se trovato solo su Drive, copia in locale

---

## 📋 Scenari

### Scenario 1: Modello NON Esiste da Nessuna Parte

**Output**:
```
################################################################################
# [1/6] Processing AAPL
################################################################################

🎯 Model not found (local or Drive) - starting training...

[1/4] Loading data...
  ✓ Market: 2215 days | News: 114 articles

[2/4] Generating LLM strategies...
  Progress: 110/110 (100.0%)
  ✓ Generated 110 strategies

[3/4] Training ReWTSE ensemble...
  ✓ Trained 5 chunk models

[4/4] Saving model...
  ✓ Saved to models/AAPL_rewts_ensemble.pkl
  ✓ Also saved to Google Drive: /content/drive/MyDrive/rewts_models/AAPL_rewts_ensemble.pkl

💾 Freeing memory...
📊 Current memory usage: 4567.8 MB

================================================================================
✅ AAPL training complete!
================================================================================
```

**Azione**: Training eseguito e modello salvato in entrambe le posizioni.

---

### Scenario 2: Modello Esiste in Locale

**Output**:
```
################################################################################
# [1/6] Processing AAPL
################################################################################

✓ Model already exists locally: models/AAPL_rewts_ensemble.pkl
  Skipping training for AAPL
  (Model not loaded to save RAM)
```

**Azione**: Training skippato, modello NON caricato in memoria (risparmio RAM).

---

### Scenario 3: Modello Esiste Solo su Drive

**Output**:
```
################################################################################
# [1/6] Processing AAPL
################################################################################

✓ Model already exists on Google Drive: /content/drive/MyDrive/rewts_models/AAPL_rewts_ensemble.pkl
  Skipping training for AAPL
  📥 Copying model from Drive to local...
  ✓ Model copied to models/AAPL_rewts_ensemble.pkl
```

**Azione**:
1. Training skippato
2. Modello copiato da Drive a locale (per backtesting successivo)
3. Modello NON caricato in memoria

---

### Scenario 4: Modello Esiste in Entrambe le Posizioni

**Output**:
```
################################################################################
# [1/6] Processing AAPL
################################################################################

✓ Model already exists locally: models/AAPL_rewts_ensemble.pkl
  Skipping training for AAPL
  (Model not loaded to save RAM)
```

**Azione**: Check locale ha priorità (più veloce), training skippato.

---

## 📊 Summary Finale

Alla fine del training, vedrai un riepilogo:

```
================================================================================
TRAINING COMPLETE
================================================================================

📊 Summary:
  Local models: 6
    - AAPL_rewts_ensemble.pkl
    - GOOGL_rewts_ensemble.pkl
    - MSFT_rewts_ensemble.pkl
    - AMZN_rewts_ensemble.pkl
    - META_rewts_ensemble.pkl
    - TSLA_rewts_ensemble.pkl
  Drive models: 6
    - AAPL_rewts_ensemble.pkl
    - GOOGL_rewts_ensemble.pkl
    - MSFT_rewts_ensemble.pkl
    - AMZN_rewts_ensemble.pkl
    - META_rewts_ensemble.pkl
    - TSLA_rewts_ensemble.pkl

================================================================================

💡 Note: Models not kept in memory to save RAM
   Load them individually for backtesting if needed
```

---

## 🔄 Use Cases

### Use Case 1: Continuare Training Interrotto

**Situazione**: Training si interrompe dopo 3 tickers (AAPL, GOOGL, MSFT)

**Soluzione**:
1. Riavvia notebook
2. Run training pipeline
3. I primi 3 tickers vengono skippati automaticamente
4. Training riparte dal 4° ticker (AMZN)

**Output**:
```
[1/6] AAPL - ✓ Already exists, skipping
[2/6] GOOGL - ✓ Already exists, skipping
[3/6] MSFT - ✓ Already exists, skipping
[4/6] AMZN - 🎯 Training...
[5/6] META - 🎯 Training...
[6/6] TSLA - 🎯 Training...
```

---

### Use Case 2: Re-train Singolo Ticker

**Situazione**: Vuoi ri-trainare solo AAPL (nuovi dati/config)

**Soluzione**:
1. Elimina il modello:
```python
# In una cella
!rm models/AAPL_rewts_ensemble.pkl
!rm /content/drive/MyDrive/rewts_models/AAPL_rewts_ensemble.pkl
```

2. Run training pipeline
3. Solo AAPL viene trainato, gli altri skippati

**Output**:
```
[1/6] AAPL - 🎯 Training...
[2/6] GOOGL - ✓ Skipping
[3/6] MSFT - ✓ Skipping
...
```

---

### Use Case 3: Training su Nuovo Notebook

**Situazione**: Nuovo notebook Colab, ma modelli già su Drive

**Soluzione**:
1. Mount Google Drive
2. Run training pipeline
3. Tutti i modelli vengono trovati su Drive
4. Copiati automaticamente in locale
5. Nessun training eseguito

**Output**:
```
[1/6] AAPL - ✓ Found on Drive, copying to local
[2/6] GOOGL - ✓ Found on Drive, copying to local
[3/6] MSFT - ✓ Found on Drive, copying to local
...

🎉 All models found and copied - no training needed!
```

**Tempo**: ~1-2 minuti invece di 3-4 ore!

---

### Use Case 4: Backup e Restore

**Situazione**: Vuoi fare backup dei modelli

**Backup**:
```python
# Modelli già salvati automaticamente su Drive durante training
# Path: /content/drive/MyDrive/rewts_models/
```

**Restore** (su nuovo Colab):
```python
# 1. Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# 2. Run training pipeline
# → Trova modelli su Drive
# → Copia in locale
# → Skip training
```

---

## ⚙️ Configurazione

### Path Drive Predefinito

```python
DRIVE_MODELS_PATH = '/content/drive/MyDrive/rewts_models'
```

### Cambiare Path Drive

Se vuoi usare un path diverso, modifica nella cella training:

```python
# Trova questa riga:
DRIVE_MODELS_PATH = '/content/drive/MyDrive/rewts_models'

# Cambia in:
DRIVE_MODELS_PATH = '/content/drive/MyDrive/my_custom_path'
```

---

## 🔍 Verifica Manuale

### Check Modelli Locali

```python
import os
local_models = os.listdir('models') if os.path.exists('models') else []
print("Local models:")
for model in local_models:
    if model.endswith('.pkl'):
        size_mb = os.path.getsize(f'models/{model}') / 1024 / 1024
        print(f"  {model}: {size_mb:.1f} MB")
```

### Check Modelli su Drive

```python
drive_path = '/content/drive/MyDrive/rewts_models'
if os.path.exists(drive_path):
    drive_models = os.listdir(drive_path)
    print("Drive models:")
    for model in drive_models:
        if model.endswith('.pkl'):
            size_mb = os.path.getsize(f'{drive_path}/{model}') / 1024 / 1024
            print(f"  {model}: {size_mb:.1f} MB")
else:
    print("Drive path not found - make sure Drive is mounted")
```

### Lista Completa con Size

```python
import os

def list_models():
    print("="*70)
    print("MODEL INVENTORY")
    print("="*70)

    # Local
    print("\n📁 Local (models/):")
    if os.path.exists('models'):
        local = [f for f in os.listdir('models') if f.endswith('.pkl')]
        if local:
            for model in sorted(local):
                size = os.path.getsize(f'models/{model}') / 1024 / 1024
                print(f"  ✓ {model:<35} {size:>6.1f} MB")
        else:
            print("  (empty)")
    else:
        print("  (directory not found)")

    # Drive
    drive_path = '/content/drive/MyDrive/rewts_models'
    print(f"\n☁️  Google Drive ({drive_path}):")
    if os.path.exists(drive_path):
        drive = [f for f in os.listdir(drive_path) if f.endswith('.pkl')]
        if drive:
            for model in sorted(drive):
                size = os.path.getsize(f'{drive_path}/{model}') / 1024 / 1024
                print(f"  ✓ {model:<35} {size:>6.1f} MB")
        else:
            print("  (empty)")
    else:
        print("  (not mounted or path not found)")

    print("="*70)

# Run
list_models()
```

Output esempio:
```
======================================================================
MODEL INVENTORY
======================================================================

📁 Local (models/):
  ✓ AAPL_rewts_ensemble.pkl            87.3 MB
  ✓ GOOGL_rewts_ensemble.pkl           91.2 MB
  ✓ MSFT_rewts_ensemble.pkl            89.4 MB

☁️  Google Drive (/content/drive/MyDrive/rewts_models):
  ✓ AAPL_rewts_ensemble.pkl            87.3 MB
  ✓ GOOGL_rewts_ensemble.pkl           91.2 MB
  ✓ MSFT_rewts_ensemble.pkl            89.4 MB
  ✓ AMZN_rewts_ensemble.pkl            93.1 MB
  ✓ META_rewts_ensemble.pkl            88.7 MB
  ✓ TSLA_rewts_ensemble.pkl            90.5 MB
======================================================================
```

---

## 🧹 Pulizia

### Elimina Tutti i Modelli Locali

```python
import shutil
if os.path.exists('models'):
    shutil.rmtree('models')
    print("✓ All local models deleted")
```

### Elimina Tutti i Modelli su Drive

```python
drive_path = '/content/drive/MyDrive/rewts_models'
if os.path.exists(drive_path):
    shutil.rmtree(drive_path)
    print("✓ All Drive models deleted")
```

### Elimina Singolo Modello

```python
ticker = 'AAPL'

# Local
local_path = f'models/{ticker}_rewts_ensemble.pkl'
if os.path.exists(local_path):
    os.remove(local_path)
    print(f"✓ Deleted local model for {ticker}")

# Drive
drive_path = f'/content/drive/MyDrive/rewts_models/{ticker}_rewts_ensemble.pkl'
if os.path.exists(drive_path):
    os.remove(drive_path)
    print(f"✓ Deleted Drive model for {ticker}")
```

---

## 💡 Best Practices

### ✅ Do

1. **Mantieni Drive come backup**
   - Modelli salvati automaticamente
   - Sopravvivono a crash/timeout Colab

2. **Verifica inventory prima di training**
   ```python
   list_models()  # Vedi funzione sopra
   ```

3. **Elimina modelli vecchi se ri-traini**
   ```python
   !rm models/AAPL_rewts_ensemble.pkl
   !rm /content/drive/MyDrive/rewts_models/AAPL_rewts_ensemble.pkl
   ```

4. **Usa Drive per condivisione**
   - Puoi condividere cartella Drive con altri
   - Altri possono usare tuoi modelli senza ri-trainare

### ❌ Don't

1. **Non eliminare Drive se training lungo**
   - Serve come backup se Colab crasha

2. **Non trainare se modello esiste**
   - Controlla prima:
   ```python
   list_models()
   ```

3. **Non mescolare versioni**
   - Se aggiorni config, elimina vecchi modelli prima

---

## 🚨 Troubleshooting

### "Drive path not found"

**Causa**: Drive non montato o path sbagliato

**Soluzione**:
```python
from google.colab import drive
drive.mount('/content/drive')

# Verifica path
!ls /content/drive/MyDrive/
```

### "Permission denied" copiando da Drive

**Causa**: Problemi permessi Drive

**Soluzione**:
```python
# Smonta e rimonta Drive
!fusermount -u /content/drive
from google.colab import drive
drive.mount('/content/drive', force_remount=True)
```

### Modello non trovato ma esiste

**Causa**: Nome file diverso

**Soluzione**:
```python
# Check nome esatto
!ls models/
!ls /content/drive/MyDrive/rewts_models/

# Deve essere esattamente: {TICKER}_rewts_ensemble.pkl
# Es: AAPL_rewts_ensemble.pkl
```

---

## 📚 Risorse

- **Memory Guide**: `MEMORY_OPTIMIZATION.md`
- **Notebooks Guide**: `NOTEBOOKS_GUIDE.md`
- **Colab Secrets**: `COLAB_SECRETS_SETUP.md`

---

**✅ Feature completata!** I notebook ora gestiscono automaticamente modelli esistenti su Drive.
