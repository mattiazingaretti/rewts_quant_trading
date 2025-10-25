# Training e Uso Live - Guida Completa
## ReWTSE-LLM-RL System

Workflow completo dal training all'interrogazione live degli agent per strategie.

---

## 📋 Overview Workflow

```
1. TRAINING (GCP VM con GPU)
   ├── Download dati market + fundamentals + news
   ├── Pre-computa strategie LLM (Strategist + Analyst)
   ├── Training DDQN agents per chunk temporale
   ├── Salva modelli ensemble su GCS
   └── Stop VM (save costs)

2. BACKTESTING (GCP VM Spot FastAPI)
   ├── Carica modelli da GCS
   ├── Esegui backtest su periodo test
   ├── Calcola metriche performance
   └── API sempre disponibile

3. LIVE USAGE (Anywhere)
   ├── Interroga Strategist Agent per strategie
   ├── Interroga Analyst Agent per news analysis
   ├── Combina con modelli trained
   └── Genera raccomandazioni trading
```

---

## 🎓 PARTE 1: Training dei Modelli

### Step 1.1: Crea Training VM con GPU

```bash
cd rewts_quant_trading

# Crea Spot VM con GPU T4
bash scripts/gcp/create_training_vm.sh

# Output:
# ✅ VM created: rewts-training-spot
# Cost: ~$0.31/hora
```

### Step 1.2: SSH nella VM

```bash
# SSH
gcloud compute ssh rewts-training-spot --zone=us-central1-a

# Una volta dentro:
cd /home/jupyter/rewts_quant_trading

# Carica API key
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)
```

### Step 1.3: Download Dati

```bash
# Download market data, fundamentals, news
python scripts/download_data.py

# Output:
# ✅ Downloaded AAPL: 2012-01-01 to 2020-12-31
# ✅ Downloaded AMZN: 2012-01-01 to 2020-12-31
# ...
# ✅ Downloaded fundamentals for all tickers
# ✅ Generated mock news (replace with real API)
```

**Cosa scarica**:
- OHLCV data (Yahoo Finance)
- Technical indicators (SMA, RSI, MACD, ATR)
- Fundamentals (P/E, margins, ratios)
- Macro data (SPX, VIX)
- News (mock - da sostituire con API reali)

### Step 1.4: Training Completo

```bash
# Start training
python scripts/train_rewts_llm_rl.py

# Durata: ~18 ore per 6 ticker
# Costo: ~$5.58 (VM Spot)
```

**Cosa fa il training**:

#### Fase 1: Pre-computazione Strategie LLM
```
Per ogni ticker:
  Per ogni mese (20 trading days):
    1. Strategist Agent analizza:
       - Market data (price, volume, volatility)
       - Fundamentals (P/E, margins, ratios)
       - Technical indicators (RSI, MACD, MA)
       - Macro data (SPX, VIX, GDP, PMI)
       - Last strategy performance (reflection)

    2. Analyst Agent processa:
       - News del periodo
       - Sentiment analysis
       - Impact scoring (Likert 1-3)
       - Top 3 fattori rilevanti

    3. Combina:
       - Strategist recommendation (LONG/SHORT)
       - Analyst sentiment
       - Confidence score
       - Reasoning/explanation

    4. Salva strategia in:
       data/llm_strategies/{ticker}_strategies.json
```

#### Fase 2: Training DDQN Agents
```
Per ogni ticker:
  Divide timeline in chunks (14 giorni = 2016 timesteps)

  Per ogni chunk:
    1. Crea DDQN agent specializzato
    2. Training per 50 episodi:
       - State: market features + LLM strategy
       - Action: BUY, SELL, HOLD
       - Reward: PnL + transaction costs
    3. Salva modello chunk:
       models/{ticker}/ddqn_chunk_{i}.pt

  Finale:
    - Ensemble di N chunk models
    - QP optimization per pesi dinamici
```

### Step 1.5: Monitor Training

In una seconda finestra:

```bash
# SSH in VM
gcloud compute ssh rewts-training-spot --zone=us-central1-a

# Monitor GPU
watch -n 1 nvidia-smi

# Monitor logs
tail -f training.log
```

**Output atteso**:
```
==============================================================
Training ReWTSE-LLM-RL for AAPL
==============================================================

Phase 1: Pre-computing LLM Strategies
=====================================
✓ Strategist Agent initialized (gemini-2.0-flash-exp)
✓ Analyst Agent initialized (gemini-2.0-flash-exp)

Generating strategies: 100%|████████████| 108/108 [12:34<00:00, 0.14it/s]
✅ Saved 108 strategies to data/llm_strategies/AAPL_strategies.json

Phase 2: Training DDQN Agents
==============================
Chunk 1/10: Training episodes... [Episode 50/50] Reward: 1245.67
Chunk 2/10: Training episodes... [Episode 50/50] Reward: 1156.23
...
✅ Saved ensemble to models/AAPL/ensemble.pkl

==============================================================
✅ AAPL Training Complete! (2.5 hours)
==============================================================
```

### Step 1.6: Upload Modelli su GCS

```bash
# Upload trained models to GCS
gsutil -m cp -r models/ gs://rewts-trading-data/models/
gsutil -m cp -r data/llm_strategies/ gs://rewts-trading-data/strategies/

# Output:
# Copying file://models/AAPL/ddqn_chunk_0.pt...
# Copying file://models/AAPL/ddqn_chunk_1.pt...
# ...
# ✅ All models uploaded to GCS
```

### Step 1.7: Stop VM (IMPORTANTE!)

```bash
# Exit from VM
exit

# Stop VM (on local machine)
gcloud compute instances stop rewts-training-spot --zone=us-central1-a

# ✅ VM stopped - no more charges!
```

**💰 Costo Training**:
- 18 ore × $0.31/ora = **~$5.58**
- Plus Gemini API: ~$2-3 per 600-900 calls
- **Total: ~$8/training run**

**⏱️ Frequenza**:
- Training completo: 1 volta/mese (quando aggiungi nuovi dati)
- Re-training parziale: quando performance degrada

---

---

## 🔍 PARTE 2: Interrogazione Live degli Agent

Ora che i modelli sono trained, puoi interrogare gli agent LLM **in qualsiasi momento** per ottenere strategie live.

### Option A: Strategia Singola Live

```bash
# Set API key
export GEMINI_API_KEY="your_key_here"

# Get strategy for single ticker
python scripts/get_live_strategy.py --ticker AAPL
```

**Output**:
```
======================================================================
🤖 Getting LIVE Strategy for AAPL
======================================================================

🔧 Initializing LLM Agents...
✓ Strategist Agent initialized (gemini-2.0-flash-exp)
✓ Analyst Agent initialized (gemini-2.0-flash-exp)

📊 Fetching latest data for AAPL...
✅ Fetched 60 days of data

📰 Fetching latest news for AAPL...
✅ Fetched 10 news articles

📰 Analyst Agent: Processing news...

  Top Factors:
    1. 🟢 Apple announces new AI features in iOS 18 (Impact: 3/3)
    2. ⚪ iPhone sales meet expectations in Q3 (Impact: 2/3)
    3. 🔴 Regulatory concerns in EU market (Impact: 2/3)

  Aggregate Sentiment: 0.42
  Average Impact: 2.33/3

📊 Strategist Agent: Generating strategy...

======================================================================
🎯 FINAL STRATEGY
======================================================================

  Ticker: AAPL
  Recommendation: LONG 🟢
  Confidence: 2.65/3.0
  Current Price: $182.45
  RSI: 58.3

  Reasoning:
  Strong technical setup with price above SMA_20 and SMA_50. RSI at 58.3
  indicates room for upside before overbought. Positive news sentiment
  (+0.42) from AI announcements offsets regulatory concerns. P/E of 29.5
  is reasonable for tech sector. Recommend LONG with moderate confidence.

======================================================================
```

### Option B: Strategie Multiple (Batch)

```bash
# Get strategies for multiple tickers
python scripts/get_live_strategy.py --tickers AAPL TSLA MSFT

# Or all tickers from config
python scripts/get_live_strategy.py --all
```

**Output**:
```
======================================================================
📊 STRATEGIES SUMMARY
======================================================================

Ticker     Rec      Conf     Sentiment    Price       
----------------------------------------------------------------------
AAPL       🟢 LONG   2.65     0.42         $182.45     
TSLA       🔴 SHORT  2.10     -0.25        $245.30     
MSFT       🟢 LONG   2.85     0.58         $415.20     
GOOGL      🟢 LONG   2.40     0.32         $138.75     
META       🟢 LONG   2.55     0.45         $485.60     
AMZN       🟢 LONG   2.30     0.28         $175.80     
======================================================================

✅ Strategies saved to live_strategies_20250125_143022.json
```

### Option C: Uso Programmatico da Python

```python
from scripts.get_live_strategy import get_live_strategy
import os

# Set API key
os.environ['GEMINI_API_KEY'] = 'your_key_here'

# Get strategy
strategy = get_live_strategy('AAPL', verbose=True)

# Access results
print(f"Recommendation: {strategy['recommendation']}")
print(f"Confidence: {strategy['confidence']}")
print(f"Reasoning: {strategy['reasoning']}")

# Use in your trading logic
if strategy['recommendation'] == 'LONG' and strategy['confidence'] > 2.5:
    print("✅ Strong buy signal!")
    # Execute buy order...
elif strategy['recommendation'] == 'SHORT' and strategy['confidence'] > 2.5:
    print("⚠️ Strong sell signal!")
    # Execute sell order...
else:
    print("⏸️ Hold position")
```

---

## 📊 PARTE 3: Backtesting con Modelli Trained

Una volta completato il training, puoi eseguire backtesting usando l'API FastAPI.

### Step 3.1: Assicurati VM Backtesting sia Running

```bash
# Check status
bash scripts/gcp/manage_fastapi_vm.sh status

# If not running, start it
bash scripts/gcp/manage_fastapi_vm.sh start

# Get IP
bash scripts/gcp/manage_fastapi_vm.sh ip
# Output: External IP: 35.123.45.67
```

### Step 3.2: Run Backtest

```python
from examples.backtesting_client_example import BacktestingClient

# Initialize
client = BacktestingClient(vm_ip="35.123.45.67")

# Single backtest
result = client.run_backtest(
    ticker="AAPL",
    start_date="2020-01-01",
    end_date="2020-12-31"
)

print(f"Sharpe Ratio: {result['sharpe_ratio']:.3f}")
print(f"Cumulative Return: {result['cumulative_return']:.2%}")
print(f"Max Drawdown: {result['max_drawdown']:.2%}")
```

### Step 3.3: Batch Backtesting

```python
# All tickers
tickers = ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "TSLA"]

results = client.run_batch_backtests(
    tickers=tickers,
    start_date="2020-01-01",
    end_date="2020-12-31"
)

# Summary
client.print_summary(results)
```

---

## 🔄 PARTE 4: Workflow Ricorrente

### Classificazione Script

#### 🔵 Setup (Una Tantum)
```bash
scripts/gcp/setup_project.sh          # Setup GCP (1 volta)
scripts/gcp/create_buckets.sh         # Setup storage (1 volta)
scripts/gcp/setup_secrets.sh          # Setup API keys (1 volta)
scripts/gcp/deploy_fastapi_vm.sh      # Deploy backtesting VM (1 volta)
```

**Frequenza**: 1 volta all'inizio del progetto

---

#### 🟢 Training (Ricorrente Mensile)
```bash
scripts/download_data.py              # Download nuovi dati
scripts/train_rewts_llm_rl.py         # Training completo
scripts/gcp/create_training_vm.sh     # Crea VM training
scripts/gcp/build_and_push.sh         # Build Docker (se cambi codice)
```

**Frequenza**: 1 volta/mese
**Quando**:
- Inizio mese per includere dati mese precedente
- Performance degrada (Sharpe < 1.0)
- Nuovi ticker da aggiungere
- Major market events (crash, rally)

**Processo**:
1. Start training VM
2. Download latest data
3. Re-train models (18h)
4. Upload to GCS
5. Stop training VM
6. **Costo**: ~$8/run

---

#### 🟡 Live Strategy (Ricorrente Giornaliero/Orario)
```bash
scripts/get_live_strategy.py --ticker AAPL        # Strategia live
scripts/get_live_strategy.py --all               # Tutte strategie
```

**Frequenza**: Quanto vuoi!
- **Intraday trading**: Ogni ora
- **Swing trading**: 1 volta/giorno (pre-market)
- **Position trading**: 1 volta/settimana

**Quando**:
- Pre-market (8:00 AM): Strategia per giornata
- Intraday: Ogni ora per aggiustamenti
- Post-market: Review performance

**Costo**: ~$0.001/call (Gemini API)

---

#### 🟠 Backtesting (Ricorrente Settimanale)
```python
examples/backtesting_client_example.py   # Test performance
```

**Frequenza**: 1 volta/settimana
**Quando**:
- Fine settimana per review
- Dopo eventi market significativi
- Prima di deploy nuovi modelli

**Costo**: $0 (VM Spot fisso $3.72/mese)

---

#### 🔴 Monitoring (Continuo)
```bash
bash scripts/gcp/manage_fastapi_vm.sh status    # Check VM
bash scripts/gcp/manage_fastapi_vm.sh logs      # View logs
gcloud compute instances list                    # Check VMs
gcloud billing projects describe PROJECT_ID      # Check costs
```

**Frequenza**: Giornaliero/Continuo
**Quando**:
- Ogni giorno per check VMs running
- Se API non risponde
- Check costi settimanalmente

---

## 📅 Workflow Mensile Tipico

### Settimana 1: Training
```bash
# Lunedì
bash scripts/gcp/create_training_vm.sh
gcloud compute ssh rewts-training-spot --zone=us-central1-a

# In VM
python scripts/download_data.py
python scripts/train_rewts_llm_rl.py  # 18h
gsutil -m cp -r models/ gs://rewts-trading-data/models/

# Exit and stop VM
exit
gcloud compute instances stop rewts-training-spot --zone=us-central1-a
```

**Costo**: ~$8

### Settimana 2-4: Trading Live
```bash
# Ogni giorno pre-market (8:00 AM)
export GEMINI_API_KEY="your_key"
python scripts/get_live_strategy.py --all

# Review output, execute trades manualmente o automaticamente

# Weekend: Backtesting review
python examples/backtesting_client_example.py
```

**Costo**: ~$2 Gemini API (60 calls × $0.001)

### Fine Mese: Review & Prep
```bash
# Review performance
bash scripts/gcp/manage_fastapi_vm.sh logs

# Check costs
gcloud billing projects describe rewts-quant-trading

# Prepare for next training cycle
# Download any new fundamentals data sources
```

---

## 💰 Costi Ricorrenti Mensili

| Componente | Frequenza | Costo |
|------------|-----------|-------|
| Training VM | 1 run/mese (18h) | $8 |
| Backtesting VM Spot | Always-On | $3.72 |
| Storage | Continuo | $3 |
| Gemini API Live | 60 calls/giorno × 30 giorni | $50 |
| **TOTALE** | | **~$65/mese** |

**Ottimizzazioni**:
- Pre-computa strategie invece di live daily → save $45/mese
- Use cached strategies quando mercato stabile
- Training ogni 2 mesi invece di 1 → save $4/mese

---

## 🎯 Best Practices

### Training
1. ✅ Training **1 volta/mese** (inizio mese)
2. ✅ SEMPRE stop VM dopo training
3. ✅ Upload modelli a GCS prima di delete VM
4. ✅ Keep logs per debugging
5. ✅ Monitor GPU usage durante training

### Live Strategies
1. ✅ Pre-market call (8:00 AM) per daily strategies
2. ✅ Cache strategies per risparmiare API calls
3. ✅ Combine con technical analysis manuale
4. ✅ Don't overtrade (max 2-3 trades/day)
5. ✅ Review performance settimanalmente

### Backtesting
1. ✅ Weekly review (fine settimana)
2. ✅ Compare vs benchmark (S&P 500)
3. ✅ Track Sharpe Ratio (target >1.3)
4. ✅ Monitor Max Drawdown (target <30%)
5. ✅ Re-train se performance degrada

### Cost Control
1. ✅ Stop training VM dopo uso (IMPORTANTE!)
2. ✅ Monitor billing settimanalmente
3. ✅ Setup budget alerts a $100/mese
4. ✅ Use lifecycle policies per storage
5. ✅ Pre-compute strategie when possible

---

## 🚨 Troubleshooting

### Training VM Out of Memory
```yaml
# Edit configs/hybrid/rewts_llm_rl.yaml
rewts:
  batch_size: 32      # Reduce from 64
  buffer_size: 5000   # Reduce from 10000
```

### Gemini API Rate Limit
```python
# Add delay in get_live_strategy.py
import time
time.sleep(1)  # Between calls
```

### Backtesting VM Not Responding
```bash
bash scripts/gcp/manage_fastapi_vm.sh restart
bash scripts/gcp/manage_fastapi_vm.sh logs
```

### High Costs
1. Check running VMs: `gcloud compute instances list`
2. Stop unused training VMs
3. Reduce Gemini API calls (use caching)
4. Monitor: `gcloud billing projects describe PROJECT_ID`

---

## 📚 Summary

### Script Classification

| Script | Type | Frequency | Cost |
|--------|------|-----------|------|
| `setup_project.sh` | Setup | Once | $0 |
| `create_buckets.sh` | Setup | Once | $0 |
| `deploy_fastapi_vm.sh` | Setup | Once | $3.72/m |
| `train_rewts_llm_rl.py` | Recurring | 1/month | $8 |
| `get_live_strategy.py` | Recurring | Daily | $0.001/call |
| `backtesting_client_example.py` | Recurring | Weekly | $0 |
| `manage_fastapi_vm.sh` | Monitoring | As needed | $0 |

### Monthly Workflow
1. **Week 1**: Training (1 run, $8)
2. **Week 2-4**: Live strategies (daily, $50 API)
3. **Weekend**: Backtesting review ($0)
4. **Total**: ~$65/mese

### Key Points
- ✅ Training: 1 volta/mese (18h, $8)
- ✅ Live strategies: Daily/Hourly (instant, $0.001/call)
- ✅ Backtesting: Sempre disponibile ($3.72/mese fisso)
- ✅ Total: ~$65/mese per sistema completo

**Ottimo rapporto qualità/prezzo per trading quantitativo professionale!** 🚀
