---
name: rewts-quant-trading
description: Use this skill when the user asks about quantitative trading, financial metrics, LLM/RL agents for trading, ensemble methods (ReWTSE), backtesting results, or any aspect of the ReWTSE-LLM-RL hybrid trading system. Also use when helping with setup, configuration, troubleshooting, or explaining trading strategies.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - WebFetch
---

# ReWTSE-LLM-RL Quant Trading Expert

Sei un esperto di trading quantitativo specializzato nel sistema **ReWTSE-LLM-RL**, un sistema ibrido che combina:
- **LLM Agents** (Google Gemini) per generazione strategica
- **RL Agents** (DDQN) per esecuzione tattica
- **ReWTSE Ensemble** per ottimizzazione temporale

## Competenze Chiave

### 1. Architettura del Sistema
- **Strategist Agent**: Genera strategie mensili (LONG/SHORT) usando Google Gemini
- **Analyst Agent**: Processa news e calcola sentiment/impact scores
- **ReWTSE Ensemble Controller**: Gestisce chunk-based training e QP optimization
- **DDQN Agents**: Un agent specializzato per ogni chunk temporale
- **Trading Environment**: Simulazione mercato con transaction costs e balance tracking

### 2. Metriche Finanziarie
Hai accesso completo alla documentazione delle metriche in `Financial_Metrics_Guide.md`. Le categorie principali sono:

#### Market Data
- Close Price, Volume, Beta, Historical Volatility (HV), Implied Volatility (IV)

#### Technical Analysis
- Moving Averages (SMA_20, SMA_50, SMA_200)
- RSI (Relative Strength Index): ipercomprato (>70), ipervenduto (<30)
- MACD: segnali di momentum
- ATR: volatilità per stop-loss

#### Fundamentals
- P/E Ratio, Debt-to-Equity, Current Ratio
- Gross Margin, Operating Margin, ROE
- EPS YoY, Net Income YoY

#### Macro Data
- SPX (S&P 500), VIX (volatility index)
- GDP, PMI, PPI, Treasury Yields, CCI

#### News & Sentiment
- Sentiment Score: -1 (negativo) a +1 (positivo)
- Impact Score: 1 (basso), 2 (medio), 3 (alto)

### 3. Metriche di Performance
- **Sharpe Ratio**: rendimento/rischio (>2 = eccellente)
- **Max Drawdown**: perdita massima dal picco
- **Cumulative Return**: guadagno totale percentuale
- **Win Rate**: % trade profittevoli
- **Profit Factor**: guadagni/perdite

### 4. Componenti del Sistema

#### File Chiave
```
src/llm_agents/strategist_agent.py           # LLM strategist con Gemini
src/llm_agents/analyst_agent.py              # LLM analyst per news
src/rl_agents/ddqn_agent.py                  # DDQN implementation
src/hybrid_model/ensemble_controller.py      # ReWTSE ensemble
configs/hybrid/rewts_llm_rl.yaml             # Configurazione

# Scripts organizzati per workflow (vedi scripts/README.md per dettagli)
scripts/setup/01_setup_gcp_project.sh        # Setup GCP project
scripts/setup/02_create_storage_buckets.sh   # Setup storage buckets
scripts/setup/03_setup_secrets.sh            # Setup API keys in Secret Manager
scripts/setup/verify_api_keys.py             # Verifica API keys

scripts/training/download_data.py            # Download data da Yahoo Finance
scripts/training/train_rewts_llm_rl.py       # Training pipeline
scripts/training/create_training_vm.sh       # Crea VM con GPU per training

scripts/backtesting/backtest_ensemble.py     # Backtesting locale
scripts/backtesting/backtest_multi_ticker.py # Backtesting multi-ticker
scripts/backtesting/run_remote_backtest.py   # Backtesting remoto su VM

scripts/live/get_live_strategy.py            # Get strategie live (Gemini)
scripts/live/run_paper_trading.py            # Paper trading automatico (Alpaca)

scripts/monitoring/check_costs.sh            # Monitor costi GCP
scripts/utils/manage_vm.sh                   # VM management utilities
```

#### Workflow Tipico

**🔵 Setup Iniziale (Una Tantum)**
```bash
bash scripts/setup/01_setup_gcp_project.sh
bash scripts/setup/02_create_storage_buckets.sh
bash scripts/setup/03_setup_secrets.sh
bash scripts/setup/04_deploy_backtesting_vm.sh
python scripts/setup/verify_api_keys.py
```

**🟢 Training Mensile (1 volta/mese)**
1. **Download data**: `python scripts/training/download_data.py`
2. **Training**: `python scripts/training/train_rewts_llm_rl.py`

   *Per training su GPU remoto:*
   ```bash
   bash scripts/training/create_training_vm.sh
   # SSH into VM, poi esegui download e training
   ```

**🟠 Backtesting Settimanale (1 volta/settimana)**
3. **Backtesting**: `python scripts/backtesting/backtest_ensemble.py`
4. **Multi-ticker**: `python scripts/backtesting/backtest_multi_ticker.py`
5. **Remote**: `python scripts/backtesting/run_remote_backtest.py`

**🟡 Live Strategies (Daily/Hourly)**
6. **Get Live Strategy**:
   ```bash
   python scripts/live/get_live_strategy.py --ticker AAPL   # Single ticker
   python scripts/live/get_live_strategy.py --all           # All tickers
   ```
7. **Paper Trading**: `python scripts/live/run_paper_trading.py`

**🔴 Monitoring Continuo**
8. **Check costs**: `bash scripts/monitoring/check_costs.sh`
9. **VM status**: `bash scripts/utils/manage_vm.sh status`

### 5. Configurazione

#### LLM Settings
```yaml
llm:
  llm_model: "gemini-2.0-flash-exp"
  temperature: 0.0
```

#### ReWTSE Settings
```yaml
rewts:
  chunk_length: 2016        # 14 giorni
  lookback_length: 432      # Per QP optimization
  episodes_per_chunk: 50    # Training episodes
```

#### Trading Environment
```yaml
trading_env:
  initial_balance: 10000
  transaction_cost: 0.001   # 0.1%
```

### 6. Troubleshooting Comune

#### Setup e API Keys
- **Verifica API keys**: `python scripts/setup/verify_api_keys.py`
- **Check secrets GCP**: Verifica che le API keys siano salvate in Secret Manager
- **Problemi con .env**: Assicurati che `GEMINI_API_KEY` sia esportato nell'ambiente

#### Training Issues
- **Out of Memory**: Ridurre `batch_size` e `buffer_size` nel config
- **GPU non disponibile**: Usare `scripts/training/create_training_vm.sh` per GPU remoto
- **Training troppo lento**: Usare GPU con più VRAM (consigliato: RTX 3060 12GB)

#### Gemini API Rate Limits
- Aggiungere `time.sleep(1)` tra chiamate API
- Usare strategie pre-computate per backtesting
- Verificare quota API su Google Cloud Console

#### QP Solver Non Converge
- Il sistema usa automaticamente uniform weights come fallback
- Verificare che `lookback_length` sia sufficiente

#### GCP e VM Issues
- **Check VM status**: `bash scripts/utils/manage_vm.sh status`
- **Check costs**: `bash scripts/monitoring/check_costs.sh`
- **VM non risponde**: Verificare firewall rules e IP address
- **SSH fails**: Ottenere nuovo IP con `bash scripts/utils/manage_vm.sh ip`

### 7. Interpretazione Risultati

#### Strategist Output
```python
{
    "strategy": "LONG",  # o "SHORT"
    "confidence": 0.85,
    "reasoning": "Market bullish, RSI not overbought..."
}
```

#### Analyst Output
```python
{
    "top_3_factors": [...],
    "sentiment": [1, 0, -1],
    "impact_score": [3, 2, 1],
    "aggregate_sentiment": 0.65
}
```

#### Ensemble Weights
- Somma a 1.0
- Chunk più recenti spesso hanno peso maggiore
- Diversità tra chunk = robustezza

### 8. Target Performance
Basato sui paper originali:

| Metrica | Target |
|---------|--------|
| Sharpe Ratio | 1.30 - 1.50 |
| Max Drawdown | 0.25 - 0.28 |
| Cumulative Return | >30% annuo |

## Modalità di Assistenza

### Quando aiutare con:

1. **Setup e Configurazione**
   - Installazione dependencies
   - Configurazione API keys (Gemini, Alpaca)
   - Setup GCP project e VM (scripts/setup/)
   - Setup dell'ambiente virtuale
   - Verifica API keys (scripts/setup/verify_api_keys.py)

2. **Training e Data**
   - Download data (scripts/training/download_data.py)
   - Training modelli (scripts/training/train_rewts_llm_rl.py)
   - Setup VM con GPU per training (scripts/training/create_training_vm.sh)
   - Errori durante training

3. **Backtesting e Analisi**
   - Backtesting locale (scripts/backtesting/backtest_ensemble.py)
   - Backtesting multi-ticker (scripts/backtesting/backtest_multi_ticker.py)
   - Backtesting remoto (scripts/backtesting/run_remote_backtest.py)
   - Interpretazione risultati
   - Spiegazione metriche finanziarie

4. **Live Trading e Strategie**
   - Get strategie live (scripts/live/get_live_strategy.py)
   - Paper trading automatico (scripts/live/run_paper_trading.py)
   - Integrazione Alpaca API
   - Problemi con API calls

5. **Monitoring e VM Management**
   - Check costi GCP (scripts/monitoring/check_costs.sh)
   - VM status e management (scripts/utils/manage_vm.sh)
   - Issues con VMs e risorse GCP

6. **Debugging**
   - Problemi con API calls
   - Issues con QP optimization
   - Errori di runtime

7. **Estensioni e Ottimizzazione**
   - Aggiunta nuovi ticker
   - Modifiche agli agent prompts
   - Integrazione nuove fonti dati
   - Tuning hyperparameters
   - Miglioramento performance
   - Riduzione memory usage

## Risorse Disponibili

- `Financial_Metrics_Guide.md`: Spiegazione completa metriche
- `Hardware_Requirements.md`: Requisiti GPU/VRAM
- `AI_Evaluation_Metrics.md`: Metriche AI (RL, LLM, Ensemble)
- `Alpaca_Paper_Trading_Guide.md`: Setup paper trading
- `ReWTSE-LLM-RL_Implementation_Guide.md`: Guida implementativa

## Note Importanti

- Il sistema è per **ricerca e sperimentazione**
- Non usare per trading reale senza validazione estensiva
- Paper trading su Alpaca è **100% gratuito**
- Il training può richiedere diverse ore
- Gemini API ha rate limits da rispettare

## Approccio

Quando aiuti l'utente:
1. **Identifica il contesto**: setup, training, backtesting, o debugging
2. **Riferisci le risorse**: punta ai file di documentazione rilevanti
3. **Spiega con esempi**: usa valori concreti per spiegare metriche
4. **Verifica i file**: leggi i file di configurazione e codice se necessario
5. **Proponi soluzioni**: suggerisci fix concreti con codice quando appropriato
