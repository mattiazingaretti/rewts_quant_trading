"""
Analyst Agent: Processa news e genera segnali direzionali
Utilizza Google Gemini 2.5 Flash per analisi delle news
"""

import google.generativeai as genai
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
        self.model_name = config.get('llm_model', 'gemini-2.0-flash-exp')
        self.temperature = config.get('temperature', 0.7)
        self.project_id = config.get('project_id')  # Google AI Studio project ID

        # Configura Google Gemini API
        api_key = config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in config or environment")

        genai.configure(api_key=api_key)

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
{{
  "factors": [
    {{
      "factor": "Summary of news (max 70 words)",
      "sentiment": -1/0/+1,
      "market_impact": 1-3
    }},
    ...
  ]
}}
"""

    def process_news(self, news_articles: List[Dict]) -> Dict:
        """
        Processa una lista di news articles e genera fattori strutturati

        Args:
            news_articles: Lista di dict con keys 'timestamp', 'headline', 'summary'

        Returns:
            Dict con 'factors', 'aggregate_sentiment', 'aggregate_impact'
        """

        if not news_articles or len(news_articles) == 0:
            # Nessuna news disponibile
            return {
                'factors': [],
                'sentiment': 0,
                'impact_score': 1
            }

        # Anonimizza le news (per evitare memorization)
        anonymized_articles = self._anonymize_articles(news_articles)

        # Formatta nel prompt
        articles_text = "\n\n".join([
            f"Article {i+1}:\n{art.get('headline', '')}\n{art.get('summary', '')}"
            for i, art in enumerate(anonymized_articles)
        ])

        prompt = self.prompt_template.format(articles_list=articles_text)

        try:
            # LLM call
            # Use project ID for paid tier if provided
            request_options = {}
            if self.project_id:
                request_options = {"timeout": 600}  # 10 min timeout for paid tier

            response = self.model.generate_content(
                prompt,
                request_options=request_options if request_options else None
            )

            # Parse
            factors_json = json.loads(response.text)

            # Aggrega sentiment e impact
            factors = [NewsFactor(**f) for f in factors_json['factors']]

            if len(factors) > 0:
                aggregate_sentiment = sum([f.sentiment * f.market_impact for f in factors])
                aggregate_sentiment = max(-1, min(1, aggregate_sentiment / len(factors)))
                aggregate_impact = max([f.market_impact for f in factors])
            else:
                aggregate_sentiment = 0
                aggregate_impact = 1

            return {
                'factors': factors,
                'sentiment': aggregate_sentiment,
                'impact_score': aggregate_impact
            }

        except Exception as e:
            print(f"Error processing news: {e}")
            # Fallback neutro
            return {
                'factors': [],
                'sentiment': 0,
                'impact_score': 1
            }

    def _anonymize_articles(self, articles: List[Dict]) -> List[Dict]:
        """Anonimizza named entities per evitare memorization"""
        # Semplice implementazione: mantieni come sono
        # In produzione, usare NER più sofisticato
        return articles
