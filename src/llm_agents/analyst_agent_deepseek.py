"""
Analyst Agent: Processa news e genera segnali direzionali
Utilizza DeepSeek-V3.2 per analisi delle news
"""

from openai import OpenAI
from typing import List, Dict
from dataclasses import dataclass
import json
import os

@dataclass
class NewsFactor:
    factor: str
    sentiment: int  # -1, 0, +1
    market_impact: int  # 1-3 (Likert)

class AnalystAgent:
    def __init__(self, config):
        self.model_name = config.get('llm_model', 'deepseek-chat')
        self.temperature = config.get('temperature', 0.7)

        # Configura DeepSeek API (compatibile OpenAI)
        api_key = config.get('deepseek_api_key') or os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in config or environment")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        print(f"✓ Analyst Agent configured with DeepSeek ({self.model_name})")

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
   - Sentiment: -1 (negative), 0 (neutral), +1 (positive)
   - Market Impact: 1-3 (Likert scale, 3 = highest)

4. Calculate overall sentiment:
   - Weighted average of factor sentiments by market impact
   - Normalize to [-1, 1] range

Output MUST be valid JSON with this structure:
{{
  "top_factors": [
    {{"factor": "Factor description", "sentiment": -1/0/1, "market_impact": 1-3}}
  ],
  "overall_sentiment": "bullish/neutral/bearish",
  "confidence": 0.0-1.0,
  "key_topics": ["topic1", "topic2", "topic3"]
}}

IMPORTANT:
- Extract maximum 3 most relevant factors
- Be concise (1-2 sentences per factor)
- Focus on price-moving catalysts
- If no significant news, return neutral sentiment with confidence < 0.5
"""

    def process_news(self, news_articles: List[Dict]) -> Dict:
        """
        Processa una lista di news articles e genera segnali

        Args:
            news_articles: Lista di dict con keys: headline, summary, source

        Returns:
            Dict con: sentiment, confidence, key_topics, factors
        """

        if not news_articles or len(news_articles) == 0:
            # Nessuna news disponibile
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'key_topics': [],
                'factors': []
            }

        # Formatta articles list per il prompt
        articles_text = ""
        for i, article in enumerate(news_articles, 1):
            headline = article.get('headline', 'No headline')
            summary = article.get('summary', 'No summary')
            source = article.get('source', 'Unknown')

            articles_text += f"\n{i}. [{source}] {headline}\n   {summary}\n"

        # Prepara prompt
        prompt = self.prompt_template.format(articles_list=articles_text)

        # Call DeepSeek API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert financial market analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        # Parse response
        response_text = response.choices[0].message.content
        result = json.loads(response_text)

        # Extract factors
        factors = []
        for factor_data in result.get('top_factors', []):
            factors.append(NewsFactor(
                factor=factor_data['factor'],
                sentiment=factor_data['sentiment'],
                market_impact=factor_data['market_impact']
            ))

        # Return structured signals
        return {
            'sentiment': result.get('overall_sentiment', 'neutral'),
            'confidence': result.get('confidence', 0.5),
            'key_topics': result.get('key_topics', []),
            'factors': factors
        }
