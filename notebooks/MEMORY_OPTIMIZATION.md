# Memory Optimization Guide

Guida alle ottimizzazioni di memoria nei notebook di training.

---

## ❌ Problema Originale

**Sintomo**: Training consuma ~50GB di RAM su Google Colab
**Causa**: Tutti i modelli tenuti in memoria contemporaneamente

```python
# ❌ Problema: Accumula modelli in memoria
trained_models = {}
for ticker in tickers:
    ensemble = train_ensemble(...)
    trained_models[ticker] = ensemble  # Kept in memory!
```

Con 6 tickers × ~8GB/modello = **48GB RAM** 💥

---

## ✅ Soluzione Implementata

### 1. **Garbage Collection Esplicito**

Dopo ogni ticker, liberiamo esplicitamente la memoria:

```python
import gc

# Train ticker
ensemble = train_ensemble(...)

# Save to disk
with open(f'models/{ticker}_ensemble.pkl', 'wb') as f:
    pickle.dump(ensemble, f)

# Free memory immediately
del ensemble
gc.collect()
```

### 2. **Non Tenere Modelli in Memoria**

```python
# ✅ Soluzione: Salva e libera
for ticker in tickers:
    ensemble = train_ensemble(...)

    # Save
    save_model(ensemble, f'models/{ticker}_ensemble.pkl')

    # Don't add to dict!
    # trained_models[ticker] = ensemble  # ❌ BAD

    # Free immediately
    del ensemble
    gc.collect()
```

### 3. **Libera Dati Intermedi**

```python
# Load data
market_df = load_data(ticker)
news_df = load_news(ticker)

# Generate strategies
strategies = generate_strategies(market_df, news_df)

# ✅ Free data after strategy generation
del market_df, news_df
gc.collect()

# Reload only what's needed
market_df = load_data(ticker)

# Train
ensemble = train_ensemble(market_df, strategies)

# ✅ Free again
del market_df, strategies
gc.collect()
```

### 4. **Backtesting Uno alla Volta**

```python
# ❌ BAD: Load all models
ensembles = {t: load_model(t) for t in tickers}
for ticker, ensemble in ensembles.items():
    backtest(ensemble)

# ✅ GOOD: Load one at a time
for ticker in tickers:
    ensemble = load_model(ticker)
    backtest(ensemble)
    del ensemble
    gc.collect()
```

---

## 📊 Risultati

| Metodo | RAM per Ticker | RAM Totale (6 tickers) |
|--------|----------------|------------------------|
| **Senza ottimizzazione** | ~8GB | ~50GB 💥 |
| **Con ottimizzazione** | ~5-10GB | ~5-10GB ✅ |

**Risparmio**: ~40GB (80% meno RAM)

---

## 🔍 Monitoraggio RAM

### In Colab (Built-in)

Colab mostra RAM usage nella barra superiore:
```
💾 RAM: 8.5 GB / 12.7 GB
```

### Nel Notebook (psutil)

```python
import psutil

def print_memory_usage():
    process = psutil.Process()
    mem_info = process.memory_info()
    mem_gb = mem_info.rss / 1024 / 1024 / 1024
    print(f"📊 Memory: {mem_gb:.2f} GB")

# After each ticker
print_memory_usage()
```

Output:
```
📊 Memory: 4.23 GB
```

### Check Disponibile

```python
import psutil

# Total system memory
total = psutil.virtual_memory().total / 1024**3
available = psutil.virtual_memory().available / 1024**3
used = psutil.virtual_memory().used / 1024**3

print(f"Total:     {total:.1f} GB")
print(f"Used:      {used:.1f} GB")
print(f"Available: {available:.1f} GB")
```

---

## 🎛️ Configurazioni Ottimizzate

### Colab Standard (12.7 GB RAM)

```python
config = {
    'tickers': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA'],  # ✅ OK

    'rewts': {
        'batch_size': 128,         # ✅ OK
        'buffer_size': 50000,      # ✅ OK
        'chunk_length': 400,       # ✅ OK
    }
}
```

### Colab Pro (25.5 GB RAM)

```python
config = {
    'tickers': ['AAPL', ..., 'TSLA', 'NVDA', 'AMD'],  # ✅ Più tickers

    'rewts': {
        'batch_size': 256,         # Può aumentare
        'buffer_size': 100000,     # Può aumentare
        'chunk_length': 500,       # Può aumentare
    }
}
```

### Colab Pro+ (51 GB RAM)

```python
config = {
    'tickers': [... 10+ tickers ...],  # ✅ Molti tickers

    'rewts': {
        'batch_size': 512,
        'buffer_size': 200000,
        'chunk_length': 800,
    }
}
```

---

## ⚠️ Troubleshooting

### "Out of Memory" durante Training

**Sintomi**:
```
RuntimeError: CUDA out of memory
# O:
MemoryError: Unable to allocate array
```

**Soluzioni**:

1. **Riduci batch_size**:
```python
'batch_size': 64,  # Da 128
```

2. **Riduci buffer_size**:
```python
'buffer_size': 25000,  # Da 50000
```

3. **Riduci chunk_length**:
```python
'chunk_length': 300,  # Da 400
```

4. **Meno tickers alla volta**:
```python
'tickers': ['AAPL', 'GOOGL'],  # Solo 2
```

5. **Restart runtime**:
```python
# Nel notebook, aggiungi periodicamente:
import gc
gc.collect()

# Oppure restart manualmente:
# Runtime → Restart runtime
```

### RAM cresce progressivamente

**Causa**: Memory leaks o garbage collection non efficace

**Soluzione**:
```python
# Aggiungi dopo ogni ticker:
import gc
import torch

# Free Python objects
gc.collect()

# Free CUDA memory (se usi GPU)
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# Force garbage collection
gc.collect()
gc.collect()  # Call twice for cyclic references
```

### Colab disconnette durante training

**Sintomi**: Tab si chiude, runtime stops

**Cause possibili**:
1. RAM esaurita → Colab kills session
2. Timeout (12h Colab standard)
3. Inattività

**Soluzioni**:
1. **Riduci RAM usage** (vedi sopra)
2. **Keep-alive script**:
```javascript
// In browser console
setInterval(() => {
  document.querySelector('colab-connect-button').click();
}, 60000);
```
3. **Checkpoint intermedi**:
```python
# Salva dopo ogni ticker
save_checkpoint(ticker, ensemble)
```

---

## 🚀 Best Practices

### ✅ Do

1. **Garbage collect dopo ogni ticker**
```python
del ensemble
gc.collect()
```

2. **Salva modelli su disco, non in memoria**
```python
save_model(ensemble)  # ✅
# trained_models[ticker] = ensemble  # ❌
```

3. **Monitora RAM usage**
```python
print_memory_usage()
```

4. **Usa chunks più piccoli se necessario**
```python
'chunk_length': 300  # vs 400
```

5. **Train meno tickers contemporaneamente**
```python
# Split in batches
batch1 = ['AAPL', 'GOOGL']
batch2 = ['MSFT', 'AMZN']
```

### ❌ Don't

1. **Non accumulare modelli**
```python
# ❌ BAD
models = {}
for ticker in tickers:
    models[ticker] = train(...)  # Accumulates!
```

2. **Non caricare tutti i modelli insieme**
```python
# ❌ BAD
models = [load(t) for t in tickers]  # All at once!

# ✅ GOOD
for ticker in tickers:
    model = load(ticker)
    use(model)
    del model
```

3. **Non ignorare memoria warnings**
```
⚠️ RAM: 11.2 GB / 12.7 GB  # ← Pericolosamente alto!
```

---

## 📝 Checklist Pre-Training

Prima di avviare training lungo:

```
□ RAM disponibile > 5GB
□ GPU disponibile (se Colab)
□ Garbage collection nel loop
□ Modelli salvati, non in memoria
□ Batch_size appropriato per RAM
□ Buffer_size appropriato per RAM
□ Monitoraggio RAM attivo
□ Checkpoint salvati su Drive
```

---

## 🔧 Advanced: Custom Memory Manager

Per controllo fine della memoria:

```python
class MemoryManager:
    def __init__(self, max_ram_gb=10):
        self.max_ram_gb = max_ram_gb

    def check_memory(self):
        import psutil
        used_gb = psutil.Process().memory_info().rss / 1024**3
        if used_gb > self.max_ram_gb:
            raise MemoryError(f"Exceeded {self.max_ram_gb}GB limit")
        return used_gb

    def cleanup(self):
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

# Uso
memory_mgr = MemoryManager(max_ram_gb=10)

for ticker in tickers:
    # Check before training
    memory_mgr.check_memory()

    # Train
    ensemble = train(...)

    # Cleanup after
    del ensemble
    memory_mgr.cleanup()

    # Verify
    used = memory_mgr.check_memory()
    print(f"Memory: {used:.2f} GB")
```

---

## 📚 Risorse

- **Notebook Guide**: `NOTEBOOKS_GUIDE.md`
- **Colab Docs**: https://colab.research.google.com/
- **Python GC**: https://docs.python.org/3/library/gc.html
- **PyTorch Memory**: https://pytorch.org/docs/stable/notes/cuda.html

---

## 💡 Summary

**Prima**: 50GB RAM (troppo per Colab standard)
**Dopo**: 5-10GB RAM (perfetto per Colab standard)

**Key changes**:
1. ✅ Garbage collection esplicito
2. ✅ Modelli non in memoria
3. ✅ Dati intermedi liberati
4. ✅ Backtesting sequenziale

**Result**: Training di 6 tickers su Colab standard (12.7GB) senza OOM! 🎉
