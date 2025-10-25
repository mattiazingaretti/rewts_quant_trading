# Training Scripts - Mensile

Scripts per training dei modelli ReWTSE-LLM-RL.

**Frequenza**: 1 volta/mese
**Tempo**: ~18 ore
**Costo**: ~$8/run

---

## 📋 Scripts

### 1. `create_training_vm.sh`
Crea VM Spot con GPU T4 per training.

**Cosa fa**:
- Crea n1-standard-4 Spot VM (4 vCPU, 15 GB RAM)
- Attach GPU T4 (16 GB VRAM)
- Installa CUDA drivers
- Clone repository
- Setup environment

**Costo**: $0.31/ora (~$5.58 per 18h training)

```bash
bash create_training_vm.sh
```

---

### 2. `download_data.py`
Download latest market data.

**Cosa fa**:
- Download OHLCV da Yahoo Finance
- Download fundamentals (P/E, margins, etc.)
- Download macro data (SPX, VIX, GDP, PMI)
- Generate/fetch news data
- Calculate technical indicators

**Tempo**: ~30 minuti
**Costo**: $0 (API gratuite)

```bash
# Run inside training VM
python download_data.py
```

**Output**:
```
data/
├── raw/
│   ├── AAPL_market_data.csv
│   ├── AAPL_fundamentals.csv
│   └── AAPL_news.json
└── processed/
    └── AAPL_features.csv
```

---

### 3. `train_rewts_llm_rl.py`
Training completo sistema.

**Cosa fa**:

#### Phase 1: Pre-compute LLM Strategies (~2-3 ore)
- Strategist Agent: Analizza market + fundamentals → LONG/SHORT
- Analyst Agent: Processa news → sentiment + impact
- Salva strategie: `data/llm_strategies/{ticker}_strategies.json`

#### Phase 2: Train DDQN Agents (~15 ore)
- Divide timeline in chunks (14 giorni)
- Train DDQN agent per chunk
- Ensemble optimization (QP)
- Salva modelli: `models/{ticker}/ddqn_chunk_{i}.pt`

**Tempo**: ~18 ore (6 ticker)
**Costo**: $5.58 (VM) + $2-3 (Gemini API)

```bash
# Run inside training VM
python train_rewts_llm_rl.py
```

**Output**:
```
models/
├── AAPL/
│   ├── ddqn_chunk_0.pt
│   ├── ddqn_chunk_1.pt
│   └── ...
└── ensemble.pkl
```

---

### 4. `build_docker_images.sh` (Optional)
Build e push Docker images.

**Quando**: Solo se hai modificato codice
**Tempo**: ~10 minuti
**Costo**: $0

```bash
bash build_docker_images.sh
```

---

## 🚀 Complete Training Workflow

### Step 1: Create Training VM
```bash
cd scripts/training
bash create_training_vm.sh

# Wait ~3 minutes for startup
```

### Step 2: SSH into VM
```bash
gcloud compute ssh rewts-training-spot --zone=us-central1-a
```

### Step 3: Setup Environment
```bash
cd /home/jupyter/rewts_quant_trading

# Load API key
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)

# Verify
echo $GEMINI_API_KEY
```

### Step 4: Download Data
```bash
python scripts/training/download_data.py

# Expected output:
# ✅ Downloaded AAPL: 2012-01-01 to 2020-12-31
# ✅ Downloaded AMZN: ...
# ✅ Downloaded fundamentals
# ✅ Generated news data
```

### Step 5: Train Models
```bash
python scripts/training/train_rewts_llm_rl.py

# This will run for ~18 hours
# You can monitor with:
# - watch -n 1 nvidia-smi
# - tail -f training.log
```

### Step 6: Upload to GCS
```bash
# Upload trained models
gsutil -m cp -r models/ gs://rewts-trading-data/models/

# Upload strategies
gsutil -m cp -r data/llm_strategies/ gs://rewts-trading-data/strategies/

# Verify
gsutil ls gs://rewts-trading-data/models/
```

### Step 7: Stop VM (IMPORTANTE!)
```bash
# Exit from VM
exit

# Stop VM (on local machine)
gcloud compute instances stop rewts-training-spot --zone=us-central1-a

# Verify stopped
gcloud compute instances list
# rewts-training-spot should show TERMINATED
```

---

## ⏱️ Timing Breakdown

| Step | Time | Cost |
|------|------|------|
| Create VM | 3 min | $0.02 |
| Download data | 30 min | $0.15 |
| LLM strategies | 3 hours | $0.93 + $2 API |
| DDQN training | 15 hours | $4.65 |
| Upload to GCS | 10 min | $0.05 |
| **TOTAL** | **~19 hours** | **~$8** |

---

## 📅 When to Train

### Monthly (Recommended)
- Inizio mese con dati mese precedente
- Consistent schedule

### On-Demand
- Performance degrada (Sharpe < 1.0)
- Major market events (crash, rally)
- Nuovi ticker da aggiungere
- Cambio strategia

### Avoid
- Training troppo frequente (overfitting)
- Training con pochi nuovi dati (<5% new)

---

## 🎯 Best Practices

### Before Training
1. ✅ Check dati disponibili sono aggiornati
2. ✅ Verify Gemini API key valid
3. ✅ Review config: `configs/hybrid/rewts_llm_rl.yaml`
4. ✅ Estimate costs (18h × $0.31 = $5.58)

### During Training
1. ✅ Monitor GPU usage: `nvidia-smi`
2. ✅ Check logs: `tail -f training.log`
3. ✅ Don't interrupt (use checkpointing if needed)

### After Training
1. ✅ **SEMPRE stop VM!** (critico per costs)
2. ✅ Upload modelli a GCS
3. ✅ Verify upload successful
4. ✅ Test models con backtesting

---

## 🚨 Troubleshooting

### Out of Memory
Edit `configs/hybrid/rewts_llm_rl.yaml`:
```yaml
rewts:
  batch_size: 32      # Reduce from 64
  buffer_size: 5000   # Reduce from 10000
```

### Gemini API Rate Limit
Add delay in code:
```python
import time
time.sleep(1)  # Between API calls
```

### GPU Not Detected
```bash
# Check GPU
nvidia-smi

# If not found, install drivers
sudo /opt/deeplearning/install-driver.sh
```

### VM Preempted During Training
Training has checkpointing. Restart VM and resume:
```bash
gcloud compute instances start rewts-training-spot --zone=us-central1-a
gcloud compute ssh rewts-training-spot --zone=us-central1-a
cd /home/jupyter/rewts_quant_trading
python scripts/training/train_rewts_llm_rl.py  # Will resume
```

---

## 💰 Cost Optimization

1. **Use Spot VMs** (già fatto) → 70% sconto
2. **Stop VM dopo uso** → 100% saving quando non usi
3. **Batch training** → Train più ticker insieme
4. **Cache LLM strategies** → Riusa se dati unchanged
5. **Train mensile** → Non più frequente del necessario

---

## 📚 Next Steps

After training:
```bash
# Test con backtesting
cd ../backtesting
python run_backtest.py

# Use for live strategies
cd ../live
python get_live_strategy.py --all
```

Or read: `../../TRAINING_AND_LIVE_USAGE_GUIDE.md`
