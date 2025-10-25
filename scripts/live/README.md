# Live Strategy Scripts - Daily/Hourly

Scripts per ottenere strategie di trading in tempo reale dagli agent LLM.

**Frequenza**: Daily o Hourly
**Tempo**: Istantaneo (2-5 secondi)
**Costo**: ~$0.001/call

---

## 📋 Scripts

### `get_live_strategy.py`
Interroga Strategist + Analyst agents per strategie live.

**Cosa fa**:
1. Fetch latest market data (Yahoo Finance)
2. Fetch latest news (Yahoo Finance)
3. Strategist Agent: Analizza market + fundamentals
4. Analyst Agent: Analizza news + sentiment
5. Combina risultati → raccomandazione LONG/SHORT

**Output**:
- Recommendation: LONG or SHORT
- Confidence: 1.0-3.0 (Likert scale)
- Reasoning: Spiegazione dettagliata
- Key factors: Top 3 fattori da news
- Analyst sentiment: -1.0 to +1.0

---

## 🚀 Usage

### Single Ticker
```bash
export GEMINI_API_KEY="your_key_here"
python get_live_strategy.py --ticker AAPL
```

**Output**:
```
======================================================================
🤖 Getting LIVE Strategy for AAPL
======================================================================

📊 Fetching latest data for AAPL...
✅ Fetched 60 days of data

📰 Fetching latest news for AAPL...
✅ Fetched 10 news articles

📰 Analyst Agent: Processing news...
  Top Factors:
    1. 🟢 Apple announces new AI features (Impact: 3/3)
    2. ⚪ iPhone sales meet expectations (Impact: 2/3)
    3. 🔴 Regulatory concerns in EU (Impact: 2/3)

  Aggregate Sentiment: +0.42
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
  (+0.42) from AI announcements offsets regulatory concerns.

======================================================================
```

### Multiple Tickers
```bash
python get_live_strategy.py --tickers AAPL TSLA MSFT
```

### All Tickers (from config)
```bash
python get_live_strategy.py --all
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

======================================================================

✅ Strategies saved to live_strategies_20250125_143022.json
```

---

## 💻 Programmatic Usage

```python
from scripts.live.get_live_strategy import get_live_strategy
import os

# Set API key
os.environ['GEMINI_API_KEY'] = 'your_key_here'

# Get strategy
strategy = get_live_strategy('AAPL', verbose=True)

# Access results
print(f"Recommendation: {strategy['recommendation']}")  # LONG or SHORT
print(f"Confidence: {strategy['confidence']}")          # 1.0-3.0
print(f"Reasoning: {strategy['reasoning']}")
print(f"Current Price: ${strategy['current_price']}")
print(f"RSI: {strategy['rsi']}")

# Trading logic example
if strategy['recommendation'] == 'LONG' and strategy['confidence'] > 2.5:
    print("✅ Strong buy signal!")
    # Execute buy order...
elif strategy['recommendation'] == 'SHORT' and strategy['confidence'] > 2.5:
    print("⚠️ Strong sell signal!")
    # Execute sell order...
else:
    print("⏸️ Hold position - weak signal")
```

---

## 📅 When to Use

### Intraday Trading
```bash
# Every hour during market hours (9:30 AM - 4:00 PM)
# Cron: 0 9-16 * * 1-5
python get_live_strategy.py --ticker AAPL
```

**Frequency**: Every hour
**Cost**: 6.5 hours × 5 days × 4 weeks = 130 calls/month = **$0.13/month**

### Swing Trading (Recommended)
```bash
# Once per day pre-market (8:00 AM)
# Cron: 0 8 * * 1-5
python get_live_strategy.py --all
```

**Frequency**: Daily
**Cost**: 60 calls/month = **$0.06/month**

### Position Trading
```bash
# Once per week (Monday 8:00 AM)
# Cron: 0 8 * * 1
python get_live_strategy.py --all
```

**Frequency**: Weekly
**Cost**: 8 calls/month = **$0.008/month**

---

## 🎯 Trading Strategies

### Strategy 1: High Confidence Only
```python
strategy = get_live_strategy('AAPL')

if strategy['confidence'] >= 2.7:
    # Very high confidence - execute
    execute_trade(strategy['recommendation'])
elif strategy['confidence'] >= 2.0:
    # Medium confidence - smaller position
    execute_trade(strategy['recommendation'], size=0.5)
else:
    # Low confidence - skip
    pass
```

### Strategy 2: Sentiment + Confidence
```python
strategy = get_live_strategy('AAPL')

# Bullish: LONG recommendation + positive sentiment
if (strategy['recommendation'] == 'LONG' and
    strategy['analyst_sentiment'] > 0.3 and
    strategy['confidence'] > 2.3):
    execute_buy()

# Bearish: SHORT recommendation + negative sentiment
if (strategy['recommendation'] == 'SHORT' and
    strategy['analyst_sentiment'] < -0.3 and
    strategy['confidence'] > 2.3):
    execute_sell()
```

### Strategy 3: Technical Confirmation
```python
strategy = get_live_strategy('AAPL')

# LONG + RSI not overbought + above SMA_50
if (strategy['recommendation'] == 'LONG' and
    strategy['rsi'] < 70 and
    strategy['current_price'] > strategy.get('sma_50')):
    execute_buy()
```

---

## 💰 Cost Analysis

### Pricing
- **Gemini API**: $0.075 per 1M input tokens, $0.30 per 1M output tokens
- **Average call**: ~5K input + 1K output tokens
- **Cost per call**: ~$0.001

### Monthly Costs by Frequency

| Frequency | Calls/Month | Cost |
|-----------|-------------|------|
| Hourly (6.5h/day) | 130 | $0.13 |
| Daily (1/day) | 60 | $0.06 |
| Weekly (1/week) | 8 | $0.008 |

**Recommendation**: Daily è il sweet spot (sufficiente per swing trading, basso costo)

---

## 🔄 Caching Strategies

Per risparmiare costs, cache le strategie:

```python
import json
from datetime import datetime, timedelta
import os

CACHE_FILE = 'strategy_cache.json'
CACHE_DURATION = timedelta(hours=1)  # Cache for 1 hour

def get_cached_strategy(ticker):
    if not os.path.exists(CACHE_FILE):
        return None

    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

    if ticker in cache:
        cached_time = datetime.fromisoformat(cache[ticker]['timestamp'])
        if datetime.now() - cached_time < CACHE_DURATION:
            print(f"✅ Using cached strategy for {ticker}")
            return cache[ticker]

    return None

def cache_strategy(ticker, strategy):
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)

    cache[ticker] = strategy

    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2, default=str)

# Usage
cached = get_cached_strategy('AAPL')
if cached:
    strategy = cached
else:
    strategy = get_live_strategy('AAPL')
    cache_strategy('AAPL', strategy)
```

**Savings**: If market stable, 1 API call/hour instead of 1/call = 90% cost reduction

---

## 🚨 Troubleshooting

### "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your_key_here"
# Or add to ~/.bashrc or ~/.zshrc
```

### Rate Limit Error
Add delay between calls:
```python
import time
time.sleep(1)  # Wait 1 second between calls
```

Or reduce frequency (daily instead of hourly).

### "No news found"
Normal for low-volume stocks. Strategist will work with just market data.

### Wrong Recommendation
Remember:
- These are suggestions, not guarantees
- Always combine with your own analysis
- Consider multiple factors (technical, fundamental, macro)
- Use risk management (stop-loss, position sizing)

---

## 📚 Next Steps

After getting live strategies:
```bash
# Review backtesting performance
cd ../backtesting
python run_backtest.py

# Check costs
cd ../monitoring
bash check_costs.sh
```

Or read: `../../TRAINING_AND_LIVE_USAGE_GUIDE.md`
