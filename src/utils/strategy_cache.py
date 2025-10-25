"""
Strategy caching system per ridurre chiamate API LLM
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import asdict, is_dataclass


class StrategyCache:
    """Cache per strategie LLM generate"""

    def __init__(self, cache_dir: str = "data/cache/strategies"):
        """
        Initialize strategy cache

        Args:
            cache_dir: Directory dove salvare il cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "strategy_cache.json"
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Carica cache da file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load cache file: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Salva cache su file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save cache file: {e}")

    def _generate_key(self,
                      ticker: str,
                      market_data: Dict[str, Any],
                      fundamentals: Dict[str, Any],
                      analytics: Dict[str, Any],
                      macro_data: Dict[str, Any],
                      news_signals: Dict[str, Any],
                      model_name: str,
                      temperature: float) -> str:
        """
        Genera chiave univoca per una strategia basata sui dati di input

        Args:
            ticker: Ticker symbol
            market_data: Dati di mercato
            fundamentals: Dati fondamentali
            analytics: Dati analitici
            macro_data: Dati macroeconomici
            news_signals: Segnali dalle news
            model_name: Nome del modello LLM
            temperature: Temperature del modello

        Returns:
            Hash MD5 come chiave
        """
        # Crea una rappresentazione normalizzata dei dati
        # Arrotondiamo i valori per evitare variazioni minime
        key_data = {
            'ticker': ticker,
            'model': model_name,
            'temp': round(temperature, 2),
            'market': {
                'close': round(market_data.get('Close', 0), 2),
                'volume': round(market_data.get('Volume', 0), -3),  # Arrotonda a migliaia
            },
            'analytics': {
                'rsi': round(analytics.get('rsi', 0), 1),
                'macd': round(analytics.get('macd', 0), 3),
            },
            'sentiment': news_signals.get('sentiment', 'neutral'),
            'confidence': round(news_signals.get('confidence', 0.5), 2)
        }

        # Serializza e genera hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self,
            ticker: str,
            market_data: Dict[str, Any],
            fundamentals: Dict[str, Any],
            analytics: Dict[str, Any],
            macro_data: Dict[str, Any],
            news_signals: Dict[str, Any],
            model_name: str,
            temperature: float) -> Optional[Dict[str, Any]]:
        """
        Recupera una strategia dalla cache se esiste

        Returns:
            Strategia cached o None se non trovata
        """
        key = self._generate_key(
            ticker, market_data, fundamentals, analytics,
            macro_data, news_signals, model_name, temperature
        )

        return self.cache_data.get(key)

    def set(self,
            ticker: str,
            market_data: Dict[str, Any],
            fundamentals: Dict[str, Any],
            analytics: Dict[str, Any],
            macro_data: Dict[str, Any],
            news_signals: Dict[str, Any],
            model_name: str,
            temperature: float,
            strategy: Any):
        """
        Salva una strategia nella cache

        Args:
            strategy: Strategia da cachare (può essere dict o dataclass)
        """
        key = self._generate_key(
            ticker, market_data, fundamentals, analytics,
            macro_data, news_signals, model_name, temperature
        )

        # Converti dataclass a dict per la serializzazione
        if is_dataclass(strategy):
            strategy_dict = asdict(strategy)
        else:
            strategy_dict = strategy

        self.cache_data[key] = strategy_dict
        self._save_cache()

    def clear(self):
        """Pulisce completamente la cache"""
        self.cache_data = {}
        self._save_cache()

    def get_stats(self) -> Dict[str, int]:
        """Ritorna statistiche sulla cache"""
        return {
            'total_entries': len(self.cache_data),
            'cache_file_size_kb': self.cache_file.stat().st_size // 1024 if self.cache_file.exists() else 0
        }
