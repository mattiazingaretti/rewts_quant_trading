# Quick Reference - Metriche e Threshold Comuni

## Metriche Tecniche - Threshold Chiave

### RSI (Relative Strength Index)
- `< 30`: **Ipervenduto** → possibile rimbalzo
- `30-70`: Range normale
- `> 70`: **Ipercomprato** → possibile correzione

### VIX (Volatility Index)
- `< 15`: Mercato calmo
- `15-25`: Volatilità normale
- `25-40`: Alta incertezza
- `> 40`: Panico estremo

### PMI (Purchasing Managers Index)
- `< 50`: Contrazione settore manifatturiero
- `= 50`: Neutrale
- `> 50`: Espansione settore
- `> 55`: Forte espansione

### Beta
- `< 1`: Meno volatile del mercato
- `= 1`: Allineato con mercato
- `> 1`: Più volatile del mercato

## Fondamentali - Range Salutari

### P/E Ratio
- `< 15`: Sottovalutato / economico
- `15-25`: Valutazione normale
- `> 25`: Sopravvalutato / aspettative crescita alte

### Debt-to-Equity
- `< 1`: Poco indebitata (safer)
- `1-2`: Livello accettabile
- `> 2`: Molto indebitata (risky)

### Current Ratio
- `< 1`: Problemi liquidità
- `1-2`: Liquidità sufficiente
- `> 2`: Ottima liquidità

### ROE (Return on Equity)
- `< 10%`: Rendimento modesto
- `10-15%`: Buono
- `> 15%`: Ottimo

### Gross Margin
- `< 20%`: Business a basso margine (retail)
- `20-50%`: Margini normali
- `> 50%`: Business molto profittevole (software)

## Performance Target (ReWTSE-LLM-RL)

### Sharpe Ratio
- `< 1`: Scarso
- `1-2`: Buono
- `> 2`: Eccellente
- **Target progetto**: 1.30-1.50

### Max Drawdown
- `< 10%`: Molto resiliente
- `10-20%`: Accettabile
- `> 30%`: Alto rischio
- **Target progetto**: 0.25-0.28 (25-28%)

## News Sentiment

### Sentiment Score
- `-1.0 a -0.5`: Molto negativo
- `-0.5 a 0`: Leggermente negativo
- `0`: Neutrale
- `0 a 0.5`: Leggermente positivo
- `0.5 a 1.0`: Molto positivo

### Impact Score (Likert Scale)
- `1`: Basso impatto
- `2`: Medio impatto
- `3`: Alto impatto

## Moving Average Crossovers

### Golden Cross (Bullish)
- `SMA_50` incrocia **sopra** `SMA_200`
- Segnale di acquisto forte

### Death Cross (Bearish)
- `SMA_50` incrocia **sotto** `SMA_200`
- Segnale di vendita forte

## MACD Signals

### Bullish
- MACD Line incrocia sopra Signal Line
- Histogram positivo e in crescita

### Bearish
- MACD Line incrocia sotto Signal Line
- Histogram negativo e in discesa

## Correlazione Metriche

### Risk-On Environment
- SPX in salita
- VIX basso (<15)
- Treasury Yields stabili
- GDP positivo
- PMI > 50
- CCI alto

### Risk-Off Environment
- SPX in discesa
- VIX alto (>25)
- Treasury Yields in calo (flight to safety)
- GDP negativo
- PMI < 50
- CCI basso

## Config Common Values

### Training
```yaml
chunk_length: 2016          # 14 giorni (2016 minuti)
episodes_per_chunk: 50      # Episodi training
batch_size: 64              # Batch size DDQN
learning_rate: 0.0001       # Learning rate
```

### Trading
```yaml
initial_balance: 10000      # Capital iniziale
transaction_cost: 0.001     # 0.1% per trade
```

### LLM
```yaml
temperature: 0.0            # Deterministico
llm_model: gemini-2.0-flash-exp
```

---

## Scripts Quick Commands

### 🔵 Setup (Una Tantum)
```bash
# Setup completo GCP
bash scripts/setup/01_setup_gcp_project.sh
bash scripts/setup/02_create_storage_buckets.sh
bash scripts/setup/03_setup_secrets.sh
bash scripts/setup/04_deploy_backtesting_vm.sh

# Verifica API keys
python scripts/setup/verify_api_keys.py
```

### 🟢 Training (Mensile)
```bash
# Download data
python scripts/training/download_data.py

# Training locale
python scripts/training/train_rewts_llm_rl.py

# Training su VM remoto con GPU
bash scripts/training/create_training_vm.sh
# SSH into VM, poi esegui download e training
```

### 🟠 Backtesting (Settimanale)
```bash
# Backtesting singolo ticker
python scripts/backtesting/backtest_ensemble.py

# Backtesting multi-ticker
python scripts/backtesting/backtest_multi_ticker.py

# Backtesting remoto su VM dedicata
python scripts/backtesting/run_remote_backtest.py
```

### 🟡 Live Strategies (Daily/Hourly)
```bash
# Get strategy per un ticker
python scripts/live/get_live_strategy.py --ticker AAPL

# Get strategies per tutti i ticker
python scripts/live/get_live_strategy.py --all

# Paper trading automatico (Alpaca)
python scripts/live/run_paper_trading.py
```

### 🔴 Monitoring (Continuo)
```bash
# Check costi GCP
bash scripts/monitoring/check_costs.sh

# VM management
bash scripts/utils/manage_vm.sh status    # Status VMs
bash scripts/utils/manage_vm.sh logs      # View logs
bash scripts/utils/manage_vm.sh ip        # Get IP address
bash scripts/utils/manage_vm.sh stop      # Stop VM
bash scripts/utils/manage_vm.sh start     # Start VM
```

---

## Workflow Mensile Tipico

### Week 1: Training (~18h, $8)
```bash
bash scripts/training/create_training_vm.sh
# SSH, download, train
```

### Week 2-4: Live Trading (daily, $0.001/call)
```bash
python scripts/live/get_live_strategy.py --all
```

### Weekend: Review (weekly, 10min, $0)
```bash
python scripts/backtesting/backtest_multi_ticker.py
bash scripts/monitoring/check_costs.sh
```

---

## Costi Stimati

| Operazione | Frequenza | Tempo | Costo |
|-----------|-----------|-------|-------|
| Setup GCP | Una tantum | 30 min | $0 |
| Training | Mensile | 18h | $8 |
| Live Strategy | Daily | Istantaneo | $0.001 |
| Backtesting | Settimanale | 10 min | $0 |
| Monitoring | Daily | 1 min | $0 |

**Costo mensile totale stimato**: ~$10-15/mese
