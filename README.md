# ReWTSE-LLM-RL: Hybrid Trading System

Sistema di trading ibrido che integra **ReWTSE** (ensemble temporale), **LLM Agents** (Google Gemini per strategia) e **RL Agents** (DDQN per esecuzione) per il trading algoritmico.

## Architettura

```
┌─────────────────────────────────────────────────────────┐
│            Strategist Agent (Google Gemini)             │
│  - Genera strategie mensili (πg)                        │
│  - Input: Market data, Fundamentals, Analytics          │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Analyst Agent (Gemini) │
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

- **LLM Agents con Google Gemini 2.5 Flash**: Strategist e Analyst utilizzano Gemini invece di GPT-4o
- **ReWTSE Ensemble**: Specializzazione temporale tramite chunk-based training
- **DDQN Agents**: Esecuzione tattica delle decisioni di trading
- **QP Optimization**: Ottimizzazione dei pesi ensemble tramite programmazione quadratica
- **Multi-Modal Data**: Integrazione di market data, fundamentals, technical indicators, macro data e news

## Struttura del Progetto

```
.
├── src/
│   ├── llm_agents/           # LLM agents (Gemini)
│   │   ├── strategist_agent.py
│   │   └── analyst_agent.py
│   ├── rl_agents/            # RL agents (DDQN)
│   │   ├── ddqn_agent.py
│   │   └── trading_env.py
│   ├── trading/              # Alpaca paper trading integration
│   │   └── alpaca_paper_trader.py
│   └── hybrid_model/         # ReWTSE ensemble
│       └── ensemble_controller.py
├── scripts/
│   ├── download_data.py          # Download dataset
│   ├── train_rewts_llm_rl.py     # Training pipeline
│   ├── backtest_ensemble.py      # Backtesting
│   └── run_alpaca_paper_trading.py  # Paper trading live
├── configs/
│   └── hybrid/
│       └── rewts_llm_rl.yaml # Configurazione
├── data/
│   ├── raw/                  # Dati grezzi
│   ├── processed/            # Dati preprocessati
│   └── llm_strategies/       # Strategie LLM pre-computate
├── models/                   # Modelli salvati
├── results/
│   ├── metrics/              # Metriche performance
│   └── visualizations/       # Grafici
├── Financial_Metrics_Guide.md      # Guida metriche finanziarie
├── Hardware_Requirements.md        # Requisiti hardware (GPU/VRAM)
├── AI_Evaluation_Metrics.md        # Metriche valutazione AI
├── Alpaca_Paper_Trading_Guide.md   # Guida paper trading
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

Crea un file `.env` nella root del progetto:

```bash
cp .env.example .env
```

Modifica `.env` e aggiungi la tua **Google Gemini API Key**:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**Come ottenere la Gemini API Key**:
1. Vai su https://makersuite.google.com/app/apikey
2. Accedi con il tuo account Google
3. Crea una nuova API key
4. Copia la key nel file `.env`

### 5. Carica la API Key nell'ambiente

```bash
export GEMINI_API_KEY=your_actual_gemini_api_key_here  # Linux/Mac
# set GEMINI_API_KEY=your_actual_gemini_api_key_here   # Windows
```

## Utilizzo

### Step 1: Download dei Dati

```bash
python scripts/download_data.py
```

Questo script scarica:
- Dati OHLCV da Yahoo Finance
- Indicatori tecnici (SMA, RSI, MACD, ATR)
- Dati SPX e VIX per context macro
- News mock (da sostituire con dati reali se disponibili)

### Step 2: Training del Sistema

```bash
python scripts/train_rewts_llm_rl.py
```

Questo script:
1. Pre-computa le strategie LLM usando Google Gemini
2. Divide i dati in chunks temporali
3. Addestra un DDQN agent per ogni chunk
4. Salva l'ensemble di modelli

**Nota**: Il training può richiedere diverse ore a seconda del numero di ticker e chunk.

### Step 3: Backtesting

```bash
python scripts/backtest_ensemble.py
```

Questo script:
1. Carica l'ensemble addestrato
2. Esegue backtesting sul test set (30% dei dati)
3. Ottimizza i pesi ensemble dinamicamente
4. Calcola metriche di performance (Sharpe Ratio, Max Drawdown, Cumulative Return)
5. Genera visualizzazioni

### Risultati

I risultati vengono salvati in:
- `results/metrics/summary_metrics.csv`: Metriche aggregate per tutti i ticker
- `results/visualizations/{ticker}_backtest.png`: Grafici di performance

## Configurazione

Il file `configs/hybrid/rewts_llm_rl.yaml` contiene tutti i parametri configurabili:

```yaml
llm:
  llm_model: "gemini-2.0-flash-exp"  # Modello Gemini
  temperature: 0.0                    # Temperature per generazione

rewts:
  chunk_length: 2016                  # Lunghezza chunk (14 giorni)
  lookback_length: 432                # Look-back per QP optimization
  episodes_per_chunk: 50              # Episodi di training per chunk

trading_env:
  initial_balance: 10000              # Capital iniziale
  transaction_cost: 0.001             # Costo transazione (0.1%)
```

## 📚 Documentazione

### Guida alle Metriche Finanziarie

Per una spiegazione dettagliata e semplice di tutte le metriche utilizzate dagli agenti LLM:

**[Financial_Metrics_Guide.md](Financial_Metrics_Guide.md)**

Questo documento spiega in termini semplici:
- Dati di mercato (Close, Volume, Beta, HV, IV)
- Analisi tecnica (MA, RSI, MACD, ATR)
- Dati fondamentali (P/E, Debt-to-Equity, ROE, margins)
- Dati macro-economici (SPX, VIX, GDP, PMI, PPI, Treasury Yields)
- Metriche di performance (Sharpe Ratio, Max Drawdown, Cumulative Return)

### Requisiti Hardware

Per informazioni su GPU, VRAM e requisiti di sistema:

**[Hardware_Requirements.md](Hardware_Requirements.md)**

Include:
- Requisiti minimi, consigliati e ottimali
- Confronto GPU (CPU-only, 6GB, 12GB, 24GB VRAM)
- Tempi di training stimati
- Alternative cloud (Google Colab, AWS, Paperspace)
- Raccomandazione: **RTX 3060 12GB** (~€350) per miglior rapporto qualità/prezzo

### Metriche Valutazione AI

Per capire come vengono valutati i modelli AI (RL, LLM, Ensemble):

**[AI_Evaluation_Metrics.md](AI_Evaluation_Metrics.md)**

Include:
- Metriche Reinforcement Learning (Reward, Loss, Q-values, Epsilon)
- Metriche LLM (Confidence, Entropy, Direction Accuracy)
- Metriche Ensemble (Weight Distribution, QP Convergence, Diversity)
- Metriche Trading (Sharpe, Max Drawdown, Win Rate, Profit Factor)
- Metriche Generalizzazione (Cross-validation, Out-of-sample)

### Paper Trading con Alpaca

Per testare strategie nel mondo reale con denaro fittizio (100% GRATUITO):

**[Alpaca_Paper_Trading_Guide.md](Alpaca_Paper_Trading_Guide.md)**

Include:
- Setup account Alpaca (5 minuti, GRATUITO)
- Configurazione API keys
- Trading automatico live con modello addestrato
- Esempi codice per trading manuale
- Costo: **€0** (paper trading completamente gratuito)

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

### Problema: Gemini API rate limits

**Soluzione**: Aggiungi delay tra chiamate in `train_rewts_llm_rl.py`:

```python
import time
time.sleep(1)  # Pausa di 1 secondo tra chiamate
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
- **ReWTSE-LLM-RL_Implementation_Guide.md**: Guida implementativa completa
- **Financial_Metrics_Guide.md**: Spiegazione delle metriche finanziarie

---

**Nota**: Questo sistema è stato sviluppato per ricerca e sperimentazione. Non utilizzare per trading reale senza una validazione estensiva e comprensione dei rischi finanziari.
