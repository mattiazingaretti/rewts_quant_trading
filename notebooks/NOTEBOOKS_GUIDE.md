# Training Notebooks Guide

Due notebook per il training del sistema ReWTSE-LLM-RL, con supporto per diversi provider LLM.

---

## 📓 Notebook Disponibili

### 1. `train_rewts_complete.ipynb` (Gemini)

**LLM Provider**: Google Gemini 1.5 Flash
**Costo**: ~$0.09 per 6 tickers (con cache)
**Badge Colab**: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mattiazingaretti/rewts_quant_trading/blob/master/notebooks/train_rewts_complete.ipynb)

**API Key richiesta**: `GEMINI_API_KEY`
**Dove ottenerla**: https://makersuite.google.com/app/apikey

**Caratteristiche**:
- ✅ Provider raccomandato (più economico)
- ✅ API tier gratuito disponibile (15 req/min)
- ✅ Prompt caching (risparmi ~25%)
- ✅ Veloce (~2-3 ore per 6 tickers)

---

### 2. `train_rewts_deepseek.ipynb` (DeepSeek)

**LLM Provider**: DeepSeek-V3.2
**Costo**: ~$0.21 per 6 tickers (con cache)
**Badge Colab**: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mattiazingaretti/rewts_quant_trading/blob/master/notebooks/train_rewts_deepseek.ipynb)

**API Key richiesta**: `DEEPSEEK_API_KEY`
**Dove ottenerla**: https://platform.deepseek.com

**Caratteristiche**:
- ✅ Ragionamento più profondo
- ✅ Context caching (risparmi ~30%)
- ⚠️  2.2x più costoso di Gemini
- ✅ Velocità simile (~2-3 ore)

---

## 🔄 Confronto

| Feature | Gemini Flash | DeepSeek Chat |
|---------|--------------|---------------|
| **Costo (6 tickers)** | **$0.09** ✅ | $0.21 |
| **Costo annuale (12x)** | **$1.12** ✅ | $2.51 |
| **Free tier** | ✅ 15 req/min | ❌ Solo paid |
| **Context window** | 128K | 128K |
| **Cache support** | ✅ Prompt cache | ✅ Cache hit/miss |
| **Reasoning mode** | ❌ | ✅ (thinking mode) |
| **Function calling** | ✅ | ❌ |
| **Velocità** | Fast | Fast |

---

## 🚀 Quick Start

### Setup API Key (Una Volta)

**Opzione A: Colab Secrets (Raccomandato)** 🔑
```bash
1. Apri notebook su Colab
2. Click sull'icona 🔑 Secrets nella sidebar
3. Add new secret:
   - Name: GEMINI_API_KEY (o DEEPSEEK_API_KEY)
   - Value: tua API key
   - Enable "Notebook access"
4. Restart runtime
```

Vedi guida dettagliata: [`COLAB_SECRETS_SETUP.md`](COLAB_SECRETS_SETUP.md)

**Opzione B: Manual Input (Fallback)**
```bash
Il notebook chiederà la key con getpass
```

### Opzione 1: Gemini (Raccomandato)

```bash
# 1. Get API key: https://makersuite.google.com/app/apikey
# 2. Configure Colab Secret (vedi sopra) oppure skip
# 3. Open Colab: train_rewts_complete.ipynb
# 4. Run all cells
```

### Opzione 2: DeepSeek (Test A/B)

```bash
# 1. Get API key: https://platform.deepseek.com
# 2. Configure Colab Secret (vedi sopra) oppure skip
# 3. Open Colab: train_rewts_deepseek.ipynb
# 4. Run all cells
```

---

## 🧪 Test A/B Raccomandato

Per determinare quale LLM genera strategie migliori:

1. **Train con Gemini**:
   - Apri `train_rewts_complete.ipynb`
   - Modifica config: `'tickers': ['AAPL']`
   - Run all cells
   - Nota il Sharpe Ratio finale

2. **Train con DeepSeek**:
   - Apri `train_rewts_deepseek.ipynb`
   - Modifica config: `'tickers': ['AAPL']`
   - Run all cells
   - Nota il Sharpe Ratio finale

3. **Confronta**:
   - Se DeepSeek dà Sharpe **significativamente migliore** → vale i +$1.39/anno
   - Altrimenti → usa Gemini (più economico)

---

## 📋 Cosa Fanno i Notebook

Entrambi i notebook eseguono la stessa pipeline:

### 1. Setup (5 min)
- Environment detection (Colab/Local)
- GPU check
- Google Drive mount
- Repository clone
- Dependencies install

### 2. Data Download (5-10 min)
- Yahoo Finance: OHLCV, fundamentals
- Technical indicators: MA, RSI, MACD, ATR
- Mock news data
- Salvataggio in `data/processed/`

### 3. LLM Strategy Generation (30-60 min)
- **~110 strategie per ticker** (ogni 20 giorni)
- **Parallelo**: 8 workers concorrenti
- **Caching**: Evita chiamate API duplicate
- **Rate limiting**: Rispetta limiti API
- **Retry**: Exponential backoff su errori

### 4. RL Training (60-90 min)
- DDQN training su chunks temporali
- Ensemble di ~5 modelli per ticker
- QP weight optimization
- Salvataggio in `models/`

### 5. Backtesting (5 min)
- Valutazione su full dataset
- Metriche: Sharpe, Drawdown, Volatility, Win Rate
- Visualizzazioni

### 6. Save (1 min)
- Modelli → `models/`
- Google Drive → `/content/drive/MyDrive/rewts_models/`
- Strategie → `data/llm_strategies/`

**Tempo totale**: ~2-3 ore per 6 tickers

---

## 💾 Output

Dopo il training, trovi:

```
models/
├── AAPL_rewts_ensemble.pkl
├── GOOGL_rewts_ensemble.pkl
├── MSFT_rewts_ensemble.pkl
├── AMZN_rewts_ensemble.pkl
├── META_rewts_ensemble.pkl
└── TSLA_rewts_ensemble.pkl

data/llm_strategies/
├── AAPL_strategies.pkl
├── GOOGL_strategies.pkl
├── ...

/content/drive/MyDrive/rewts_models/  (su Colab)
├── AAPL_rewts_ensemble.pkl
├── ...
```

---

## 🔧 Personalizzazione

### Test Veloce (1 ticker, 20 min)

Modifica config in cella 9:

```python
config = {
    'tickers': ['AAPL'],  # Solo 1 ticker
    # ... resto invariato
}
```

### Training Completo (6 tickers, 2-3 ore)

```python
config = {
    'tickers': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA'],
    # ... resto invariato
}
```

### Custom Tickers

```python
config = {
    'tickers': ['NVDA', 'AMD', 'INTC'],  # Tech semicon
    # O:
    # 'tickers': ['JPM', 'BAC', 'WFC'],  # Finance
    # O:
    # 'tickers': ['XOM', 'CVX', 'COP'],  # Energy
}
```

---

## ⚠️ Troubleshooting

### "Rate limit exceeded"
- **Gemini free tier**: 15 req/min max
- **Soluzione**: Il notebook gestisce automaticamente con retry
- Oppure: Passa a paid tier o DeepSeek

### "API key invalid"
- Verifica che l'API key sia corretta
- Gemini: deve iniziare con `AIza...`
- DeepSeek: formato diverso

### "Out of memory" su Colab
- **Soluzione**: Usa GPU runtime (T4 gratuita)
- Runtime → Change runtime type → GPU

### Notebook si disconnette
- **Soluzione**: Checkpoint automatico ogni 10 strategie
- Riesegui cella strategy generation → riprende da dove era rimasto

---

## 📚 Documentazione Aggiuntiva

- **Implementation Guide**: `../docs/guides/ReWTSE-LLM-RL_Implementation_Guide.md`
- **Financial Metrics**: `../Financial_Metrics_Guide.md`
- **Paper Trading**: `../Alpaca_Paper_Trading_Guide.md`
- **Cost Analysis**: `../COLAB_MIGRATION_SUMMARY.md`

---

## 💡 Best Practices

1. **Inizia con 1 ticker** per test veloce
2. **Verifica API key** prima di training lungo
3. **Usa cache** per risparmiare su riesecuzioni
4. **Salva su Drive** per non perdere modelli
5. **Fai A/B test** Gemini vs DeepSeek per il tuo caso

---

**🎉 Happy Training!**
