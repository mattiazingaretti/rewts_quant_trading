"""
Script principale per training del sistema ReWTSE-LLM-RL
"""

import pandas as pd
import numpy as np
from tqdm import tqdm
import sys
import os
import pickle

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_agents.strategist_agent import StrategistAgent
from src.llm_agents.analyst_agent import AnalystAgent
from src.rl_agents.trading_env import TradingEnv
from src.hybrid_model.ensemble_controller import ReWTSEnsembleController
from src.utils.data_utils import load_market_data, load_news_data, filter_news_by_period

def load_data(ticker, config):
    """Carica dati preprocessati"""
    market_df = load_market_data(ticker)
    news_df = load_news_data(ticker)
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

        # Filter news for this period using utility function
        period_news = filter_news_by_period(
            news_df,
            period_data.index[0],
            period_data.index[-1]
        )

        # Processa news con Analyst Agent
        if len(period_news) > 0:
            news_signals = analyst.process_news(period_news.to_dict('records'))
        else:
            # No news available for this period
            news_signals = {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'key_topics': []
            }

        # Prepara input per Strategist
        market_data = {
            'timestamp': str(period_data.index[-1]),
            'Close': float(period_data['Close'].iloc[-1]),
            'Volume': float(period_data['Volume'].iloc[-1]),
            'Weekly_Returns': period_data['Close'].pct_change().tail(20).tolist(),
            'HV_Close': float(period_data['HV_Close'].iloc[-1]) if 'HV_Close' in period_data else 0.0,
            'IV_Close': float(period_data.get('IV_Close', pd.Series([0])).iloc[-1]) if 'IV_Close' in period_data else 0.0,
            'Beta': 1.0,
            'Classification': 'Growth'
        }

        fundamentals = {
            'current_ratio': float(period_data.get('Current_Ratio', pd.Series([1.5])).iloc[-1]) if 'Current_Ratio' in period_data else 1.5,
            'debt_to_equity': float(period_data.get('Debt_to_Equity', pd.Series([0.5])).iloc[-1]) if 'Debt_to_Equity' in period_data else 0.5,
            'pe_ratio': float(period_data.get('PE_Ratio', pd.Series([20])).iloc[-1]) if 'PE_Ratio' in period_data else 20.0,
            'gross_margin': float(period_data.get('Gross_Margin', pd.Series([0.4])).iloc[-1]) if 'Gross_Margin' in period_data else 0.4,
            'operating_margin': float(period_data.get('Operating_Margin', pd.Series([0.2])).iloc[-1]) if 'Operating_Margin' in period_data else 0.2,
            'eps_yoy': 0.1,
            'net_income_yoy': 0.1
        }

        analytics = {
            'ma_20': float(period_data['SMA_20'].iloc[-1]),
            'ma_50': float(period_data['SMA_50'].iloc[-1]),
            'ma_200': float(period_data['SMA_200'].iloc[-1]),
            'ma_20_slope': float(period_data['SMA_20_Slope'].iloc[-1]),
            'ma_50_slope': float(period_data['SMA_50_Slope'].iloc[-1]),
            'rsi': float(period_data['RSI'].iloc[-1]),
            'macd': float(period_data['MACD'].iloc[-1]),
            'macd_signal': float(period_data['MACD_Signal'].iloc[-1]),
            'atr': float(period_data['ATR'].iloc[-1])
        }

        macro_data = {
            'SPX_Close': float(period_data['SPX_Close'].iloc[-1]) if 'SPX_Close' in period_data else 0.0,
            'SPX_Slope': float(period_data['SPX_Close'].diff().iloc[-1]) if 'SPX_Close' in period_data else 0.0,
            'VIX_Close': float(period_data['VIX_Close'].iloc[-1]) if 'VIX_Close' in period_data else 0.0,
            'VIX_Slope': float(period_data['VIX_Close'].diff().iloc[-1]) if 'VIX_Close' in period_data else 0.0,
            'GDP_QoQ': 0.0,
            'PMI': 50.0,
            'PPI_YoY': 0.0,
            'Treasury_YoY': 0.0
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
    os.makedirs('data/llm_strategies', exist_ok=True)
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

        # Assicurati che ci siano strategie
        if len(chunk_strategies) == 0:
            print(f"Warning: No strategies for chunk {chunk_id}, skipping")
            continue

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

    # Configurazione (usa Gemini invece di GPT)
    config = {
        'tickers': ['AAPL'],  # Start with one ticker for testing
        'llm': {
            'llm_model': 'gemini-2.0-flash-exp',  # Google Gemini 2.5 Flash
            'temperature': 0.0,
            'seed': 49,
            'gemini_api_key': os.getenv('GEMINI_API_KEY')  # Leggi da environment
        },
        'rewts': {
            'chunk_length': 500,  # Ridotto per testing
            'lookback_length': 100,
            'forecast_horizon': 1,
            'episodes_per_chunk': 20,  # Ridotto per testing
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
        with open(f"models/{ticker}_rewts_ensemble.pkl", 'wb') as f:
            pickle.dump(ensemble, f)

        print(f"\n✓ {ticker} complete!")

    print(f"\n{'='*60}")
    print("✓ All tickers processed successfully!")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
