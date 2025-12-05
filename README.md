# ReWTSE-LLM-RL: Hybrid Trading System

Sistema di trading ibrido che integra **ReWTSE** (ensemble temporale), **LLM Agents** (DeepSeek per strategia) e **RL Agents** (DDQN per esecuzione) per il trading algoritmico.

## Architettura

```
┌─────────────────────────────────────────────────────────┐
│            Strategist Agent (DeepSeek)                  │
│  - Genera strategie mensili (πg)                        │
│  - Input: Market data, Fundamentals, Analytics          │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────▼──────────────┐
         │  Analyst Agent (DeepSeek)│
         │  - Processa news          │
         │  - Genera segnali         │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────────────────┐
         │   ReWTSE Ensemble Controller         │
         │                                       │
         │  ┌─────────┐  ┌─────────┐  ┌──────┐ │
         │  │ DDQN_1  │  │ DDQN_2  │  │DDQN_C││
         │  │Chunk 1  │  │Chunk 2  │  │Chunk C││
         │  └─────────┘  └─────────┘  └──────┘ │
         │                                       │
         │  QP Weight Optimization (cvxopt)     │
         │  w* = argmin Σ ||y - Mw||²           │
         └───────────┬───────────────────────────┘
                     │
                     ▼
              Market Environment
```

## Caratteristiche Principali

- **LLM Agents con DeepSeek-V3**: Strategist e Analyst utilizzano DeepSeek per generazione strategie
- **ReWTSE Ensemble**: Specializzazione temporale tramite chunk-based training
- **DDQN Agents**: Esecuzione tattica delle decisioni di trading
- **QP Optimization**: Ottimizzazione dei pesi ensemble tramite programmazione quadratica
- **Multi-Modal Data**: Integrazione di market data, fundamentals, technical indicators, macro data e news

## Struttura del Progetto

```
.
├── src/
│   ├── llm_agents/           # LLM agents (DeepSeek)
│   │   ├── strategist_agent_deepseek.py
│   │   └── analyst_agent_deepseek.py
│   ├── rl_agents/            # RL agents (DDQN)
│   │   ├── ddqn_agent.py
│   │   └── trading_env.py
│   ├── trading/              # Alpaca paper trading integration
│   │   └── alpaca_paper_trader.py
│   ├── hybrid_model/         # ReWTSE ensemble
│   │   └── ensemble_controller.py
│   └── utils/                # Utilities
│       ├── data_utils.py
│       ├── rate_limiter.py
│       └── strategy_cache.py
├── scripts/
│   ├── setup/              # 🔵 Setup iniziale
│   │   ├── 02_create_storage_buckets.sh
│   │   └── verify_api_keys.py
│   ├── training/           # 🟢 Training modelli
│   │   ├── download_data.py
│   │   └── train_rewts_llm_rl.py
│   ├── live/               # 🟡 Paper trading live
│   │   ├── get_live_strategy.py
│   │   └── run_paper_trading.py
│   ├── backtesting/        # 🟠 Backtesting
│   │   ├── backtest_ensemble.py
│   │   ├── backtest_multi_ticker.py
│   │   └── backtest_utils.py
│   └── utils/              # 🔧 Utilities varie
│       └── regenerate_strategies.py
├── notebooks/                # Jupyter notebooks per training
│   ├── train_rewts_deepseek.ipynb
│   ├── train_rewts_complete.ipynb
│   └── train_rewts_llm_rl.ipynb
├── api/                      # FastAPI server
│   └── fastapi_server.py
├── configs/
│   └── hybrid/
│       └── rewts_llm_rl.yaml # Configurazione
├── data/
│   ├── raw/                  # Dati grezzi
│   ├── processed/            # Dati preprocessati
│   ├── llm_strategies/       # Strategie LLM pre-computate
│   └── cache/                # Cache dati
├── models/                   # Modelli salvati (.pkl, .pt)
├── results/
│   ├── metrics/              # Metriche performance
│   └── visualizations/       # Grafici
├── docs/
│   └── guides/               # Guide e documentazione
│       ├── Alpaca_Paper_Trading_Guide.md
│       └── ReWTSE-LLM-RL_Implementation_Guide.md
├── DEEPSEEK_INTEGRATION.md   # Guida integrazione DeepSeek
├── requirements.txt
└── README.md
```

## Setup e Installazione

### 1. Clone del Repository

```bash
cd /path/to/Papers
```

### 2. Crea Virtual Environment

```bash
python -m venv venv_rewts_llm
source venv_rewts_llm/bin/activate  # Linux/Mac
# venv_rewts_llm\Scripts\activate   # Windows
```

### 3. Installa Dipendenze

```bash
pip install -r requirements.txt
```

### 4. Configura API Keys

Crea un file `.env` nella root del progetto con le seguenti variabili:

```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ALPACA_KEY=your_alpaca_key_here
ALPACA_SECRET=your_alpaca_secret_here
```

**Come ottenere la DeepSeek API Key**:
1. Vai su https://platform.deepseek.com
2. Crea un account
3. Genera una nuova API key
4. Copia la key nel file `.env`

**Come ottenere le Alpaca API Keys** (per paper trading):
1. Vai su https://alpaca.markets
2. Crea un account paper trading (gratuito)
3. Genera le API keys
4. Copia key e secret nel file `.env`

### 5. Carica le API Keys nell'ambiente

```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key_here  # Linux/Mac
# set DEEPSEEK_API_KEY=your_deepseek_api_key_here   # Windows
```

## Utilizzo

Gli scripts sono organizzati per workflow e frequenza d'uso. Per una guida completa, consulta **[scripts/README.md](scripts/README.md)**.

### 🔵 Setup Iniziale

**Verifica API keys:**
```bash
python scripts/setup/verify_api_keys.py
```

### 🟢 Training

**Step 1: Download dei Dati**

```bash
python scripts/training/download_data.py
```

Scarica:
- Dati OHLCV da Yahoo Finance
- Indicatori tecnici (SMA, RSI, MACD, ATR)
- Dati SPX e VIX per context macro
- News mock (da sostituire con dati reali se disponibili)

**Step 2: Training del Sistema**

```bash
python scripts/training/train_rewts_llm_rl.py
```

Esegue:
1. Pre-computa le strategie LLM usando DeepSeek
2. Divide i dati in chunks temporali
3. Addestra un DDQN agent per ogni chunk
4. Salva l'ensemble di modelli

**Nota**: Il training può richiedere diverse ore. In alternativa, usa i notebooks su Google Colab:

```bash
# Apri notebooks/train_rewts_deepseek.ipynb su Colab
# Runtime → Change runtime type → GPU (T4)
# Inserisci DEEPSEEK_API_KEY quando richiesto
```

### 🟠 Backtesting

**Step 3: Backtesting**

```bash
python scripts/backtesting/backtest_ensemble.py
```

Esegue:
1. Carica l'ensemble addestrato
2. Esegue backtesting sul test set (30% dei dati)
3. Ottimizza i pesi ensemble dinamicamente
4. Calcola metriche di performance (Sharpe Ratio, Max Drawdown, Cumulative Return)
5. Genera visualizzazioni

**Backtesting multi-ticker:**
```bash
python scripts/backtesting/backtest_multi_ticker.py
```

### 🟡 Live Strategies

**Get strategie live per un singolo ticker:**
```bash
export DEEPSEEK_API_KEY="your_key"
python scripts/live/get_live_strategy.py --ticker AAPL
```

**Get strategie live per tutti i ticker:**
```bash
python scripts/live/get_live_strategy.py --all
```

**Paper Trading automatico (Alpaca):**
```bash
python scripts/live/run_paper_trading.py
```

### 🔧 Utilities

**Rigenera strategie LLM:**
```bash
python scripts/utils/regenerate_strategies.py
```

### Risultati

I risultati vengono salvati in:
- `results/metrics/summary_metrics.csv`: Metriche aggregate per tutti i ticker
- `results/visualizations/{ticker}_backtest.png`: Grafici di performance

## Configurazione

Il file `configs/hybrid/rewts_llm_rl.yaml` contiene tutti i parametri configurabili:

```yaml
llm:
  llm_model: "deepseek-chat"          # DeepSeek-V3
  temperature: 0.0                    # Temperature per generazione

rewts:
  chunk_length: 400                   # ~2 trading years
  lookback_length: 200                # ~1 trading year
  episodes_per_chunk: 100             # Episodi di training per chunk

trading_env:
  initial_balance: 10000              # Capital iniziale
  transaction_cost: 0.0015            # Costo transazione (0.15%)
  max_position: 0.95                  # Max 95% capital in position
  max_drawdown_limit: 0.15            # Stop trading at 15% drawdown
```

## 📚 Documentazione

### Guida Implementativa Completa

Per una guida dettagliata sull'architettura e implementazione del sistema:

**[docs/guides/ReWTSE-LLM-RL_Implementation_Guide.md](docs/guides/ReWTSE-LLM-RL_Implementation_Guide.md)**

### Paper Trading con Alpaca

Per testare strategie nel mondo reale con denaro fittizio (100% GRATUITO):

**[docs/guides/Alpaca_Paper_Trading_Guide.md](docs/guides/Alpaca_Paper_Trading_Guide.md)**

Include:
- Setup account Alpaca (5 minuti, GRATUITO)
- Configurazione API keys
- Trading automatico live con modello addestrato
- Esempi codice per trading manuale

### Integrazione DeepSeek

Per dettagli sull'integrazione con DeepSeek LLM:

**[DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md)**

Include:
- Confronto costi DeepSeek vs Gemini
- Setup API key
- Notebooks per training su Colab
- Token usage breakdown

## Metriche Target Attese

Basandosi sui risultati dei paper originali:

| Metrica | RL-only | LLM+RL | **ReWTSE-LLM-RL (target)** |
|---------|---------|--------|----------------------------|
| Sharpe Ratio (mean) | 0.64 | 1.10 | **1.30 - 1.50** |
| Max Drawdown (mean) | 0.36 | 0.31 | **0.25 - 0.28** |
| Robustezza outlier | Bassa | Media | **Alta** |

## Paper di Riferimento

- **ReWTSE Paper**: [https://arxiv.org/abs/2403.02150](https://arxiv.org/abs/2403.02150)
- **ReWTSE Repo**: [https://github.com/SINTEF/rewts](https://github.com/SINTEF/rewts)
- **LLM+RL Paper**: arXiv:2508.02366v1

## Componenti Riutilizzati

### Dal Repository ReWTS
- Chunk-based training framework
- QP Optimization (cvxopt)
- Configuration system (Hydra-compatible)

### Dal Paper LLM+RL
- Strategist Prompt (Listing 1)
- Analyst Prompt (Listing 2)
- DDQN Baseline architecture
- Feature Engineering multi-modale

## Troubleshooting

### Problema: Out of Memory durante training

**Soluzione**: Riduci `batch_size` e `buffer_size` in `configs/hybrid/rewts_llm_rl.yaml`

```yaml
rewts:
  batch_size: 32      # invece di 64
  buffer_size: 5000   # invece di 10000
```

### Problema: DeepSeek API rate limits

**Soluzione**: Il sistema include un rate limiter automatico in `src/utils/rate_limiter.py`. Se necessario, modifica `max_requests_per_second` in `configs/hybrid/rewts_llm_rl.yaml`:

```yaml
max_requests_per_second: 8.0  # Riduci se hai rate limits
```

### Problema: QP solver non converge

Il sistema usa automaticamente uniform weights come fallback in caso di problemi con la QP optimization.

## Estensioni Future

- **Reward Shaping**: Integrare segnali LLM nella reward function
- **Hierarchical ReWTSE**: Ensemble anche a livello LLM
- **Online Learning**: Incremental updates senza full retraining
- **Multi-Asset Portfolio**: Estensione a portfolio allocation
- **Real News Integration**: Sostituire mock news con API reali (Alpaca, Bloomberg)

## Licenza

Questo progetto è fornito "as-is" per scopi educativi e di ricerca.

## Contatti

Per domande o supporto, consultare:
- **[docs/guides/ReWTSE-LLM-RL_Implementation_Guide.md](docs/guides/ReWTSE-LLM-RL_Implementation_Guide.md)**: Guida implementativa completa
- **[DEEPSEEK_INTEGRATION.md](DEEPSEEK_INTEGRATION.md)**: Documentazione integrazione DeepSeek

---

**Nota**: Questo sistema è stato sviluppato per ricerca e sperimentazione. Non utilizzare per trading reale senza una validazione estensiva e comprensione dei rischi finanziari.
