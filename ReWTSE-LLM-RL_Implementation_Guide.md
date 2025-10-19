# ReWTSE-LLM-RL: Guida di Implementazione

## Panoramica

Questa guida descrive l'implementazione di un'architettura ibrida che integra:
- **ReWTSE**: Ensemble temporalmente segmentato per la specializzazione dei modelli
- **LLM Agents**: Strategist e Analyst per guidance strategica
- **RL Agents (DDQN)**: Esecutori tattici delle decisioni di trading

## Architettura Proposta

```
┌─────────────────────────────────────────────────────┐
│              Strategist Agent (LLM)                 │
│  - Genera strategie mensili (πg)                    │
│  - Input: Market data, Fundamentals, Analytics      │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Analyst Agent (LLM)    │
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

---

## Repository e Codice Esistente

### Repository ReWTS
- **URL**: https://github.com/SINTEF/rewts
- **Componenti Riutilizzabili**:
  - `src/`: Framework per chunk-based training
  - `configs/`: Sistema di configurazione Hydra
  - Ottimizzazione QP con cvxopt
  - DataModule per time-series
  - Supporto multi-architettura (XGBoost, LSTM, TCN, Elastic Net)

### Repository LLM+RL
- **Baseline DDQN**: Implementazione disponibile nel paper
- **LLM Prompts**: Templates per Strategist e Analyst (vedi Appendix del paper)
- **Feature Engineering**: Dataset multi-modale completo

---

## Phase 1: Setup Ambiente

### 1.1 Installazione Dipendenze

```bash
# Clone del repository ReWTS
git clone https://github.com/SINTEF/rewts.git
cd rewts

# Crea virtual environment
python -m venv venv_rewts_llm
source venv_rewts_llm/bin/activate  # Linux/Mac
# venv_rewts_llm\Scripts\activate   # Windows

# Installa ReWTS e dipendenze
pip install -e .

# Installa dipendenze aggiuntive per LLM+RL
pip install openai anthropic
pip install gym stable-baselines3
pip install torch torchvision  # Se non già installato
pip install pandas numpy matplotlib seaborn
pip install yfinance alpaca-trade-api sec-api fredapi
pip install ta-lib  # Per technical indicators
```

### 1.2 Struttura Directory Proposta

```
rewts/
├── src/
│   ├── rewts/                    # Codice originale ReWTS
│   ├── llm_agents/               # NUOVO: LLM Agents
│   │   ├── __init__.py
│   │   ├── strategist_agent.py
│   │   └── analyst_agent.py
│   ├── rl_agents/                # NUOVO: RL Agents
│   │   ├── __init__.py
│   │   ├── ddqn_agent.py
│   │   └── trading_env.py
│   └── hybrid_model/             # NUOVO: Integrazione
│       ├── __init__.py
│       ├── rewts_llm_rl.py
│       └── ensemble_controller.py
├── configs/
│   ├── model/                    # Configs ReWTS esistenti
│   └── hybrid/                   # NUOVO: Configs ibridi
│       ├── rewts_llm_rl.yaml
│       └── experiment_config.yaml
├── data/
│   ├── raw/                      # Dati grezzi scaricati
│   ├── processed/                # Dati preprocessati
│   └── llm_strategies/           # Strategie LLM pre-computate
├── notebooks/
│   └── 01_prototype_single_ticker.ipynb
├── scripts/
│   ├── download_data.py
│   ├── train_chunk_models.py
│   └── backtest_ensemble.py
└── results/
    ├── metrics/
    └── visualizations/
```

---

## Phase 2: Data Preparation

### 2.1 Dataset Multi-Modale

Creare `scripts/download_data.py`:

```python
"""
Script per scaricare e preparare il dataset multi-modale
utilizzando le stesse fonti del paper LLM+RL
"""

import yfinance as yf
import pandas as pd
from fredapi import Fred
from alpaca_trade_api.rest import REST
import sec_api
from datetime import datetime, timedelta

class DataDownloader:
    def __init__(self, config):
        self.tickers = config['tickers']
        self.start_date = config['start_date']
        self.end_date = config['end_date']

        # API Keys (configurare in .env)
        self.fred = Fred(api_key=config['fred_api_key'])
        self.alpaca = REST(
            config['alpaca_key'],
            config['alpaca_secret'],
            base_url='https://data.alpaca.markets'
        )
        self.sec_api = sec_api.ExtractorApi(config['sec_api_key'])

    def download_market_data(self, ticker):
        """Scarica OHLCV + IV data"""
        # Price data da Yahoo Finance
        stock = yf.Ticker(ticker)
        df = stock.history(start=self.start_date, end=self.end_date)

        # Options IV (implied volatility)
        # Questo richiede iVolatility API o simili
        # Per semplicità, calcoliamo HV (historical vol) come proxy
        df['HV_Close'] = df['Close'].pct_change().rolling(20).std() * (252**0.5)

        # SPX e VIX per market context
        spx = yf.Ticker('^GSPC').history(start=self.start_date, end=self.end_date)
        vix = yf.Ticker('^VIX').history(start=self.start_date, end=self.end_date)

        df['SPX_Close'] = spx['Close']
        df['VIX_Close'] = vix['Close']

        return df

    def download_fundamentals(self, ticker):
        """Scarica fundamentals da Yahoo Finance e SEC"""
        stock = yf.Ticker(ticker)

        # Financial ratios
        info = stock.info
        fundamentals = {
            'PE_Ratio': info.get('trailingPE', None),
            'Debt_to_Equity': info.get('debtToEquity', None),
            'Current_Ratio': info.get('currentRatio', None),
            'ROE': info.get('returnOnEquity', None),
            'Gross_Margin': info.get('grossMargins', None),
            # ... altri ratios
        }

        # Quarterly financials
        quarterly = stock.quarterly_financials

        return fundamentals, quarterly

    def download_macro_data(self):
        """Scarica macroeconomic indicators da FRED"""
        macro_data = {}

        # GDP
        macro_data['GDP'] = self.fred.get_series('GDP',
                                                  start_date=self.start_date,
                                                  end_date=self.end_date)

        # PMI
        macro_data['PMI'] = self.fred.get_series('MANEMP',
                                                  start_date=self.start_date,
                                                  end_date=self.end_date)

        # Consumer Confidence
        macro_data['CCI'] = self.fred.get_series('CSCICP03USM665S',
                                                  start_date=self.start_date,
                                                  end_date=self.end_date)

        # 10Y Treasury Yield
        macro_data['T10Y'] = self.fred.get_series('DGS10',
                                                   start_date=self.start_date,
                                                   end_date=self.end_date)

        # PPI
        macro_data['PPI'] = self.fred.get_series('PPIACO',
                                                  start_date=self.start_date,
                                                  end_date=self.end_date)

        return pd.DataFrame(macro_data)

    def download_news(self, ticker):
        """Scarica news headlines da Alpaca"""
        news_data = []

        # Alpaca News API
        news = self.alpaca.get_news(ticker,
                                     start=self.start_date,
                                     end=self.end_date)

        for article in news:
            news_data.append({
                'timestamp': article.created_at,
                'headline': article.headline,
                'summary': article.summary,
                'source': article.source
            })

        return pd.DataFrame(news_data)

    def compute_technical_indicators(self, df):
        """Calcola technical indicators usando TA-Lib"""
        import talib

        # Moving Averages
        df['SMA_20'] = talib.SMA(df['Close'], timeperiod=20)
        df['SMA_50'] = talib.SMA(df['Close'], timeperiod=50)
        df['SMA_100'] = talib.SMA(df['Close'], timeperiod=100)
        df['SMA_200'] = talib.SMA(df['Close'], timeperiod=200)

        # RSI
        df['RSI'] = talib.RSI(df['Close'], timeperiod=14)

        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = talib.MACD(
            df['Close'],
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )

        # ATR
        df['ATR'] = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)

        # Slopes delle MA (usando diff)
        df['SMA_20_Slope'] = df['SMA_20'].diff()
        df['SMA_50_Slope'] = df['SMA_50'].diff()
        df['SMA_100_Slope'] = df['SMA_100'].diff()
        df['SMA_200_Slope'] = df['SMA_200'].diff()

        return df

    def prepare_full_dataset(self):
        """Combina tutti i dati in un dataset unificato"""
        datasets = {}

        for ticker in self.tickers:
            print(f"Processing {ticker}...")

            # Market data
            market_df = self.download_market_data(ticker)
            market_df = self.compute_technical_indicators(market_df)

            # Fundamentals
            fundamentals, quarterly = self.download_fundamentals(ticker)

            # News
            news_df = self.download_news(ticker)

            # Merge tutto in un DataFrame allineato per timestamp
            full_df = market_df.copy()

            # Aggiungi fundamentals (forward-fill per dati trimestrali)
            for key, value in fundamentals.items():
                full_df[key] = value

            # Salva
            datasets[ticker] = {
                'market': full_df,
                'news': news_df,
                'fundamentals': fundamentals
            }

            # Save to disk
            full_df.to_csv(f'data/processed/{ticker}_full_data.csv')
            news_df.to_csv(f'data/processed/{ticker}_news.csv')

        # Macro data (comune a tutti)
        macro_df = self.download_macro_data()
        macro_df.to_csv('data/processed/macro_data.csv')

        return datasets

if __name__ == '__main__':
    config = {
        'tickers': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'TSLA'],
        'start_date': '2012-01-01',
        'end_date': '2020-12-31',
        'fred_api_key': 'YOUR_FRED_KEY',
        'alpaca_key': 'YOUR_ALPACA_KEY',
        'alpaca_secret': 'YOUR_ALPACA_SECRET',
        'sec_api_key': 'YOUR_SEC_API_KEY'
    }

    downloader = DataDownloader(config)
    datasets = downloader.prepare_full_dataset()
    print("✓ Dataset preparation complete!")
```

---

## Phase 3: LLM Agents Implementation

### 3.1 Strategist Agent

Creare `src/llm_agents/strategist_agent.py`:

```python
"""
Strategist Agent: Genera strategie mensili di trading
Riutilizza i prompt dal paper LLM+RL (Listing 1)
"""

import openai
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np

@dataclass
class TradingStrategy:
    """Rappresenta una strategia generata dall'LLM"""
    direction: int  # 1 = LONG, 0 = SHORT
    confidence: float  # Likert 1-3
    strength: float  # entropy-adjusted confidence
    explanation: str
    features_used: List[Dict[str, any]]
    timestamp: str

class StrategistAgent:
    def __init__(self, config):
        self.model = config.get('llm_model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.0)
        self.seed = config.get('seed', 49)

        # Carica prompt template dal paper
        self.prompt_template = self._load_prompt_template()

        # In-Context Memory (ICM) per reflection
        self.memory_buffer = []

    def _load_prompt_template(self):
        """Carica il prompt P4 dal paper (Listing 1 in Appendix)"""
        # Questo è il prompt finale tuned dal paper
        # Lo riporto qui in forma condensata

        return """
User_Context:
Last_Strategy_Used_Data:
  last_returns: "{last_returns}"
  last_action: "{last_action}"
  Rationale: "{last_rationale}"

Stock_Data:
  General:
    Beta: {beta}
    Classification: {classification}

  Last_Weeks_Price:
    Close: {close}
    Volume: {volume}

  Weekly_Past_Returns: {weekly_returns}

  Historical_Volatility:
    HV_Close: {hv_close}

  Implied_Volatility:
    IV_Close: {iv_close}

Fundamental_Data:
  Ratios:
    Current_Ratio: {current_ratio}
    Debt_to_Equity_Ratio: {debt_to_equity}
    PE_Ratio: {pe_ratio}

  Margins:
    Gross_Margin: {gross_margin}
    Operating_Margin: {operating_margin}

  Growth_Metrics:
    EPS_YoY: {eps_yoy}
    Net_Income_YoY: {net_income_yoy}

Technical_Analysis:
  Moving_Averages:
    20MA: {ma_20}
    50MA: {ma_50}
    200MA: {ma_200}

  MA_Slopes:
    20MA_Slope: {ma_20_slope}
    50MA_Slope: {ma_50_slope}

  MACD:
    Value: {macd}
    Signal_Line: {macd_signal}

  RSI:
    Value: {rsi}

  ATR: {atr}

Macro_Data:
  Macro_Indices:
    SPX:
      Close: {spx_close}
      Close_Slope: {spx_slope}
    VIX:
      Close: {vix_close}
      Close_Slope: {vix_slope}

  Economic_Data:
    GDP_QoQ: {gdp_qoq}
    PMI: {pmi}
    PPI_YoY: {ppi_yoy}
    Treasury_Yields_YoY: {treasury_yoy}

News_Sentiment: {news_sentiment}
News_Impact_Score: {news_impact}

System_Context:
Persona: You are an expert quantitative trading strategist with deep knowledge
         of technical analysis, fundamental valuation, and market microstructure.

Portfolio_Objectives: Maximize risk-adjusted returns while maintaining capital
                       preservation during market downturns.

Instructions:
Develop a LONG or SHORT trading strategy for the next month. Follow these steps:

1. Stock Analysis:
   - Compare Close price against moving averages (20MA, 50MA, 200MA)
   - Analyze Weekly_Past_Returns for trend sustainability
   - Use HV_Close and IV_Close to assess volatility regime

2. Technical Analysis:
   - RSI: >70 overbought, <30 oversold
   - MACD: Crossovers indicate momentum shifts
   - MA slopes: Steep positive = bullish, steep negative = bearish

3. Fundamental Analysis:
   - Growth metrics (EPS_YoY, Net_Income_YoY) for profitability trends
   - Ratios (Debt_to_Equity, Current_Ratio) for financial health

4. Macro Analysis:
   - SPX_Close_Slope > 0 && VIX_Close_Slope < 0: Bullish (Risk-On)
   - SPX_Close_Slope < 0 && VIX_Close_Slope > 0: Bearish (Risk-Off)
   - GDP_QoQ > 0 && PMI > 50: Economic expansion

5. News Analysis:
   - Use News_Sentiment (-1, 0, +1) and News_Impact_Score (1-3)
   - High impact news (score=3) can override other signals

6. Performance Reflection:
   - Review Last_Strategy_Used_Data
   - Assess whether last_action led to positive last_returns
   - Do NOT copy previous rationale; learn from its outcome

Output (JSON format):
{
  "action": "LONG" or "SHORT",
  "action_confidence": 1-3 (Likert scale),
  "explanation": "Max 350 words rationale",
  "features_used": [
    {"feature": "Stock_Data.Close", "direction": "LONG/SHORT", "weight": 1-3},
    ...
  ]
}
"""

    def generate_strategy(
        self,
        market_data: Dict,
        fundamentals: Dict,
        analytics: Dict,
        macro_data: Dict,
        news_signals: Dict,
        last_strategy: TradingStrategy = None
    ) -> TradingStrategy:
        """
        Genera una strategia di trading mensile

        Args:
            market_data: OHLCV, IV, HV
            fundamentals: Ratios, margins, growth
            analytics: Technical indicators
            macro_data: SPX, VIX, economic indicators
            news_signals: Sentiment e impact score dall'Analyst Agent
            last_strategy: Strategia precedente per ICM reflection

        Returns:
            TradingStrategy object
        """

        # Prepara i dati per il prompt
        prompt_data = self._prepare_prompt_data(
            market_data, fundamentals, analytics,
            macro_data, news_signals, last_strategy
        )

        # Formatta il prompt
        prompt = self.prompt_template.format(**prompt_data)

        # Chiamata all'LLM
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a quantitative trading strategist."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            seed=self.seed,
            response_format={"type": "json_object"}
        )

        # Parse response
        import json
        strategy_json = json.loads(response.choices[0].message.content)

        # Calcola entropy-adjusted confidence (come nel paper)
        logprobs = response.choices[0].logprobs  # Se disponibile
        entropy = self._calculate_entropy(logprobs) if logprobs else 0.5

        confidence_score = strategy_json['action_confidence'] / 3.0  # Normalize to [0,1]
        certainty = 0.01 + (1 - 0.01) * (1 - entropy)  # ε + (1-ε)(1-H)
        strength = confidence_score * certainty

        # Crea TradingStrategy
        strategy = TradingStrategy(
            direction=1 if strategy_json['action'] == 'LONG' else 0,
            confidence=strategy_json['action_confidence'],
            strength=strength,
            explanation=strategy_json['explanation'],
            features_used=strategy_json['features_used'],
            timestamp=market_data['timestamp']
        )

        # Aggiungi a memory buffer per future reflections
        self.memory_buffer.append(strategy)
        if len(self.memory_buffer) > 10:  # Keep last 10 strategies
            self.memory_buffer.pop(0)

        return strategy

    def _prepare_prompt_data(self, market_data, fundamentals, analytics,
                            macro_data, news_signals, last_strategy):
        """Helper per formattare i dati nel formato del prompt"""

        data = {}

        # Last strategy (per ICM)
        if last_strategy:
            data['last_returns'] = last_strategy.get('returns', 'N/A')
            data['last_action'] = 'LONG' if last_strategy.direction == 1 else 'SHORT'
            data['last_rationale'] = last_strategy.explanation
        else:
            data['last_returns'] = 'N/A'
            data['last_action'] = 'N/A'
            data['last_rationale'] = 'N/A'

        # Market data
        data['close'] = market_data.get('Close', 0)
        data['volume'] = market_data.get('Volume', 0)
        data['weekly_returns'] = market_data.get('Weekly_Returns', [])
        data['hv_close'] = market_data.get('HV_Close', 0)
        data['iv_close'] = market_data.get('IV_Close', 0)
        data['beta'] = market_data.get('Beta', 1.0)
        data['classification'] = market_data.get('Classification', 'Growth')

        # Fundamentals
        data.update(fundamentals)

        # Analytics
        data.update(analytics)

        # Macro
        data['spx_close'] = macro_data.get('SPX_Close', 0)
        data['spx_slope'] = macro_data.get('SPX_Slope', 0)
        data['vix_close'] = macro_data.get('VIX_Close', 0)
        data['vix_slope'] = macro_data.get('VIX_Slope', 0)
        data.update({k: v for k, v in macro_data.items()
                    if k.startswith(('GDP', 'PMI', 'PPI', 'Treasury'))})

        # News
        data['news_sentiment'] = news_signals.get('sentiment', 0)
        data['news_impact'] = news_signals.get('impact_score', 1)

        return data

    def _calculate_entropy(self, logprobs):
        """Calcola entropy normalizzata dai logprobs"""
        if not logprobs:
            return 0.5

        # Top-k approximation come nel paper (eq. 5)
        probs = [np.exp(lp) for lp in logprobs['token_logprobs'][:10]]  # top-10
        probs_sum = sum(probs)
        probs = [p / probs_sum for p in probs]

        entropy = -sum([p * np.log(p) if p > 0 else 0 for p in probs])
        max_entropy = np.log(len(probs))

        return entropy / max_entropy if max_entropy > 0 else 0.5
```

### 3.2 Analyst Agent

Creare `src/llm_agents/analyst_agent.py`:

```python
"""
Analyst Agent: Processa news e genera segnali direzionali
Riutilizza il prompt dal paper LLM+RL (Listing 2)
"""

import openai
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class NewsFactor:
    factor: str
    sentiment: int  # -1, 0, +1
    market_impact: int  # 1-3 (Likert)

class AnalystAgent:
    def __init__(self, config):
        self.model = config.get('llm_model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.7)

        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self):
        """Carica prompt Analyst dal paper (Listing 2)"""

        return """
User_Context:
Monthly_News_Articles_List:
{articles_list}

System_Context:
Persona: Financial Market Analyst

Instructions:
Extract the Top 3 news factors influencing stock price movements from the
Monthly_News_Articles_List. Follow these steps:

1. Rank news by relevance to stock price movements:
   - Prioritize significant financial or market impacts (e.g., acquisitions,
     partnerships, guidance revisions)
   - Weigh industry trends, macroeconomic influences, analyst ratings based on
     expected effect on company valuation
   - News with broad or long-term implications rank higher

2. Summarize content into key factors and corporate events affecting stock prices,
   using concise language and causal relationships

3. For each factor, assign:
   - Sentiment: +1 for positive, -1 for negative, 0 for neutral/mixed
   - Market_Impact_Score: Likert scale 1-3
     * 1 = minimal relevance
     * 2 = moderate influence
     * 3 = high impact driver

Examples of factors:
- Strategic partnerships or competitor activity
- Industry trends or macroeconomic influences
- Product launches or market expansions
- Analyst ratings, significant stock price moves
- Corporate events: guidance revisions, acquisitions, contracts

Output (JSON format):
{
  "factors": [
    {
      "factor": "Summary of news (max 70 words)",
      "sentiment": -1/0/+1,
      "market_impact": 1-3
    },
    ...
  ]
}
"""

    def process_news(self, news_articles: List[Dict]) -> Dict:
        """
        Processa una lista di news articles e genera fattori strutturati

        Args:
            news_articles: Lista di dict con keys 'timestamp', 'headline', 'summary'

        Returns:
            Dict con 'factors', 'aggregate_sentiment', 'aggregate_impact'
        """

        # Anonimizza le news (per evitare memorization)
        anonymized_articles = self._anonymize_articles(news_articles)

        # Formatta nel prompt
        articles_text = "\n\n".join([
            f"Article {i+1}:\n{art['headline']}\n{art.get('summary', '')}"
            for i, art in enumerate(anonymized_articles)
        ])

        prompt = self.prompt_template.format(articles_list=articles_text)

        # LLM call
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a financial market analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        # Parse
        import json
        factors_json = json.loads(response.choices[0].message.content)

        # Aggrega sentiment e impact
        factors = [NewsFactor(**f) for f in factors_json['factors']]

        aggregate_sentiment = sum([f.sentiment * f.market_impact for f in factors])
        aggregate_sentiment = max(-1, min(1, aggregate_sentiment / len(factors)))

        aggregate_impact = max([f.market_impact for f in factors])

        return {
            'factors': factors,
            'sentiment': aggregate_sentiment,
            'impact_score': aggregate_impact
        }

    def _anonymize_articles(self, articles: List[Dict]) -> List[Dict]:
        """Anonimizza named entities per evitare memorization"""
        # Semplice implementazione: rimuovi ticker symbols e company names
        # In produzione, usare NER più sofisticato

        anonymized = []
        for art in articles:
            anon_art = art.copy()
            # Placeholder: sostituisci ticker con "the Company"
            # Qui servirebbe un NER model o regex più robusto
            anon_art['headline'] = art['headline']  # TODO: implementare anonymization
            anonymized.append(anon_art)

        return anonymized
```

---

## Phase 4: RL Agent (DDQN) Integration

### 4.1 Trading Environment

Creare `src/rl_agents/trading_env.py`:

```python
"""
Trading Environment per RL Agent
Estende il benchmark environment del paper LLM+RL
"""

import gym
from gym import spaces
import numpy as np
import pandas as pd

class TradingEnv(gym.Env):
    """
    Custom Trading Environment per DDQN

    Observation Space: price features + technical indicators + LLM signal (τ)
    Action Space: [0: SHORT, 1: HOLD, 2: LONG]
    Reward: Differenza nei rendimenti del portafoglio
    """

    metadata = {'render.modes': ['human']}

    def __init__(self, df, llm_strategies, config):
        super(TradingEnv, self).__init__()

        self.df = df.reset_index(drop=True)
        self.llm_strategies = llm_strategies  # Pre-computed LLM strategies
        self.config = config

        # Parametri
        self.initial_balance = config.get('initial_balance', 10000)
        self.transaction_cost = config.get('transaction_cost', 0.001)  # 0.1%
        self.max_position = config.get('max_position', 1.0)  # No leverage

        # State
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # -1: SHORT, 0: HOLD, 1: LONG
        self.shares_held = 0
        self.portfolio_value = self.initial_balance

        # Observation space
        # Features: Close, Volume, HV, technical indicators, LLM signal τ
        num_features = len(self._get_observation(0))
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(num_features,),
            dtype=np.float32
        )

        # Action space: [SHORT, HOLD, LONG]
        self.action_space = spaces.Discrete(3)

        # Tracking
        self.portfolio_history = []

    def _get_observation(self, step):
        """Costruisce observation vector includendo LLM signal τ"""

        row = self.df.iloc[step]

        # Price features (normalized)
        close = row['Close']
        volume = row['Volume']
        hv = row['HV_Close']

        # Technical indicators
        sma_20 = row['SMA_20']
        sma_50 = row['SMA_50']
        sma_200 = row['SMA_200']
        rsi = row['RSI']
        macd = row['MACD']

        # LLM signal τ = dir(πg) * str(πg)
        # Ottieni strategia LLM corrente (mensile)
        month_idx = step // 20  # Strategia mensile (20 trading days)
        if month_idx < len(self.llm_strategies):
            strategy = self.llm_strategies[month_idx]
            direction = 2 * strategy.direction - 1  # {0,1} -> {-1,1}
            strength = strategy.strength
            tau = direction * strength
        else:
            tau = 0.0

        # Portfolio state
        portfolio_value = self._get_portfolio_value(step)

        # Normalizzazione
        obs = np.array([
            close / 100.0,  # Normalize price
            volume / 1e6,
            hv * 100,
            sma_20 / close if close > 0 else 0,
            sma_50 / close if close > 0 else 0,
            sma_200 / close if close > 0 else 0,
            rsi / 100.0,
            macd,
            tau,  # LLM guidance signal
            portfolio_value / self.initial_balance,
            self.position  # Current position
        ], dtype=np.float32)

        return obs

    def _get_portfolio_value(self, step):
        """Calcola portfolio value corrente"""
        current_price = self.df.iloc[step]['Close']
        return self.balance + self.shares_held * current_price

    def reset(self):
        """Reset environment"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.shares_held = 0
        self.portfolio_value = self.initial_balance
        self.portfolio_history = []

        return self._get_observation(0)

    def step(self, action):
        """
        Execute action

        Actions:
          0: SHORT (sell if holding, or go short)
          1: HOLD (no action)
          2: LONG (buy if not holding)
        """

        current_price = self.df.iloc[self.current_step]['Close']

        # Execute trade
        if action == 0:  # SHORT
            if self.position == 1:  # Close LONG position
                revenue = self.shares_held * current_price * (1 - self.transaction_cost)
                self.balance += revenue
                self.shares_held = 0
                self.position = 0

        elif action == 2:  # LONG
            if self.position == 0:  # Open LONG position
                max_shares = self.balance / current_price
                shares_to_buy = int(max_shares * self.max_position)
                cost = shares_to_buy * current_price * (1 + self.transaction_cost)

                if cost <= self.balance:
                    self.shares_held += shares_to_buy
                    self.balance -= cost
                    self.position = 1

        # else: HOLD (action == 1), no action

        # Move to next step
        self.current_step += 1

        # Calculate reward (portfolio value change)
        new_portfolio_value = self._get_portfolio_value(self.current_step)
        reward = (new_portfolio_value - self.portfolio_value) / self.portfolio_value
        self.portfolio_value = new_portfolio_value

        # Track history
        self.portfolio_history.append(self.portfolio_value)

        # Check if done
        done = self.current_step >= len(self.df) - 1

        # Next observation
        obs = self._get_observation(self.current_step) if not done else np.zeros(self.observation_space.shape)

        return obs, reward, done, {}

    def render(self, mode='human'):
        """Visualizza stato corrente"""
        print(f"Step: {self.current_step}, Portfolio Value: ${self.portfolio_value:.2f}, Position: {self.position}")
```

### 4.2 DDQN Agent

Creare `src/rl_agents/ddqn_agent.py`:

```python
"""
DDQN Agent per trading
Implementazione basata sul paper benchmark [Theate & Ernst 2021]
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random

class DQN(nn.Module):
    """Deep Q-Network"""

    def __init__(self, input_dim, output_dim, hidden_dims=[128, 64]):
        super(DQN, self).__init__()

        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class ReplayBuffer:
    """Experience Replay Buffer"""

    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(states),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(next_states),
            torch.FloatTensor(dones)
        )

    def __len__(self):
        return len(self.buffer)

class DDQNAgent:
    """Double DQN Agent"""

    def __init__(self, state_dim, action_dim, config):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config

        # Hyperparameters
        self.gamma = config.get('gamma', 0.99)
        self.epsilon = config.get('epsilon_start', 1.0)
        self.epsilon_min = config.get('epsilon_min', 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.learning_rate = config.get('learning_rate', 1e-3)
        self.batch_size = config.get('batch_size', 64)
        self.target_update_freq = config.get('target_update_freq', 10)

        # Networks
        hidden_dims = config.get('hidden_dims', [128, 64])
        self.policy_net = DQN(state_dim, action_dim, hidden_dims)
        self.target_net = DQN(state_dim, action_dim, hidden_dims)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)

        # Replay buffer
        buffer_size = config.get('buffer_size', 10000)
        self.replay_buffer = ReplayBuffer(buffer_size)

        # Training state
        self.steps_done = 0
        self.episode_count = 0

    def select_action(self, state, explore=True):
        """ε-greedy action selection"""

        if explore and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def train_step(self):
        """Single training step usando experience replay"""

        if len(self.replay_buffer) < self.batch_size:
            return None

        # Sample batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        # Compute Q(s_t, a)
        q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Compute V(s_{t+1}) usando Double DQN
        with torch.no_grad():
            # Azione selezionata dalla policy net
            next_actions = self.policy_net(next_states).argmax(1)
            # Q-value dalla target net
            next_q_values = self.target_net(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

        # Loss
        loss = nn.MSELoss()(q_values, target_q_values)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        self.steps_done += 1

        # Update target network
        if self.steps_done % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return loss.item()

    def update_epsilon(self):
        """Decay epsilon"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, path):
        """Save model"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps_done': self.steps_done
        }, path)

    def load(self, path):
        """Load model"""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        self.steps_done = checkpoint['steps_done']
```

---

## Phase 5: ReWTSE Ensemble Integration

### 5.1 Ensemble Controller

Creare `src/hybrid_model/ensemble_controller.py`:

```python
"""
ReWTSE Ensemble Controller
Integra chunk-based DDQN models con ottimizzazione QP dei pesi
"""

import numpy as np
from cvxopt import matrix, solvers
import torch
from typing import List, Dict
from src.rl_agents.ddqn_agent import DDQNAgent

class ReWTSEnsembleController:
    """
    Controller per ReWTSE Ensemble di DDQN agents

    Implementa:
    - Training chunk-based di DDQN agents
    - Ottimizzazione QP dei pesi basata su look-back performance
    - Weighted ensemble prediction
    """

    def __init__(self, config):
        self.config = config

        # Chunk parameters (dal paper ReWTSE)
        self.chunk_length = config.get('chunk_length', 2016)  # 14 giorni
        self.lookback_length = config.get('lookback_length', 432)  # 3 giorni
        self.forecast_horizon = config.get('forecast_horizon', 1)  # 1 step ahead

        # Ensemble di DDQN agents (uno per chunk)
        self.chunk_models = []

        # Pesi correnti
        self.current_weights = None

        # Storia performance
        self.performance_history = []

    def train_chunk_model(self, chunk_id, env, num_episodes=50):
        """
        Addestra un DDQN agent su un chunk specifico

        Args:
            chunk_id: ID del chunk
            env: TradingEnv per il chunk
            num_episodes: Numero di episodi di training

        Returns:
            Trained DDQNAgent
        """

        print(f"\n{'='*60}")
        print(f"Training Chunk {chunk_id}")
        print(f"{'='*60}")

        # Crea nuovo DDQN agent
        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n

        agent = DDQNAgent(state_dim, action_dim, self.config)

        # Training loop
        episode_rewards = []

        for episode in range(num_episodes):
            state = env.reset()
            episode_reward = 0
            done = False

            while not done:
                # Select action
                action = agent.select_action(state, explore=True)

                # Execute action
                next_state, reward, done, _ = env.step(action)

                # Store transition
                agent.replay_buffer.push(state, action, reward, next_state, done)

                # Train
                loss = agent.train_step()

                # Update state
                state = next_state
                episode_reward += reward

            # Decay epsilon
            agent.update_epsilon()

            episode_rewards.append(episode_reward)

            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                print(f"Episode {episode+1}/{num_episodes}, Avg Reward: {avg_reward:.4f}, Epsilon: {agent.epsilon:.4f}")

        # Salva modello
        model_path = f"models/chunk_{chunk_id}_ddqn.pt"
        agent.save(model_path)
        print(f"✓ Chunk {chunk_id} model saved to {model_path}")

        return agent

    def optimize_weights(self, lookback_data, lookback_returns):
        """
        Ottimizzazione QP per trovare pesi ottimali basati su look-back performance

        Risolve:
            min_w  Σ ||y_(k+1):(k+h) - M_h(X:k, y:k) * w||²
            s.t.   w >= 0
                   1^T * w = 1

        Args:
            lookback_data: Look-back observations
            lookback_returns: Actual returns nel look-back period

        Returns:
            Optimal weights array
        """

        num_models = len(self.chunk_models)
        lookback_len = len(lookback_data) - self.forecast_horizon

        if lookback_len <= 0:
            # Fallback: uniform weights
            return np.ones(num_models) / num_models

        # Costruisci forecast matrix M_h
        # Shape: (lookback_len, num_models)
        M_h_list = []

        for k in range(lookback_len):
            # Per ogni timestep nel look-back
            forecasts_k = []

            for model in self.chunk_models:
                # Previsione h-step del modello
                state_k = lookback_data[k]

                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state_k).unsqueeze(0)
                    q_values = model.policy_net(state_tensor)

                    # Converti Q-values in expected return
                    # Usiamo il Q-value dell'azione ottimale come proxy
                    expected_return = q_values.max().item()

                forecasts_k.append(expected_return)

            M_h_list.append(forecasts_k)

        M_h = np.array(M_h_list)  # Shape: (lookback_len, num_models)

        # Target returns
        y_actual = np.array(lookback_returns[:lookback_len])

        # QP formulation
        # min 0.5 * w^T * P * w + q^T * w
        # s.t. G * w <= h (w >= 0)
        #      A * w = b  (sum(w) = 1)

        P = matrix(M_h.T @ M_h)
        q = matrix(-M_h.T @ y_actual)

        # Inequality constraints: w >= 0
        G = matrix(-np.eye(num_models))
        h = matrix(np.zeros(num_models))

        # Equality constraint: sum(w) = 1
        A = matrix(np.ones((1, num_models)))
        b = matrix(1.0)

        # Solve QP
        solvers.options['show_progress'] = False
        sol = solvers.qp(P, q, G, h, A, b)

        if sol['status'] == 'optimal':
            weights = np.array(sol['x']).flatten()
        else:
            print(f"Warning: QP solver failed with status {sol['status']}, using uniform weights")
            weights = np.ones(num_models) / num_models

        return weights

    def predict_ensemble(self, state, weights=None):
        """
        Weighted ensemble prediction

        Args:
            state: Current observation
            weights: Model weights (if None, use self.current_weights)

        Returns:
            Ensemble action
        """

        if weights is None:
            weights = self.current_weights

        if weights is None:
            # Fallback: uniform weights
            weights = np.ones(len(self.chunk_models)) / len(self.chunk_models)

        # Ottieni Q-values da ogni chunk model
        q_values_list = []

        for model in self.chunk_models:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = model.policy_net(state_tensor).squeeze().numpy()
                q_values_list.append(q_values)

        # Weighted average di Q-values
        weighted_q_values = np.zeros_like(q_values_list[0])

        for i, q_vals in enumerate(q_values_list):
            weighted_q_values += weights[i] * q_vals

        # Seleziona azione con Q-value massimo
        action = np.argmax(weighted_q_values)

        return action, weighted_q_values
```

### 5.2 Main Training Script

Creare `scripts/train_rewts_llm_rl.py`:

```python
"""
Script principale per training del sistema ReWTSE-LLM-RL
"""

import pandas as pd
import numpy as np
from tqdm import tqdm

from src.llm_agents.strategist_agent import StrategistAgent
from src.llm_agents.analyst_agent import AnalystAgent
from src.rl_agents.trading_env import TradingEnv
from src.hybrid_model.ensemble_controller import ReWTSEnsembleController

def load_data(ticker, config):
    """Carica dati preprocessati"""
    market_df = pd.read_csv(f"data/processed/{ticker}_full_data.csv", index_col=0, parse_dates=True)
    news_df = pd.read_csv(f"data/processed/{ticker}_news.csv", index_col=0, parse_dates=True)
    macro_df = pd.read_csv("data/processed/macro_data.csv", index_col=0, parse_dates=True)

    # Merge macro data
    market_df = market_df.join(macro_df, how='left').fillna(method='ffill')

    return market_df, news_df

def precompute_llm_strategies(ticker, market_df, news_df, config):
    """Pre-computa le strategie LLM per tutto il periodo"""

    print(f"\n{'='*60}")
    print(f"Pre-computing LLM Strategies for {ticker}")
    print(f"{'='*60}")

    strategist = StrategistAgent(config['llm'])
    analyst = AnalystAgent(config['llm'])

    strategies = []

    # Genera strategie mensili (ogni 20 trading days)
    strategy_frequency = config.get('strategy_frequency', 20)
    num_strategies = len(market_df) // strategy_frequency

    for i in tqdm(range(num_strategies), desc="Generating strategies"):
        start_idx = i * strategy_frequency
        end_idx = min((i + 1) * strategy_frequency, len(market_df))

        # Dati per questa strategia
        period_data = market_df.iloc[start_idx:end_idx]
        period_news = news_df[
            (news_df.index >= period_data.index[0]) &
            (news_df.index <= period_data.index[-1])
        ]

        # Processa news con Analyst Agent
        news_signals = analyst.process_news(period_news.to_dict('records'))

        # Prepara input per Strategist
        market_data = {
            'timestamp': period_data.index[-1],
            'Close': period_data['Close'].iloc[-1],
            'Volume': period_data['Volume'].iloc[-1],
            'Weekly_Returns': period_data['Close'].pct_change().tail(20).tolist(),
            'HV_Close': period_data['HV_Close'].iloc[-1],
            'IV_Close': period_data.get('IV_Close', pd.Series([0])).iloc[-1],
            'Beta': 1.0,  # Placeholder
            'Classification': 'Growth'  # Placeholder
        }

        fundamentals = {
            'current_ratio': period_data.get('Current_Ratio', 1.5),
            'debt_to_equity': period_data.get('Debt_to_Equity', 0.5),
            'pe_ratio': period_data.get('PE_Ratio', 20),
            'gross_margin': period_data.get('Gross_Margin', 0.4),
            'operating_margin': period_data.get('Operating_Margin', 0.2),
            'eps_yoy': period_data.get('EPS_YoY', 0.1),
            'net_income_yoy': period_data.get('Net_Income_YoY', 0.1)
        }

        analytics = {
            'ma_20': period_data['SMA_20'].iloc[-1],
            'ma_50': period_data['SMA_50'].iloc[-1],
            'ma_200': period_data['SMA_200'].iloc[-1],
            'ma_20_slope': period_data['SMA_20_Slope'].iloc[-1],
            'ma_50_slope': period_data['SMA_50_Slope'].iloc[-1],
            'rsi': period_data['RSI'].iloc[-1],
            'macd': period_data['MACD'].iloc[-1],
            'macd_signal': period_data['MACD_Signal'].iloc[-1],
            'atr': period_data['ATR'].iloc[-1]
        }

        macro_data = {
            'SPX_Close': period_data['SPX_Close'].iloc[-1],
            'SPX_Slope': period_data['SPX_Close'].diff().iloc[-1],
            'VIX_Close': period_data['VIX_Close'].iloc[-1],
            'VIX_Slope': period_data['VIX_Close'].diff().iloc[-1],
            'GDP_QoQ': period_data.get('GDP', 0),
            'PMI': period_data.get('PMI', 50),
            'PPI_YoY': period_data.get('PPI', 0),
            'Treasury_YoY': period_data.get('T10Y', 0)
        }

        # Genera strategia
        last_strategy = strategies[-1] if strategies else None

        strategy = strategist.generate_strategy(
            market_data=market_data,
            fundamentals=fundamentals,
            analytics=analytics,
            macro_data=macro_data,
            news_signals=news_signals,
            last_strategy=last_strategy
        )

        strategies.append(strategy)

    print(f"✓ Generated {len(strategies)} strategies")

    # Salva strategies
    import pickle
    with open(f"data/llm_strategies/{ticker}_strategies.pkl", 'wb') as f:
        pickle.dump(strategies, f)

    return strategies

def train_rewts_ensemble(ticker, market_df, strategies, config):
    """Addestra ReWTSE ensemble di DDQN agents"""

    print(f"\n{'='*60}")
    print(f"Training ReWTSE Ensemble for {ticker}")
    print(f"{'='*60}")

    # Inizializza ensemble controller
    ensemble = ReWTSEnsembleController(config['rewts'])

    # Determina numero di chunks
    chunk_length = config['rewts']['chunk_length']
    num_chunks = len(market_df) // chunk_length

    print(f"Total data points: {len(market_df)}")
    print(f"Chunk length: {chunk_length}")
    print(f"Number of chunks: {num_chunks}")

    # Train un DDQN per ogni chunk
    for chunk_id in range(num_chunks):
        start_idx = chunk_id * chunk_length
        end_idx = min((chunk_id + 1) * chunk_length, len(market_df))

        # Estrai chunk data
        chunk_df = market_df.iloc[start_idx:end_idx].copy()

        # Strategie LLM per questo chunk
        strategy_start_idx = start_idx // config['strategy_frequency']
        strategy_end_idx = end_idx // config['strategy_frequency']
        chunk_strategies = strategies[strategy_start_idx:strategy_end_idx]

        # Crea environment per il chunk
        env = TradingEnv(chunk_df, chunk_strategies, config['trading_env'])

        # Addestra DDQN agent
        agent = ensemble.train_chunk_model(
            chunk_id=chunk_id,
            env=env,
            num_episodes=config['rewts']['episodes_per_chunk']
        )

        ensemble.chunk_models.append(agent)

    print(f"\n✓ Ensemble training complete!")
    print(f"  Total chunk models: {len(ensemble.chunk_models)}")

    return ensemble

def main():
    """Main training pipeline"""

    # Configurazione
    config = {
        'tickers': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'TSLA'],
        'llm': {
            'llm_model': 'gpt-4o-mini',
            'temperature': 0.0,
            'seed': 49
        },
        'rewts': {
            'chunk_length': 2016,  # 14 giorni
            'lookback_length': 432,  # 3 giorni
            'forecast_horizon': 1,
            'episodes_per_chunk': 50,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_min': 0.01,
            'epsilon_decay': 0.995,
            'learning_rate': 1e-3,
            'batch_size': 64,
            'buffer_size': 10000,
            'target_update_freq': 10,
            'hidden_dims': [128, 64]
        },
        'trading_env': {
            'initial_balance': 10000,
            'transaction_cost': 0.001,
            'max_position': 1.0
        },
        'strategy_frequency': 20  # Strategia mensile
    }

    # Loop su tutti i ticker
    for ticker in config['tickers']:
        print(f"\n{'#'*60}")
        print(f"# Processing {ticker}")
        print(f"{'#'*60}")

        # Load data
        market_df, news_df = load_data(ticker, config)

        # Pre-compute LLM strategies
        strategies = precompute_llm_strategies(ticker, market_df, news_df, config)

        # Train ReWTSE ensemble
        ensemble = train_rewts_ensemble(ticker, market_df, strategies, config)

        # Salva ensemble
        import pickle
        with open(f"models/{ticker}_rewts_ensemble.pkl", 'wb') as f:
            pickle.dump(ensemble, f)

        print(f"\n✓ {ticker} complete!")

    print(f"\n{'='*60}")
    print("✓ All tickers processed successfully!")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
```

---

## Phase 6: Backtesting e Evaluation

### 6.1 Backtesting Script

Creare `scripts/backtest_ensemble.py`:

```python
"""
Backtesting script per ReWTSE-LLM-RL ensemble
"""

import pandas as pd
import numpy as np
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt

from src.rl_agents.trading_env import TradingEnv

def calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252):
    """Calcola Sharpe Ratio annualizzato"""
    excess_returns = returns - risk_free_rate
    return np.sqrt(periods_per_year) * (excess_returns.mean() / excess_returns.std())

def calculate_max_drawdown(portfolio_values):
    """Calcola Maximum Drawdown"""
    cumulative = pd.Series(portfolio_values)
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()

def backtest_ensemble(ticker, ensemble, market_df, strategies, config):
    """
    Backtest del ReWTSE ensemble su test set

    Returns:
        Dict con metriche di performance
    """

    print(f"\n{'='*60}")
    print(f"Backtesting {ticker}")
    print(f"{'='*60}")

    # Split train/test
    train_size = int(0.7 * len(market_df))
    test_df = market_df.iloc[train_size:].copy()
    test_strategies = strategies[train_size // config['strategy_frequency']:]

    # Crea environment di test
    test_env = TradingEnv(test_df, test_strategies, config['trading_env'])

    # Inizializza
    state = test_env.reset()
    done = False

    lookback_length = config['rewts']['lookback_length']
    lookback_buffer = []

    portfolio_values = [test_env.initial_balance]
    actions_taken = []
    weights_history = []

    step = 0

    with tqdm(total=len(test_df), desc="Backtesting") as pbar:
        while not done:
            # Accumula look-back data
            lookback_buffer.append(state)
            if len(lookback_buffer) > lookback_length:
                lookback_buffer.pop(0)

            # Ottimizza pesi se abbiamo abbastanza look-back data
            if len(lookback_buffer) == lookback_length:
                # Estrai returns dal look-back
                lookback_returns = []
                for i in range(len(lookback_buffer) - 1):
                    # Semplice proxy: variazione del close price
                    # In produzione, usare actual portfolio returns
                    ret = (test_df.iloc[step - lookback_length + i + 1]['Close'] /
                           test_df.iloc[step - lookback_length + i]['Close']) - 1
                    lookback_returns.append(ret)

                # Ottimizza pesi
                weights = ensemble.optimize_weights(lookback_buffer, lookback_returns)
                ensemble.current_weights = weights
                weights_history.append(weights)
            else:
                # Usa uniform weights
                weights = np.ones(len(ensemble.chunk_models)) / len(ensemble.chunk_models)
                ensemble.current_weights = weights
                weights_history.append(weights)

            # Predizione ensemble
            action, q_values = ensemble.predict_ensemble(state)

            # Execute action
            next_state, reward, done, _ = test_env.step(action)

            # Track
            portfolio_values.append(test_env.portfolio_value)
            actions_taken.append(action)

            state = next_state
            step += 1
            pbar.update(1)

    # Calcola metriche
    portfolio_values = np.array(portfolio_values)
    returns = np.diff(portfolio_values) / portfolio_values[:-1]

    sharpe_ratio = calculate_sharpe_ratio(returns)
    max_drawdown = calculate_max_drawdown(portfolio_values)
    cumulative_return = (portfolio_values[-1] / portfolio_values[0]) - 1

    metrics = {
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'cumulative_return': cumulative_return,
        'final_portfolio_value': portfolio_values[-1],
        'portfolio_values': portfolio_values,
        'actions': actions_taken,
        'weights_history': weights_history
    }

    print(f"\n{'='*60}")
    print(f"Backtest Results for {ticker}")
    print(f"{'='*60}")
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"Max Drawdown: {max_drawdown:.4f}")
    print(f"Cumulative Return: {cumulative_return:.2%}")
    print(f"Final Portfolio Value: ${portfolio_values[-1]:.2f}")

    return metrics

def plot_results(ticker, metrics):
    """Visualizza risultati backtest"""

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Portfolio value
    axes[0].plot(metrics['portfolio_values'])
    axes[0].set_title(f"{ticker} - Portfolio Value")
    axes[0].set_ylabel("Value ($)")
    axes[0].grid(True)

    # Actions
    actions = np.array(metrics['actions'])
    axes[1].scatter(range(len(actions)), actions, c=actions, cmap='RdYlGn', alpha=0.6)
    axes[1].set_title(f"{ticker} - Actions (0=SHORT, 1=HOLD, 2=LONG)")
    axes[1].set_ylabel("Action")
    axes[1].set_ylim(-0.5, 2.5)
    axes[1].grid(True)

    # Weights evolution
    weights_history = np.array(metrics['weights_history'])
    for i in range(weights_history.shape[1]):
        axes[2].plot(weights_history[:, i], label=f"Model {i+1}", alpha=0.7)
    axes[2].set_title(f"{ticker} - Model Weights Over Time")
    axes[2].set_ylabel("Weight")
    axes[2].set_xlabel("Time Step")
    axes[2].legend(loc='upper right')
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig(f"results/visualizations/{ticker}_backtest.png", dpi=300)
    plt.close()

    print(f"✓ Plot saved to results/visualizations/{ticker}_backtest.png")

def main():
    """Main backtesting pipeline"""

    config = {
        'tickers': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'TSLA'],
        'rewts': {
            'chunk_length': 2016,
            'lookback_length': 432,
            'forecast_horizon': 1
        },
        'trading_env': {
            'initial_balance': 10000,
            'transaction_cost': 0.001,
            'max_position': 1.0
        },
        'strategy_frequency': 20
    }

    all_metrics = {}

    for ticker in config['tickers']:
        # Load ensemble
        with open(f"models/{ticker}_rewts_ensemble.pkl", 'rb') as f:
            ensemble = pickle.load(f)

        # Load data e strategies
        market_df = pd.read_csv(f"data/processed/{ticker}_full_data.csv", index_col=0, parse_dates=True)
        with open(f"data/llm_strategies/{ticker}_strategies.pkl", 'rb') as f:
            strategies = pickle.load(f)

        # Backtest
        metrics = backtest_ensemble(ticker, ensemble, market_df, strategies, config)
        all_metrics[ticker] = metrics

        # Plot
        plot_results(ticker, metrics)

    # Summary table
    print(f"\n{'='*60}")
    print("Summary Across All Tickers")
    print(f"{'='*60}")

    summary_df = pd.DataFrame({
        ticker: {
            'Sharpe Ratio': metrics['sharpe_ratio'],
            'Max Drawdown': metrics['max_drawdown'],
            'Cumulative Return': metrics['cumulative_return']
        }
        for ticker, metrics in all_metrics.items()
    }).T

    print(summary_df)
    summary_df.to_csv("results/metrics/summary_metrics.csv")

    print(f"\n✓ Summary saved to results/metrics/summary_metrics.csv")

if __name__ == '__main__':
    main()
```

---

## Phase 7: Esecuzione del Pipeline Completo

### 7.1 Setup Iniziale

```bash
# 1. Scarica dati
python scripts/download_data.py

# 2. Train ReWTSE-LLM-RL ensemble
python scripts/train_rewts_llm_rl.py

# 3. Backtest
python scripts/backtest_ensemble.py
```

### 7.2 Notebook Prototipo

Creare `notebooks/01_prototype_single_ticker.ipynb` per testing rapido su singolo ticker (AAPL).

```python
# In Jupyter Notebook

import sys
sys.path.append('..')

from scripts.train_rewts_llm_rl import *
from scripts.backtest_ensemble import *

# Config ridotto per prototipo
config = {
    'tickers': ['AAPL'],  # Solo AAPL
    'llm': {
        'llm_model': 'gpt-4o-mini',
        'temperature': 0.0,
        'seed': 49
    },
    'rewts': {
        'chunk_length': 1000,  # Ridotto per testing
        'lookback_length': 200,
        'episodes_per_chunk': 10,  # Ridotto
        # ... altri params
    }
}

# Esegui pipeline
market_df, news_df = load_data('AAPL', config)
strategies = precompute_llm_strategies('AAPL', market_df, news_df, config)
ensemble = train_rewts_ensemble('AAPL', market_df, strategies, config)
metrics = backtest_ensemble('AAPL', ensemble, market_df, strategies, config)
plot_results('AAPL', metrics)
```

---

## Componenti Riutilizzati dai Paper

### Dal Repository ReWTS (https://github.com/SINTEF/rewts)

| Componente | Utilizzo | File |
|------------|----------|------|
| Chunk-based training framework | Base per segmentazione temporale | `src/rewts/` |
| QP Optimization (cvxopt) | Ottimizzazione pesi | `ensemble_controller.py` |
| Configuration system (Hydra) | Gestione configs | `configs/` |
| Data module structure | Template per dataset loading | `src/rewts/datamodules/` |

### Dal Paper LLM+RL

| Componente | Utilizzo | File |
|------------|----------|------|
| Strategist Prompt (Listing 1) | Template per strategy generation | `strategist_agent.py` |
| Analyst Prompt (Listing 2) | Template per news processing | `analyst_agent.py` |
| DDQN Baseline | Architettura RL agent | `ddqn_agent.py` |
| Feature Engineering | Dataset multi-modale | `download_data.py` |
| Interaction term τ | LLM signal integration | `trading_env.py` |

---

## Metriche Target Attese

Basandosi sui risultati dei paper:

| Metrica | RL-only | LLM+RL | **ReWTSE-LLM-RL (target)** |
|---------|---------|--------|----------------------------|
| Sharpe Ratio (mean) | 0.64 | 1.10 | **1.30 - 1.50** |
| Max Drawdown (mean) | 0.36 | 0.31 | **0.25 - 0.28** |
| Robustezza outlier | Bassa | Media | **Alta** |

---

## Troubleshooting Comune

### Problema 1: Out of Memory durante training

**Soluzione**:
```python
# Riduci batch_size
config['rewts']['batch_size'] = 32  # invece di 64

# Riduci buffer size
config['rewts']['buffer_size'] = 5000  # invece di 10000
```

### Problema 2: LLM API rate limits

**Soluzione**:
```python
# Pre-computa tutte le strategie offline e cachale
import time
time.sleep(1)  # Aggiungi delay tra chiamate

# Oppure usa batch processing
```

### Problema 3: QP solver non converge

**Soluzione**:
```python
# Aggiungi regularizzazione
epsilon = 1e-5
P = P + epsilon * np.eye(num_models)

# Oppure usa fallback a uniform weights
if sol['status'] != 'optimal':
    weights = np.ones(num_models) / num_models
```

---

## Next Steps e Estensioni

### Possibili Miglioramenti

1. **Reward Shaping**: Integrare segnali LLM direttamente nella reward function
2. **Hierarchical ReWTSE**: Applicare ensemble anche al livello LLM
3. **Online Learning**: Supporto per incremental updates senza full retraining
4. **Multi-Asset Portfolio**: Estendere a portfolio allocation invece di single-stock
5. **Hyperparameter Optimization**: Usare Optuna per tuning automatico

---

## Conclusione

Questa guida fornisce un'implementazione completa e modulare del sistema ReWTSE-LLM-RL, riutilizzando il più possibile il codice esistente dai repository dei paper originali.

L'architettura proposta combina:
- ✅ **ReWTSE**: Specializzazione temporale e robustezza
- ✅ **LLM**: Reasoning strategico e multi-modal signal integration
- ✅ **RL**: Esecuzione tattica e adattamento continuo

Per domande o supporto, consulta:
- ReWTSE Paper: https://arxiv.org/abs/2403.02150
- ReWTSE Repo: https://github.com/SINTEF/rewts
- LLM+RL Paper: arXiv:2508.02366v1
