# Scripts Organization

Scripts organizzati per workflow. **Google Cloud non più necessario!**

---

## 📁 Struttura

```
scripts/
├── setup/              # 🔵 Setup iniziale (API keys)
├── training/           # 🟢 Training modelli (Google Colab o locale)
├── live/              # 🟡 Paper trading live (daily/hourly)
├── backtesting/       # 🟠 Backtesting e review
└── utils/             # 🔧 Utilities
```

---

## 🔵 setup/ - Setup Iniziale

**Quando**: All'inizio del progetto (1 volta)
**Tempo**: ~5 minuti
**Costo**: $0

```bash
python scripts/setup/verify_api_keys.py       # Verifica API keys
```

📖 [Leggi setup/README.md](setup/README.md)

---

## 🟢 training/ - Training Modelli

**Quando**: 1 volta/mese (inizio mese)
**Tempo**: ~2-3 ore (su Google Colab con GPU)
**Costo**: $0 (Colab gratuito con GPU)

**Opzione 1: Google Colab (Raccomandato)**
```bash
# Apri il notebook Colab:
# notebooks/train_rewts_complete.ipynb
# Esegui tutte le celle!
```

**Opzione 2: Locale**
```bash
python scripts/training/download_data.py       # Download dati
python scripts/training/train_rewts_llm_rl.py  # Train modelli
```

📖 [Leggi training/README.md](training/README.md)

---

## 🟡 live/ - Paper Trading Live

**Quando**: Ogni giorno o ogni ora
**Tempo**: Istantaneo
**Costo**: ~$0.001/call (Gemini API)

```bash
export GEMINI_API_KEY="your_key"
python scripts/live/get_live_strategy.py --ticker AAPL    # Single ticker
python scripts/live/get_live_strategy.py --all            # All tickers
python scripts/live/run_paper_trading.py                  # Paper trading con Alpaca
```

📖 [Leggi live/README.md](live/README.md)

---

## 🟠 backtesting/ - Review Performance

**Quando**: 1 volta/settimana (weekend)
**Tempo**: ~5-10 minuti
**Costo**: $0

```bash
python scripts/backtesting/backtest_ensemble.py         # Single ticker
python scripts/backtesting/backtest_multi_ticker.py     # All tickers
```

📖 [Leggi backtesting/README.md](backtesting/README.md)

---

## 📅 Workflow Mensile

### Week 1: Training su Google Colab
```bash
# Apri notebooks/train_rewts_complete.ipynb su Google Colab
# Esegui tutte le celle per:
# - Download dati
# - Generazione strategie LLM
# - Training ensemble DDQN
# - Backtesting
# - Salvataggio modelli su Google Drive
```

### Week 2-4: Live Trading
```bash
# Paper trading giornaliero
python scripts/live/run_paper_trading.py

# O strategie on-demand
python scripts/live/get_live_strategy.py --all
```

### Weekend: Review
```bash
# Backtest performance
python scripts/backtesting/backtest_multi_ticker.py
```

---

## 💡 Quick Start

### 1. Setup API Keys (5 min)
```bash
# Configura Gemini API key
export GEMINI_API_KEY="your_key_here"

# (Opzionale) Alpaca API per paper trading
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"

# Verifica
python scripts/setup/verify_api_keys.py
```

### 2. Training su Google Colab (2-3h)
```bash
# 1. Apri Google Colab: https://colab.research.google.com
# 2. Upload notebook: notebooks/train_rewts_complete.ipynb
# 3. Esegui tutte le celle
# 4. Modelli salvati automaticamente su Google Drive
```

### 3. Paper Trading (daily)
```bash
# Scarica modelli da Google Drive
# Esegui paper trading
python scripts/live/run_paper_trading.py
```

---

## 📚 Documentation

- **Complete Colab Notebook**: `notebooks/train_rewts_complete.ipynb`
- **Alpaca Paper Trading**: `../Alpaca_Paper_Trading_Guide.md`
- **Financial Metrics**: `../Financial_Metrics_Guide.md`
- **Hardware Requirements**: `../Hardware_Requirements.md`

---

## ⚠️ Note Importanti

- **No Google Cloud necessario**: Tutto il training può essere fatto su Google Colab gratuito
- **No VM deployment**: Non servono più script per VM e deployment cloud
- **Caching intelligente**: Le strategie LLM sono cachate per evitare chiamate API duplicate
- **Rate limiting automatico**: Rispetto automatico dei limiti API di Gemini
