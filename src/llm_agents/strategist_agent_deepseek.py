"""
Strategist Agent: Genera strategie mensili di trading
Utilizza DeepSeek-V3.2 per generare strategie basate su multi-modal data
"""

from openai import OpenAI
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
        self.model_name = config.get('llm_model', 'deepseek-chat')
        self.temperature = config.get('temperature', 0.0)

        # Configura DeepSeek API (compatibile OpenAI)
        api_key = config.get('deepseek_api_key') or os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in config or environment")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        print(f"✓ Strategist Agent configured with DeepSeek ({self.model_name})")

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

  Growth:
    EPS_YoY: {eps_yoy}
    Net_Income_YoY: {net_income_yoy}

Analytics_Data:
  Moving_Averages:
    MA_20: {ma_20}
    MA_50: {ma_50}
    MA_200: {ma_200}

  Moving_Average_Slopes:
    MA_20_Slope: {ma_20_slope}
    MA_50_Slope: {ma_50_slope}

  Momentum:
    RSI: {rsi}

  Volatility:
    ATR: {atr}

  MACD:
    MACD: {macd}
    MACD_Signal: {macd_signal}

Macro_Data:
  Market_Context:
    SPX_Close: {spx_close}
    SPX_Slope: {spx_slope}
    VIX_Close: {vix_close}
    VIX_Slope: {vix_slope}

  Economic:
    GDP_QoQ: {gdp_qoq}
    PMI: {pmi}
    PPI_YoY: {ppi_yoy}
    Treasury_YoY: {treasury_yoy}

News_Signals:
  sentiment: {sentiment}
  confidence: {news_confidence}
  key_topics: {key_topics}

System_Context:
Persona: Expert Quantitative Hedge Fund Manager
Goal: Generate monthly trading strategy based on multi-modal market data

Instructions:
1. Analyze the provided data holistically: technical indicators, fundamentals,
   macro conditions, and news sentiment
2. Determine market direction (LONG or SHORT) for next month
3. Assign confidence level (1-3 Likert scale):
   - 1: Low confidence
   - 2: Moderate confidence
   - 3: High confidence
4. Provide concise rationale explaining key factors driving the decision
5. List which features most influenced your decision

Output MUST be valid JSON with this structure:
{{
  "direction": 1 or 0,
  "confidence": 1.0-3.0,
  "explanation": "Brief rationale (2-3 sentences)",
  "key_features": [
    {{"feature": "feature_name", "impact": "positive/negative", "weight": 0.0-1.0}}
  ],
  "timestamp": "{timestamp}"
}}

IMPORTANT:
- direction=1 means LONG (bullish), direction=0 means SHORT (bearish)
- confidence is Likert scale 1.0-3.0 (can be decimal like 2.5)
- Focus on actionable insights, not data recitation
- Consider multi-modal evidence, not just one signal
"""

    def generate_strategy(
        self,
        market_data: Dict,
        fundamentals: Dict,
        analytics: Dict,
        macro_data: Dict,
        news_signals: Dict,
        last_strategy: 'TradingStrategy' = None
    ) -> TradingStrategy:
        """
        Genera una strategia di trading mensile

        Args:
            market_data: Dati di mercato (prezzi, volumi, volatilità)
            fundamentals: Dati fondamentali (ratios, margins)
            analytics: Indicatori tecnici (MA, RSI, MACD)
            macro_data: Dati macro (SPX, VIX, GDP, PMI)
            news_signals: Segnali dalle news (sentiment, topics)
            last_strategy: Strategia precedente per reflection

        Returns:
            TradingStrategy object
        """

        # Prepara last strategy context
        if last_strategy:
            last_returns = "positive" if last_strategy.direction == 1 else "negative"
            last_action = "LONG" if last_strategy.direction == 1 else "SHORT"
            last_rationale = last_strategy.explanation
        else:
            last_returns = "N/A"
            last_action = "N/A"
            last_rationale = "No previous strategy"

        # Prepara prompt con dati
        prompt = self.prompt_template.format(
            # Last strategy
            last_returns=last_returns,
            last_action=last_action,
            last_rationale=last_rationale,

            # Market data
            beta=market_data.get('Beta', 1.0),
            classification=market_data.get('Classification', 'Unknown'),
            close=market_data.get('Close', 0),
            volume=market_data.get('Volume', 0),
            weekly_returns=market_data.get('Weekly_Returns', []),
            hv_close=market_data.get('HV_Close', 0),
            iv_close=market_data.get('IV_Close', 0),

            # Fundamentals
            current_ratio=fundamentals.get('current_ratio', 0),
            debt_to_equity=fundamentals.get('debt_to_equity', 0),
            pe_ratio=fundamentals.get('pe_ratio', 0),
            gross_margin=fundamentals.get('gross_margin', 0),
            operating_margin=fundamentals.get('operating_margin', 0),
            eps_yoy=fundamentals.get('eps_yoy', 0),
            net_income_yoy=fundamentals.get('net_income_yoy', 0),

            # Analytics
            ma_20=analytics.get('ma_20', 0),
            ma_50=analytics.get('ma_50', 0),
            ma_200=analytics.get('ma_200', 0),
            ma_20_slope=analytics.get('ma_20_slope', 0),
            ma_50_slope=analytics.get('ma_50_slope', 0),
            rsi=analytics.get('rsi', 50),
            atr=analytics.get('atr', 0),
            macd=analytics.get('macd', 0),
            macd_signal=analytics.get('macd_signal', 0),

            # Macro
            spx_close=macro_data.get('SPX_Close', 0),
            spx_slope=macro_data.get('SPX_Slope', 0),
            vix_close=macro_data.get('VIX_Close', 0),
            vix_slope=macro_data.get('VIX_Slope', 0),
            gdp_qoq=macro_data.get('GDP_QoQ', 0),
            pmi=macro_data.get('PMI', 50),
            ppi_yoy=macro_data.get('PPI_YoY', 0),
            treasury_yoy=macro_data.get('Treasury_YoY', 0),

            # News
            sentiment=news_signals.get('sentiment', 'neutral'),
            news_confidence=news_signals.get('confidence', 0.5),
            key_topics=news_signals.get('key_topics', []),

            # Timestamp
            timestamp=market_data.get('timestamp', '')
        )

        # Call DeepSeek API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert quantitative hedge fund manager generating trading strategies."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        # Parse response
        response_text = response.choices[0].message.content
        result = json.loads(response_text)

        # Calcola strength (entropy-adjusted confidence)
        # Paper formula: τ = (2d - 1) × c
        direction = result['direction']
        confidence = result['confidence']
        strength = (2 * direction - 1) * confidence

        # Create TradingStrategy object
        strategy = TradingStrategy(
            direction=direction,
            confidence=confidence,
            strength=strength,
            explanation=result['explanation'],
            features_used=result.get('key_features', []),
            timestamp=result.get('timestamp', market_data.get('timestamp', ''))
        )

        # Update ICM
        self.memory_buffer.append(strategy)
        if len(self.memory_buffer) > 10:  # Keep last 10 strategies
            self.memory_buffer.pop(0)

        return strategy
