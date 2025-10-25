"""
Strategist Agent: Genera strategie mensili di trading
Utilizza Google Gemini 2.5 Flash per generare strategie basate su multi-modal data
"""

import google.generativeai as genai
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import json
import os

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
        self.model_name = config.get('llm_model', 'gemini-2.0-flash-exp')
        self.temperature = config.get('temperature', 0.0)
        self.seed = config.get('seed', 49)
        self.project_id = config.get('project_id')  # Google AI Studio project ID

        # Configura Google Gemini API
        api_key = config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in config or environment")

        # Configure with project ID for paid tier quota
        if self.project_id:
            from google.api_core.client_options import ClientOptions
            client_options = ClientOptions(quota_project_id=self.project_id)
            genai.configure(api_key=api_key, client_options=client_options)
            print(f"✓ Strategist Agent configured with paid tier project: {self.project_id}")
        else:
            genai.configure(api_key=api_key)
            print("⚠ Strategist Agent using free tier (no project_id provided)")

        # Inizializza il modello
        generation_config = {
            "temperature": self.temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
        )

        # Carica prompt template dal paper
        self.prompt_template = self._load_prompt_template()

        # In-Context Memory (ICM) per reflection
        self.memory_buffer = []

    def _load_prompt_template(self):
        """Carica il prompt P4 dal paper (Listing 1 in Appendix)"""
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
{{
  "action": "LONG" or "SHORT",
  "action_confidence": 1-3 (Likert scale),
  "explanation": "Max 350 words rationale",
  "features_used": [
    {{"feature": "Stock_Data.Close", "direction": "LONG/SHORT", "weight": 1-3}},
    ...
  ]
}}
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

        try:
            # Chiamata a Gemini (project ID già configurato in __init__)
            response = self.model.generate_content(
                prompt,
                request_options={"timeout": 600}  # 10 min timeout
            )

            # Parse response
            strategy_json = json.loads(response.text)

            # Calcola entropy-adjusted confidence
            # Per Gemini, non abbiamo logprobs direttamente, usiamo un proxy
            entropy = 0.5  # Default middle value

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

        except Exception as e:
            print(f"Error generating strategy: {e}")
            # Fallback strategy
            return TradingStrategy(
                direction=1,
                confidence=1.0,
                strength=0.5,
                explanation="Fallback strategy due to API error",
                features_used=[],
                timestamp=market_data.get('timestamp', 'N/A')
            )

    def _prepare_prompt_data(self, market_data, fundamentals, analytics,
                            macro_data, news_signals, last_strategy):
        """Helper per formattare i dati nel formato del prompt"""

        data = {}

        # Last strategy (per ICM)
        if last_strategy:
            data['last_returns'] = getattr(last_strategy, 'returns', 'N/A')
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
        data['gdp_qoq'] = macro_data.get('GDP_QoQ', 0)
        data['pmi'] = macro_data.get('PMI', 50.0)
        data['ppi_yoy'] = macro_data.get('PPI_YoY', 0)
        data['treasury_yoy'] = macro_data.get('Treasury_YoY', 0)

        # News
        data['news_sentiment'] = news_signals.get('sentiment', 0)
        data['news_impact'] = news_signals.get('impact_score', 1)

        return data
