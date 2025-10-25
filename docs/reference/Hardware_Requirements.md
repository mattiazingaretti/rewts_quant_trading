# Requisiti Hardware per ReWTSE-LLM-RL

Questo documento descrive i requisiti hardware necessari per addestrare e utilizzare il sistema ReWTSE-LLM-RL, con particolare attenzione alle esigenze di GPU e VRAM.

---

## 📊 Sommario Requisiti

| Componente | Minimo | Consigliato | Ottimale |
|------------|--------|-------------|----------|
| **CPU** | 4 core | 8 core | 16+ core |
| **RAM** | 16 GB | 32 GB | 64 GB |
| **GPU** | Opzionale | GTX 1660 Ti (6GB) | RTX 3090/4090 (24GB) |
| **VRAM** | N/A (CPU-only) | 6 GB | 12-24 GB |
| **Storage** | 50 GB SSD | 100 GB SSD | 500 GB NVMe |
| **Tempo Training** | ~24-48h | ~8-12h | ~2-4h |

---

## 🖥️ Requisiti Dettagliati per Componente

### 1. CPU (Central Processing Unit)

#### Minimo (CPU-only setup)
- **Cores**: 4 core / 8 thread
- **Clock**: 2.5 GHz+
- **Esempi**:
  - Intel Core i5-8400
  - AMD Ryzen 5 3600
- **Nota**: Possibile addestrare su CPU, ma **molto lento** (10-50x più lento della GPU)

#### Consigliato
- **Cores**: 8 core / 16 thread
- **Clock**: 3.0 GHz+
- **Esempi**:
  - Intel Core i7-10700K
  - AMD Ryzen 7 5800X
- **Perché**: Utile per preprocessing dati, chiamate API LLM parallele, e QP optimization

#### Ottimale
- **Cores**: 16+ core / 32+ thread
- **Clock**: 3.5 GHz+
- **Esempi**:
  - Intel Core i9-13900K
  - AMD Ryzen 9 7950X
  - AMD Threadripper 3970X
- **Perché**: Massime performance per preprocessing massivo e training multi-chunk parallelo

---

### 2. RAM (Memory)

#### Minimo: 16 GB
**Breakdown**:
- Sistema operativo: ~4 GB
- Dataset in memoria: ~2-4 GB (per ticker)
- PyTorch training: ~4-6 GB
- Google Gemini API calls: ~1-2 GB
- Buffer e overhead: ~2 GB

**Limitazioni**:
- Possibile solo con 1-2 ticker alla volta
- Necessario ridurre batch_size e buffer_size
- Rischio di swap su disco (molto lento)

#### Consigliato: 32 GB
**Breakdown**:
- Sistema operativo: ~4 GB
- Dataset multi-ticker: ~8-10 GB
- PyTorch training: ~8-10 GB
- LLM processing: ~2-4 GB
- QP optimization (cvxopt): ~2-4 GB
- Buffer e headroom: ~4 GB

**Capacità**:
- 3-4 ticker simultaneamente
- Batch size standard (64)
- Buffer size standard (10000)

#### Ottimale: 64 GB
**Breakdown**:
- Permette di caricare tutti i 6 ticker in memoria
- Training multi-chunk parallelo
- Grandi batch size (128-256)
- Buffer size esteso (50000+)
- Nessun rischio di memory swapping

---

### 3. GPU (Graphics Processing Unit)

#### Scenario 1: CPU-Only (Nessuna GPU)

**Fattibilità**: ✅ Possibile ma **NON consigliato**

**Pros**:
- Nessun costo aggiuntivo GPU
- Funziona su qualsiasi computer moderno

**Cons**:
- Training **10-50x più lento**
- Tempo stimato per 1 ticker: **24-48 ore**
- Tempo stimato per 6 ticker: **1-2 settimane**
- Inefficiente per sperimentazione iterativa

**Quando usarlo**:
- Solo per testing iniziale del codice
- Budget molto limitato
- Proof-of-concept minimo

**Configurazione consigliata per CPU-only**:
```yaml
rewts:
  chunk_length: 500          # Ridotto
  episodes_per_chunk: 10     # Molto ridotto
  batch_size: 32             # Ridotto
  hidden_dims: [64, 32]      # Rete più piccola
```

---

#### Scenario 2: GPU Entry-Level (6 GB VRAM)

**GPU Consigliate**:
- NVIDIA GTX 1660 Ti (6 GB)
- NVIDIA RTX 2060 (6 GB)
- NVIDIA RTX 3050 (8 GB)

**Fattibilità**: ✅ Buono per progetti individuali

**Pros**:
- Training **5-10x più veloce** della CPU
- Tempo stimato per 1 ticker: **4-8 ore**
- Costo contenuto (~€200-400)

**Cons**:
- VRAM limitata → necessario ridurre dimensioni modello
- Possibile training solo 1 chunk alla volta
- Batch size limitato

**Capacità**:
- 1-2 ticker alla volta
- Batch size: 32-64
- Buffer size: 5000-10000
- Hidden dims: [128, 64] o [64, 32]

**Breakdown VRAM (6 GB)**:
- PyTorch framework: ~1 GB
- Policy Network: ~0.5 GB
- Target Network: ~0.5 GB
- Replay Buffer: ~1-2 GB
- Batch tensors: ~0.5-1 GB
- Gradients & optimizer state: ~1-1.5 GB
- Overhead: ~0.5 GB

**Configurazione ottimizzata per 6 GB**:
```yaml
rewts:
  chunk_length: 1000
  episodes_per_chunk: 30
  batch_size: 32             # Ridotto per VRAM
  buffer_size: 5000          # Ridotto per VRAM
  hidden_dims: [128, 64]     # OK per 6 GB
```

---

#### Scenario 3: GPU Mid-Range (8-12 GB VRAM)

**GPU Consigliate**:
- NVIDIA RTX 3060 (12 GB) ⭐ **SCELTA OTTIMALE PREZZO/PRESTAZIONI**
- NVIDIA RTX 3060 Ti (8 GB)
- NVIDIA RTX 4060 Ti (8-16 GB)

**Fattibilità**: ✅✅ **Ideale per questo progetto**

**Pros**:
- Training **10-20x più veloce** della CPU
- Tempo stimato per 1 ticker: **2-4 ore**
- Tempo stimato per 6 ticker: **12-24 ore**
- VRAM sufficiente per configurazione standard
- Ottimo rapporto qualità/prezzo

**Cons**:
- Nessun limite significativo per questo progetto

**Capacità**:
- Tutti i 6 ticker (sequenzialmente)
- Batch size standard: 64
- Buffer size standard: 10000
- Hidden dims: [128, 64] o [256, 128]
- Possibilità di training parallelo di 2 chunk su GPU diverse

**Breakdown VRAM (12 GB)**:
- PyTorch framework: ~1 GB
- Policy Network (128x64): ~0.8 GB
- Target Network (128x64): ~0.8 GB
- Replay Buffer (10000): ~2-3 GB
- Batch tensors (64): ~1 GB
- Gradients & optimizer state: ~2 GB
- Overhead: ~1 GB
- **Headroom**: ~3-4 GB per sperimentare

**Configurazione standard per 8-12 GB**:
```yaml
rewts:
  chunk_length: 2016         # Standard
  episodes_per_chunk: 50     # Standard
  batch_size: 64             # Standard
  buffer_size: 10000         # Standard
  hidden_dims: [128, 64]     # Standard
```

**Raccomandazione**: 🎯 **RTX 3060 12GB a ~€300-350 è la scelta migliore per questo progetto.**

---

#### Scenario 4: GPU High-End (16-24 GB VRAM)

**GPU Consigliate**:
- NVIDIA RTX 3090 (24 GB)
- NVIDIA RTX 4090 (24 GB)
- NVIDIA RTX A5000 (24 GB)
- NVIDIA RTX 4080 (16 GB)

**Fattibilità**: ✅✅✅ Overkill ma ottimale

**Pros**:
- Training **20-40x più veloce** della CPU
- Tempo stimato per 1 ticker: **1-2 ore**
- Tempo stimato per 6 ticker: **6-12 ore**
- VRAM abbondante per sperimentazione
- Possibilità di reti molto grandi
- Training parallelo di chunk multipli
- Nessun limite pratico

**Cons**:
- Costo molto elevato (€1000-2000+)
- Overkill per questo progetto specifico
- Consumo energetico alto (350-450W)

**Capacità**:
- Tutti i 6 ticker simultaneamente
- Batch size esteso: 128-256
- Buffer size esteso: 50000+
- Hidden dims estesi: [256, 128] o [512, 256]
- Training parallelo di 3-4 chunk
- Hyperparameter search massivo

**Breakdown VRAM (24 GB)**:
- PyTorch framework: ~1 GB
- Policy Network (256x128): ~1.5 GB
- Target Network (256x128): ~1.5 GB
- Replay Buffer (50000): ~8-10 GB
- Batch tensors (128): ~2 GB
- Gradients & optimizer state: ~3 GB
- Multiple chunks in parallel: ~4 GB
- **Headroom**: ~5-8 GB

**Configurazione estesa per 16-24 GB**:
```yaml
rewts:
  chunk_length: 2016
  episodes_per_chunk: 100    # Esteso
  batch_size: 128            # Esteso
  buffer_size: 50000         # Esteso
  hidden_dims: [256, 128]    # Esteso
```

---

### 4. Storage (Archiviazione)

#### Minimo: 50 GB SSD
**Breakdown**:
- Sistema operativo e software: ~20 GB
- Python + PyTorch + dipendenze: ~10 GB
- Dataset (6 ticker, 2012-2020): ~5 GB
- Modelli salvati (chunk models): ~5 GB
- Strategie LLM pre-computate: ~2 GB
- Risultati e visualizzazioni: ~3 GB
- Spazio temporaneo: ~5 GB

#### Consigliato: 100 GB SSD
- Spazio per esperimenti multipli
- Checkpoints intermedi
- Dati aggiuntivi (real news, etc.)

#### Ottimale: 500 GB NVMe
- Dataset estesi (più ticker, più anni)
- Multiple configurazioni salvate
- Grid search di hyperparameters
- Performance I/O massima

**Velocità I/O Importante Per**:
- Caricamento dataset: 5-10x più veloce con NVMe
- Salvataggio checkpoints frequenti
- Scrittura metriche e logs

---

## ⚡ Confronto Tempi di Training

### Training completo (6 ticker, configurazione standard)

| Setup | GPU | VRAM | Tempo Totale | Costo Hardware |
|-------|-----|------|--------------|----------------|
| **CPU-only** | Nessuna | N/A | ~7-14 giorni | €0 (già disponibile) |
| **Entry-level** | GTX 1660 Ti | 6 GB | ~2-3 giorni | ~€250 |
| **Mid-range** ⭐ | RTX 3060 | 12 GB | **12-24 ore** | **~€350** |
| **High-end** | RTX 3090 | 24 GB | 6-12 ore | ~€1500 |
| **Cloud (Colab)** | T4/V100 | 16 GB | 12-18 ore | $0-50/mese |

### Training singolo ticker (es. AAPL)

| Setup | Tempo | Note |
|-------|-------|------|
| **CPU-only** | 24-48 ore | Non pratico |
| **Entry-level (6 GB)** | 4-8 ore | Accettabile |
| **Mid-range (12 GB)** ⭐ | **2-4 ore** | **Ottimale** |
| **High-end (24 GB)** | 1-2 ore | Veloce ma costoso |

---

## ☁️ Alternative Cloud (Senza GPU Locale)

### Google Colab

**Pro**:
- **Gratuito** (con limiti) o €9.99/mese (Colab Pro)
- GPU Tesla T4 (16 GB) o V100 (16 GB)
- Nessun investimento hardware
- Accesso immediato

**Contro**:
- Limite di 12 ore per sessione gratuita
- Possibili disconnessioni
- Necessario dividere training in chunk
- Dipendenza da connessione internet

**Costo**:
- **Free**: €0 (con limitazioni)
- **Colab Pro**: €9.99/mese
- **Colab Pro+**: €49.99/mese (V100, 24h runtime)

**Consigliato per**:
- Testing iniziale
- Budget molto limitato
- Uso occasionale

---

### Paperspace Gradient

**Specs**:
- GPU P4000 (8 GB): $0.51/ora
- GPU RTX 4000 (8 GB): $0.76/hora
- GPU RTX 5000 (16 GB): $1.11/hora
- GPU A6000 (48 GB): $1.89/hora

**Costo stimato per training completo** (6 ticker):
- P4000: ~$10-15 (20-30 ore)
- RTX 5000: ~$15-20 (12-18 ore)

**Pro**:
- Pay-per-use
- Nessun investimento iniziale
- Storage persistente
- Buone performance

**Contro**:
- Costi ricorrenti
- Dipendenza da connessione

---

### AWS EC2 (con GPU)

**Istanze GPU**:
- g4dn.xlarge (T4, 16GB): $0.526/ora
- g5.xlarge (A10G, 24GB): $1.006/ora
- p3.2xlarge (V100, 16GB): $3.06/ora

**Costo stimato per training completo** (6 ticker):
- g4dn.xlarge: ~$10-15 (20-30 ore)
- g5.xlarge: ~$12-18 (12-18 ore)

**Pro**:
- Massima flessibilità
- Scalabilità
- Storage S3 illimitato

**Contro**:
- Configurazione complessa
- Costi variabili
- Necessario gestire istanze

---

## 🎯 Raccomandazioni Finali

### Per Budget Limitato (<€100)
**Soluzione**: Google Colab Pro (€9.99/mese)
- Sufficiente per completare il training
- Nessun investimento hardware
- Cancellabile dopo il progetto

**Tempo**: ~2-3 giorni di training distribuito

---

### Per Budget Medio (€300-500) ⭐ **RACCOMANDATO**
**Soluzione**: RTX 3060 12GB (~€350)
- **Miglior rapporto qualità/prezzo**
- Velocità ottima per questo progetto
- Riutilizzabile per altri progetti ML
- No costi ricorrenti

**Tempo**: 12-24 ore per training completo

**Perché è la scelta migliore**:
- VRAM (12 GB) più che sufficiente
- Prezzo accessibile
- Ottima per deep learning in generale
- Efficienza energetica buona (170W)
- Disponibilità sul mercato

---

### Per Uso Professionale/Ricerca (€1000+)
**Soluzione**: RTX 4090 24GB (~€1800)
- Massima velocità
- Nessun limite per sperimentazione
- Future-proof per progetti più grandi

**Tempo**: 6-12 ore per training completo

---

## 🔧 Ottimizzazioni per Hardware Limitato

### Se hai solo CPU (nessuna GPU)

1. **Riduci drasticamente la complessità**:
```yaml
rewts:
  chunk_length: 500          # ~3.5 giorni invece di 14
  episodes_per_chunk: 10     # Molto ridotto
  batch_size: 16             # Minimo
  buffer_size: 2000          # Ridotto
  hidden_dims: [64, 32]      # Rete piccola
```

2. **Usa un solo ticker per testing**: `tickers: ['AAPL']`

3. **Riduci periodo dati**: `2018-2020` invece di `2012-2020`

4. **Considera cloud GPU per training finale**

---

### Se hai GPU con poca VRAM (4-6 GB)

1. **Ottimizza configurazione**:
```yaml
rewts:
  batch_size: 32             # Ridotto
  buffer_size: 5000          # Ridotto
  hidden_dims: [64, 32]      # Rete più piccola
```

2. **Training sequenziale**:
```python
# Train un ticker alla volta
for ticker in ['AAPL']:  # Un ticker per volta
    train_ticker(ticker)
    torch.cuda.empty_cache()  # Libera VRAM
```

3. **Gradient checkpointing** (avanzato):
```python
# In ddqn_agent.py, usa gradient checkpointing
torch.utils.checkpoint.checkpoint(...)
```

---

## 📊 Monitoring Utilizzo Risorse

### Durante il Training

**CPU**:
```bash
htop  # Linux/Mac
# Oppure Task Manager su Windows
```

**GPU**:
```bash
watch -n 1 nvidia-smi  # Mostra utilizzo GPU ogni secondo
```

**RAM e Storage**:
```bash
free -h  # RAM usage (Linux)
df -h    # Disk usage
```

**In Python (durante training)**:
```python
import psutil
import torch

# RAM
print(f"RAM: {psutil.virtual_memory().percent}%")

# GPU (se disponibile)
if torch.cuda.is_available():
    print(f"GPU Memory: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    print(f"GPU Memory Cached: {torch.cuda.memory_reserved() / 1e9:.2f} GB")
```

---

## 🏁 Conclusione

### Setup Ottimale Raccomandato per ReWTSE-LLM-RL

**Hardware**:
- CPU: 8 core (Ryzen 7 / i7)
- RAM: 32 GB
- GPU: **RTX 3060 12GB** ⭐
- Storage: 100 GB SSD

**Costo Totale**: ~€350-400 (solo GPU, il resto tipicamente già disponibile)

**Performance Attese**:
- Training 1 ticker: 2-4 ore
- Training 6 ticker: 12-24 ore
- Backtesting: 5-10 minuti

**Questo setup offre il miglior compromesso tra costo, velocità e flessibilità per questo progetto specifico.**

---

## ❓ FAQ Hardware

**Q: Posso usare una GPU AMD invece di NVIDIA?**
A: No, PyTorch richiede CUDA (NVIDIA) per training ottimale. AMD ROCm è supportato ma meno stabile.

**Q: Posso usare un Mac con M1/M2?**
A: Sì, ma con limitazioni. PyTorch supporta MPS (Metal) ma è più lento di CUDA. Stimare ~2-3x più lento di RTX 3060.

**Q: La GPU è assolutamente necessaria?**
A: No, ma fortemente consigliata. CPU-only richiede 10-50x più tempo.

**Q: Quanta energia consuma il training?**
A: RTX 3060: ~170W x 24h = ~4 kWh (~€1-2 di elettricità per training completo)

**Q: Posso interrompere e riprendere il training?**
A: Sì, basta implementare checkpoint saving (già previsto nel codice).

**Q: Serve GPU anche per backtesting?**
A: No, il backtesting usa solo inferenza (veloce anche su CPU).
