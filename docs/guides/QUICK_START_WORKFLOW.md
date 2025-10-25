# Quick Start - Training e Uso Live

Guida rapida per capire cosa fare e quando.

---

## 📋 Scripts: Una Tantum vs Ricorrenti

### 🔵 SETUP (Una Tantum - All'inizio)

```bash
# Esegui solo 1 volta all'inizio progetto (~30 min)
bash scripts/gcp/setup_project.sh          # Setup GCP
bash scripts/gcp/create_buckets.sh         # Storage
bash scripts/gcp/setup_secrets.sh          # API keys
bash scripts/gcp/deploy_fastapi_vm.sh      # Backtesting VM (option 2)
```

**Costo**: $0 setup + $3.72/mese (VM Spot)

---

### 🟢 TRAINING (Ricorrente - 1 volta/mese)

```bash
# Ogni mese (~18 ore training)
bash scripts/gcp/create_training_vm.sh
gcloud compute ssh rewts-training-spot --zone=us-central1-a

# Nella VM:
cd /home/jupyter/rewts_quant_trading
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)

python scripts/download_data.py           # Download latest data
python scripts/train_rewts_llm_rl.py      # Training completo

gsutil -m cp -r models/ gs://rewts-trading-data/models/
exit

# IMPORTANTE: Stop VM!
gcloud compute instances stop rewts-training-spot --zone=us-central1-a
```

**Frequenza**: 1 volta/mese (inizio mese)
**Costo**: ~$8/training

**Quando fare training**:
- ✅ Inizio mese (nuovi dati disponibili)
- ✅ Performance degrada (Sharpe < 1.0)
- ✅ Major market events (crash, rally)
- ✅ Nuovi ticker da aggiungere

---

### 🟡 LIVE STRATEGIES (Ricorrente - Daily/Hourly)

```bash
# Ogni giorno o ogni ora (istantaneo)
export GEMINI_API_KEY="your_key"

# Single ticker
python scripts/get_live_strategy.py --ticker AAPL

# All tickers
python scripts/get_live_strategy.py --all
```

**Frequenza**:
- Intraday: Ogni ora
- Swing trading: 1 volta/giorno (pre-market 8AM)
- Position trading: 1 volta/settimana

**Costo**: ~$0.001/call

---

### 🟠 BACKTESTING (Ricorrente - Weekly)

```python
# Weekend review (~10 min)
from examples.backtesting_client_example import BacktestingClient

client = BacktestingClient(vm_ip="YOUR_VM_IP")
result = client.run_backtest(ticker="AAPL", ...)
```

**Frequenza**: 1 volta/settimana (fine settimana)
**Costo**: $0 (VM fisso)

---

### 🔴 MONITORING (Continuo)

```bash
# Daily checks
bash scripts/gcp/manage_fastapi_vm.sh status
gcloud compute instances list
gcloud billing projects describe rewts-quant-trading
```

**Frequenza**: Giornaliero
**Costo**: $0

---

## 📅 Workflow Mensile Tipico

### Week 1: Training
```
Lunedì:
  → Create training VM ($0.31/hora)
  → SSH & download data (2h)
  → Start training (18h overnight)

Martedì:
  → Upload models to GCS
  → STOP VM ⚠️ (IMPORTANTE!)

Costo: ~$8
```

### Week 2-4: Live Trading
```
Ogni giorno (8:00 AM pre-market):
  → get_live_strategy.py --all
  → Review recommendations
  → Execute trades (manual or auto)

Weekend:
  → Backtesting review
  → Performance analysis

Costo: ~$2 Gemini API
```

---

## 💰 Costi Summary

| Tipo | Script | Frequenza | Costo |
|------|--------|-----------|-------|
| 🔵 Setup | `setup_project.sh` | Once | $0 |
| 🔵 Setup | `deploy_fastapi_vm.sh` | Once | $3.72/m |
| 🟢 Training | `train_rewts_llm_rl.py` | 1/month | $8 |
| 🟡 Live | `get_live_strategy.py` | Daily | $0.001/call |
| 🟠 Backtest | `backtesting_client.py` | Weekly | $0 |

**Total mensile**: ~$15-65/mese (dipende da uso live strategies)

---

## 🎯 Esempi Pratici

### Esempio 1: Swing Trader (Daily)
```bash
# Ogni giorno 8:00 AM
export GEMINI_API_KEY="your_key"
python scripts/get_live_strategy.py --ticker AAPL

# Output: LONG, confidence 2.7/3.0
# → Execute buy order
```

**Costo mensile**: Training $8 + Live $1.80 (60 calls) + VM $3.72 = **~$13/mese**

### Esempio 2: Position Trader (Weekly)
```bash
# Ogni lunedì
python scripts/get_live_strategy.py --all

# Weekend: Backtesting review
python examples/backtesting_client_example.py
```

**Costo mensile**: Training $8 + Live $0.12 (8 batch calls) + VM $3.72 = **~$12/mese**

### Esempio 3: Intraday Trader (Hourly)
```bash
# Ogni ora durante market hours (9:30 AM - 4:00 PM)
# 6.5 hours × 5 days × 4 weeks = 130 calls/mese

python scripts/get_live_strategy.py --ticker AAPL
```

**Costo mensile**: Training $8 + Live $3.90 (130 calls) + VM $3.72 = **~$16/mese**

---

## ⚡ Quick Commands

### Get Live Strategy Now
```bash
export GEMINI_API_KEY="your_key"
python scripts/get_live_strategy.py --ticker AAPL
```

### Check Backtest ing VM
```bash
bash scripts/gcp/manage_fastapi_vm.sh status
bash scripts/gcp/manage_fastapi_vm.sh ip
```

### Check Training VM (should be STOPPED)
```bash
gcloud compute instances list
# rewts-training-spot should be TERMINATED
```

### Check Costs
```bash
gcloud billing projects describe rewts-quant-trading
```

---

## 🎓 Learning Path

### Day 1: Setup (30 min)
```bash
bash scripts/gcp/setup_project.sh
bash scripts/gcp/create_buckets.sh
bash scripts/gcp/setup_secrets.sh
bash scripts/gcp/deploy_fastapi_vm.sh
```

### Day 2-3: First Training (20 hours)
```bash
bash scripts/gcp/create_training_vm.sh
# SSH, download, train, upload, stop
```

### Day 4-30: Live Usage (daily)
```bash
python scripts/get_live_strategy.py --all
# Review, trade, repeat
```

### Weekend: Review
```python
# Backtesting analysis
client = BacktestingClient(...)
results = client.run_batch_backtests(...)
```

---

## 📚 Full Documentation

- **Full Guide**: `TRAINING_AND_LIVE_USAGE_GUIDE.md`
- **GCP Setup**: `GCP_VM_Spot_Deployment.md`
- **Scripts Reference**: `scripts/gcp/README.md`
- **Examples**: `examples/backtesting_client_example.py`

---

## 🚨 Important Reminders

1. **ALWAYS** stop training VM after use!
   ```bash
   gcloud compute instances stop rewts-training-spot --zone=us-central1-a
   ```

2. **Backtesting VM** stays on 24/7 (Spot, $3.72/mese)

3. **Training** 1 volta/mese is enough (unless major events)

4. **Live strategies** cache risultati per save costs

5. **Monitor costs** settimanalmente:
   ```bash
   gcloud billing projects describe rewts-quant-trading
   ```

---

## ✅ Checklist

### Setup (Once)
- [ ] `setup_project.sh` - GCP project
- [ ] `create_buckets.sh` - Storage
- [ ] `setup_secrets.sh` - API keys
- [ ] `deploy_fastapi_vm.sh` - Backtesting VM

### Monthly
- [ ] `create_training_vm.sh` - Start training VM
- [ ] `download_data.py` - Get latest data
- [ ] `train_rewts_llm_rl.py` - Train models
- [ ] Upload to GCS
- [ ] **STOP training VM** ⚠️

### Daily
- [ ] `get_live_strategy.py` - Get recommendations
- [ ] Review & execute trades
- [ ] Monitor performance

### Weekly
- [ ] `backtesting_client.py` - Review backtest
- [ ] Check costs
- [ ] Performance analysis

---

Ora sei pronto! Inizia con il setup e poi training mensile + live strategies daily. 🚀
