"""
Script principale per training del sistema ReWTSE-LLM-RL
"""

import pandas as pd
import numpy as np
from tqdm import tqdm
import sys
import os
import pickle
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_agents.strategist_agent import StrategistAgent, TradingStrategy
from src.llm_agents.analyst_agent import AnalystAgent
from src.rl_agents.trading_env import TradingEnv
from src.hybrid_model.ensemble_controller import ReWTSEnsembleController
from src.utils.data_utils import load_market_data, load_news_data, filter_news_by_period
from src.utils.strategy_cache import StrategyCache
from src.utils.rate_limiter import RateLimiter, RequestMonitor, retry_with_exponential_backoff
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def load_data(ticker, config):
    """Carica dati preprocessati"""
    market_df = load_market_data(ticker)
    news_df = load_news_data(ticker)
    return market_df, news_df

def precompute_llm_strategies(ticker, market_df, news_df, config):
    """Pre-computa le strategie LLM per tutto il periodo con parallelizzazione"""

    print(f"\n{'='*60}")
    print(f"Pre-computing LLM Strategies for {ticker}")
    print(f"{'='*60}")

    # Inizializza cache
    cache = StrategyCache()
    cache_stats = cache.get_stats()
    print(f"Cache initialized: {cache_stats['total_entries']} entries, {cache_stats['cache_file_size_kb']} KB")

    # Inizializza rate limiter e monitor
    max_workers = config.get('parallel_workers', 8)
    max_requests_per_second = config.get('max_requests_per_second', 8.0)

    rate_limiter = RateLimiter(max_per_second=max_requests_per_second)
    monitor = RequestMonitor(window_seconds=60, limit_rpm=1000)

    skip_news = config.get('skip_news_processing', False)
    print(f"Parallel execution: {max_workers} workers, {max_requests_per_second} req/s max")
    if skip_news:
        print(f"⚠️  News processing DISABLED - using neutral sentiment (saves 50% API calls)")

    strategist = StrategistAgent(config['llm'])
    analyst = AnalystAgent(config['llm']) if not skip_news else None

    # Genera strategie mensili
    strategy_frequency = config.get('strategy_frequency', 20)
    num_strategies = len(market_df) // strategy_frequency

    # Prepara tutti i task params prima del loop parallelo
    print(f"Preparing {num_strategies} strategy generation tasks...")
    task_params = []

    for i in range(num_strategies):
        start_idx = i * strategy_frequency
        end_idx = min((i + 1) * strategy_frequency, len(market_df))

        # Dati per questa strategia
        period_data = market_df.iloc[start_idx:end_idx]

        # Filter news for this period
        period_news = filter_news_by_period(
            news_df,
            period_data.index[0],
            period_data.index[-1]
        )

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

        task_params.append({
            'task_id': i,
            'period_news': period_news,
            'market_data': market_data,
            'fundamentals': fundamentals,
            'analytics': analytics,
            'macro_data': macro_data
        })

    print(f"✓ Prepared {len(task_params)} tasks")

    # Funzione worker per generare una singola strategia
    def generate_single_strategy(params):
        """Worker function per generare una strategia con rate limiting"""
        task_id = params['task_id']
        period_news = params['period_news']
        market_data = params['market_data']
        fundamentals = params['fundamentals']
        analytics = params['analytics']
        macro_data = params['macro_data']

        # Process news (può essere cached anche questo)
        skip_news = config.get('skip_news_processing', False)

        if skip_news or len(period_news) == 0 or analyst is None:
            # Skip news processing (risparmia API calls)
            news_signals = {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'key_topics': []
            }
        else:
            news_signals = analyst.process_news(period_news.to_dict('records'))

        # Controlla cache
        cached_strategy = cache.get(
            ticker=ticker,
            market_data=market_data,
            fundamentals=fundamentals,
            analytics=analytics,
            macro_data=macro_data,
            news_signals=news_signals,
            model_name=config['llm']['llm_model'],
            temperature=config['llm']['temperature']
        )

        if cached_strategy is not None:
            return {
                'task_id': task_id,
                'strategy': TradingStrategy(**cached_strategy),
                'from_cache': True
            }

        # Non in cache, genera con rate limiting
        rate_limiter.wait()
        monitor.record_request()

        # Wrapper function per retry
        def _generate():
            return strategist.generate_strategy(
                market_data=market_data,
                fundamentals=fundamentals,
                analytics=analytics,
                macro_data=macro_data,
                news_signals=news_signals,
                last_strategy=None  # In parallelo non possiamo usare last_strategy
            )

        try:
            strategy = retry_with_exponential_backoff(
                _generate,
                max_retries=3,
                initial_wait=2.0,
                max_wait=30.0
            )

            # Salva in cache
            cache.set(
                ticker=ticker,
                market_data=market_data,
                fundamentals=fundamentals,
                analytics=analytics,
                macro_data=macro_data,
                news_signals=news_signals,
                model_name=config['llm']['llm_model'],
                temperature=config['llm']['temperature'],
                strategy=strategy
            )

            return {
                'task_id': task_id,
                'strategy': strategy,
                'from_cache': False
            }

        except Exception as e:
            print(f"❌ Failed to generate strategy {task_id}: {e}")
            # Fallback strategy
            return {
                'task_id': task_id,
                'strategy': TradingStrategy(
                    direction=1,
                    confidence=1.5,
                    strength=0.5,
                    explanation=f'Fallback strategy due to error: {str(e)}',
                    features_used=[],
                    timestamp=market_data.get('timestamp', 'N/A')
                ),
                'from_cache': False,
                'error': True
            }

    # Esegui in parallelo con ThreadPoolExecutor
    print(f"\n🚀 Starting parallel strategy generation...")
    start_time = time.time()

    strategies_dict = {}
    cache_hits = 0
    cache_misses = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tutti i task
        futures = {executor.submit(generate_single_strategy, params): params['task_id']
                   for params in task_params}

        # Progress bar
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            strategies_dict[result['task_id']] = result['strategy']

            if result['from_cache']:
                cache_hits += 1
            else:
                cache_misses += 1

            if result.get('error'):
                errors += 1

            completed += 1

            # Print progress ogni 10 strategie
            if completed % 10 == 0 or completed == len(task_params):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(task_params) - completed) / rate if rate > 0 else 0

                print(f"Progress: {completed}/{len(task_params)} "
                      f"({100*completed/len(task_params):.1f}%) | "
                      f"Rate: {rate:.1f} strat/s | "
                      f"ETA: {eta:.0f}s")

                # Print monitor stats ogni 20 strategie
                if completed % 20 == 0:
                    monitor.print_stats()

    # Riordina strategie per task_id
    strategies = [strategies_dict[i] for i in range(len(task_params))]

    elapsed_time = time.time() - start_time
    print(f"\n✓ Generated {len(strategies)} strategies in {elapsed_time:.1f}s")
    print(f"  Cache hits: {cache_hits} ({100*cache_hits/len(strategies):.1f}%)")
    print(f"  Cache misses: {cache_misses} ({100*cache_misses/len(strategies):.1f}%)")
    print(f"  Errors (fallback used): {errors}")
    print(f"  API calls saved: {cache_hits}")
    print(f"  Average time per strategy: {elapsed_time/len(strategies):.1f}s")
    monitor.print_stats()

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

def load_config(config_path='configs/hybrid/rewts_llm_rl.yaml'):
    """Load configuration from YAML file"""
    # Get project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    config_file = os.path.join(project_root, config_path)

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Resolve environment variables in config
    if 'llm' in config and 'gemini_api_key' in config['llm']:
        api_key_value = config['llm']['gemini_api_key']
        if isinstance(api_key_value, str) and api_key_value.startswith('${') and api_key_value.endswith('}'):
            env_var = api_key_value[2:-1]
            config['llm']['gemini_api_key'] = os.getenv(env_var)

    return config

def main():
    """Main training pipeline"""

    # Load configuration from YAML file
    print("Loading configuration from configs/hybrid/rewts_llm_rl.yaml...")
    config = load_config()

    # Print configuration summary
    print(f"\n{'='*60}")
    print("Configuration loaded:")
    print(f"  Tickers: {config['tickers']}")
    print(f"  LLM Model: {config['llm']['llm_model']}")
    print(f"  Project ID: {config['llm'].get('project_id', 'NOT SET')}")
    print(f"  Strategy Frequency: {config['strategy_frequency']} days")
    print(f"{'='*60}\n")

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
