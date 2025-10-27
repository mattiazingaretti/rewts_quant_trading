# DeepSeek Integration Summary

**Data**: 27 Ottobre 2025
**Obiettivo**: Aggiungere supporto DeepSeek-V3.2 come alternativa a Gemini per LLM agents

---

## ✅ File Creati

### 1. Agent DeepSeek

#### `src/llm_agents/strategist_agent_deepseek.py`
- **Purpose**: Strategist Agent usando DeepSeek API
- **Base**: OpenAI-compatible SDK (`openai` package)
- **Model**: `deepseek-chat` (DeepSeek-V3.2-Exp)
- **Features**:
  - Stesso prompt template del paper
  - JSON output mode
  - In-Context Memory (ICM)
  - Entropy-adjusted confidence

#### `src/llm_agents/analyst_agent_deepseek.py`
- **Purpose**: Analyst Agent per news processing
- **Base**: OpenAI-compatible SDK
- **Model**: `deepseek-chat`
- **Features**:
  - Top 3 factors extraction
  - Sentiment analysis (-1/0/+1)
  - Market impact scoring (1-3)
  - JSON output mode

### 2. Notebook Colab

#### `notebooks/train_rewts_deepseek.ipynb`
- **Purpose**: Training completo su Colab con DeepSeek
- **Differenze vs Gemini**:
  - API key: `DEEPSEEK_API_KEY`
  - Import: agent deepseek versions
  - Config: `llm_model: deepseek-chat`
  - Cost info: ~$0.21 per 6 tickers
- **Identico**: Tutto il resto (data, training, backtest)

### 3. Documentazione

#### `notebooks/NOTEBOOKS_GUIDE.md`
- **Purpose**: Guida ai due notebook (Gemini vs DeepSeek)
- **Content**:
  - Confronto costi e features
  - Quick start per entrambi
  - Test A/B workflow
  - Troubleshooting
  - Best practices

---

## 🔧 File Modificati

### 1. `requirements.txt`
**Aggiunto**:
```txt
openai>=1.0.0  # For DeepSeek (OpenAI-compatible)
```

Necessario per gli agent DeepSeek.

---

## 💰 Analisi Costi DeepSeek vs Gemini

### Pricing DeepSeek-V3.2

```
Input tokens (cache MISS): $0.28 / 1M
Input tokens (cache HIT):  $0.028 / 1M  (10x risparmio!)
Output tokens:             $0.42 / 1M
```

### Training 6 Tickers (660 chiamate)

| Scenario | Input | Output | Cache Hit | Total | vs Gemini |
|----------|-------|--------|-----------|-------|-----------|
| **No cache** | 0.726M | 0.231M | 0% | **$0.30** | +$0.18 (2.4x) |
| **Cache 50%** | 0.726M | 0.231M | 50% | **$0.21** | +$0.12 (2.2x) |
| **Cache 75%** | 0.726M | 0.231M | 75% | **$0.16** | +$0.07 (1.7x) |

### Gemini 1.5 Flash (confronto)

```
Input tokens:  $0.075 / 1M
Output tokens: $0.30 / 1M
Prompt cache:  $0.01875 / 1M (75% discount)
```

| Scenario | Total |
|----------|-------|
| **No cache** | **$0.12** |
| **Cache 75%** | **$0.09** |

### Confronto Annuale

Training mensile (12x/anno):

- **Gemini**: $1.12/anno
- **DeepSeek**: $2.51/anno
- **Differenza**: +$1.39/anno (poco rilevante)

---

## 🎯 Quando Usare Quale?

### Usa Gemini ✅
- Budget limitato
- Free tier sufficiente (15 req/min)
- Strategie già performanti
- Training frequente (>1x/mese)

### Usa DeepSeek 🧠
- Hai bisogno di ragionamento più profondo
- Vuoi testare se genera strategie migliori
- Budget non è problema (+$1.39/anno)
- Hai paid tier DeepSeek

### Test A/B 🧪
**Approccio raccomandato**:
1. Train AAPL con Gemini → nota Sharpe
2. Train AAPL con DeepSeek → nota Sharpe
3. Se DeepSeek > Gemini + 0.1-0.2 Sharpe → vale la differenza
4. Altrimenti → rimani con Gemini

---

## 🚀 Come Usare DeepSeek

### 1. Setup API Key

```bash
# Get key from: https://platform.deepseek.com
export DEEPSEEK_API_KEY="sk-..."
```

### 2. Opzione A: Notebook Colab (Raccomandato)

```bash
# 1. Open: notebooks/train_rewts_deepseek.ipynb
# 2. Runtime → Change runtime type → GPU (T4)
# 3. Enter DEEPSEEK_API_KEY when prompted
# 4. Run all cells
```

### 3. Opzione B: Script Locale

Modifica `configs/hybrid/rewts_llm_rl.yaml`:

```yaml
llm:
  llm_model: deepseek-chat
  deepseek_api_key: ${DEEPSEEK_API_KEY}
  temperature: 0.0
```

Poi usa script personalizzato:

```python
from src.llm_agents.strategist_agent_deepseek import StrategistAgent
from src.llm_agents.analyst_agent_deepseek import AnalystAgent

# ... resto del codice uguale
```

---

## 📊 Token Usage Breakdown

### Per strategia singola:

```
Input:  ~1,100 tokens
  - System prompt:    500
  - Market data:      200
  - Fundamentals:     100
  - Analytics:        150
  - Macro:            100
  - News:             50

Output: ~350 tokens
  - Direction/conf:   50
  - Explanation:      200
  - Features:         100
```

### Per 6 tickers (110 strategie/ticker):

```
Total calls: 660

Input:  660 × 1,100 = 726,000 tokens (0.726M)
Output: 660 × 350   = 231,000 tokens (0.231M)
Total:                957,000 tokens (0.957M)
```

### Costi per singolo ticker:

```
No cache:   $0.050
Cache 50%:  $0.035
Cache 75%:  $0.027
```

---

## 🔬 Caratteristiche Tecniche

### DeepSeek API

**Base URL**: `https://api.deepseek.com`
**SDK**: OpenAI-compatible (`openai` Python package)
**Authentication**: Bearer token (`DEEPSEEK_API_KEY`)

**Esempio request**:
```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-...",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[...],
    temperature=0.0,
    response_format={"type": "json_object"}
)
```

### Cache Behavior

DeepSeek implementa **prompt caching** simile a Gemini:

- **Cache HIT**: Se stesso prompt recente (entro 1 ora)
  - Costo: $0.028/1M (10x risparmio)
- **Cache MISS**: Nuovo prompt o oltre 1 ora
  - Costo: $0.28/1M (standard)

Il notebook con `StrategyCache` sfrutta questo:
- Prima esecuzione: cache misses
- Riesecuzioni: ~50-75% cache hits

---

## ⚙️ Configurazione Notebook

### Config cell (identica per entrambi):

```python
config = {
    'tickers': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA'],

    # Solo questa cambia per DeepSeek:
    'llm': {
        'llm_model': 'deepseek-chat',  # vs 'gemini-1.5-flash'
        'deepseek_api_key': os.getenv('DEEPSEEK_API_KEY'),
        'temperature': 0.0,
    },

    # Resto identico:
    'rewts': { ... },
    'trading_env': { ... },
    'parallel_workers': 8,
    'skip_news_processing': True
}
```

---

## 🧪 Test Eseguiti

### ✅ Validazione Codice

```bash
# Agent DeepSeek creati ✓
# Notebook creato ✓
# Sintassi Python validata ✓
# Import verificati ✓
```

### ⏳ Da Testare (utente)

```
□ Test reale su Colab
□ Verifica API key DeepSeek
□ Training 1 ticker (20-30 min)
□ Confronto Sharpe vs Gemini
□ Cache hit rate reale
```

---

## 📝 Checklist Deployment

### Per utente finale:

```bash
# 1. Get DeepSeek API key
□ Vai su https://platform.deepseek.com
□ Crea account
□ Genera API key

# 2. Test locale (opzionale)
□ pip install openai>=1.0.0
□ export DEEPSEEK_API_KEY="sk-..."
□ python test_deepseek_agent.py

# 3. Colab training
□ Open notebooks/train_rewts_deepseek.ipynb
□ Runtime → GPU (T4)
□ Enter DEEPSEEK_API_KEY
□ Run all cells
□ Attendi ~2-3 ore

# 4. Confronto
□ Confronta Sharpe con Gemini
□ Decide quale usare going forward
```

---

## 🔗 Risorse

### Documentazione
- **Notebook Guide**: `notebooks/NOTEBOOKS_GUIDE.md`
- **DeepSeek Docs**: https://platform.deepseek.com/docs
- **Pricing**: https://platform.deepseek.com/pricing
- **OpenAI SDK**: https://github.com/openai/openai-python

### File Progetto
- **Agent Strategist**: `src/llm_agents/strategist_agent_deepseek.py`
- **Agent Analyst**: `src/llm_agents/analyst_agent_deepseek.py`
- **Notebook DeepSeek**: `notebooks/train_rewts_deepseek.ipynb`
- **Notebook Gemini**: `notebooks/train_rewts_complete.ipynb`

---

## 💡 Best Practices

1. **Inizia con test su 1 ticker** (AAPL)
2. **Confronta subito con Gemini** sullo stesso ticker
3. **Misura Sharpe ratio difference** per decidere
4. **Se DeepSeek > +0.2 Sharpe** → vale i +$1.39/anno
5. **Monitora cache hit rate** nelle riesecuzioni

---

## 🎉 Summary

**Integrazione DeepSeek completata!**

✅ **Agent creati** (OpenAI-compatible)
✅ **Notebook pronto** per Colab
✅ **Documentazione** completa
✅ **Analisi costi** dettagliata
✅ **Test A/B workflow** definito

**Pronto per deployment e test reali!**

---

**Next steps**: Test utente su Colab con 1 ticker per validare integrazione.
