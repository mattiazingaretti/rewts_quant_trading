"""
Regenerate LLM strategies for existing trained models
This script generates only the strategies without retraining the models
"""

import sys
import os
from pathlib import Path
import pickle
import yaml
import re
from dotenv import load_dotenv

# Add parent directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.llm_agents.strategist_agent_deepseek import StrategistAgent, TradingStrategy
from src.llm_agents.analyst_agent_deepseek import AnalystAgent
from src.utils.data_utils import load_market_data, load_news_data, filter_news_by_period
from src.utils.strategy_cache import StrategyCache
from src.utils.rate_limiter import RateLimiter, RequestMonitor, retry_with_exponential_backoff

import pandas as pd
import numpy as np
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def expand_env_vars(config):
    """Recursively expand ${VAR_NAME} placeholders in config dict"""
    if isinstance(config, dict):
        return {k: expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Replace ${VAR_NAME} with os.getenv('VAR_NAME')
        pattern = r'\$\{([^}]+)\}'
        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Keep original if not found
        return re.sub(pattern, replacer, config)
    else:
        return config


def generate_strategies_for_ticker(ticker, config):
    """Generate LLM strategies for a single ticker"""

    print(f"\n{'='*70}")
    print(f"Generating Strategies for {ticker}")
    print(f"{'='*70}")

    # Check if strategies already exist
    strategies_path = f"data/llm_strategies/{ticker}_strategies.pkl"
    if os.path.exists(strategies_path):
        print(f"⚠️  Strategies already exist: {strategies_path}")
        response = input(f"Overwrite? (y/n): ").lower()
        if response != 'y':
            print(f"Skipping {ticker}")
            return None

    # Load data
    print("Loading data...")
    market_df = load_market_data(ticker)
    news_df = load_news_data(ticker)
    print(f"✓ Market: {len(market_df)} days | News: {len(news_df)} articles")

    # Initialize agents
    cache = StrategyCache()
    max_workers = config.get('parallel_workers', 8)
    max_rps = config.get('max_requests_per_second', 8.0)
    skip_news = config.get('skip_news_processing', False)

    rate_limiter = RateLimiter(max_per_second=max_rps)
    monitor = RequestMonitor(window_seconds=60, limit_rpm=1000)

    strategist = StrategistAgent(config['llm'])
    analyst = AnalystAgent(config['llm']) if not skip_news else None

    # Prepare tasks
    strategy_frequency = config['strategy_frequency']
    num_strategies = len(market_df) // strategy_frequency

    print(f"\nPreparing {num_strategies} strategy generation tasks...")

    task_params = []
    for i in range(num_strategies):
        start_idx = i * strategy_frequency
        end_idx = min((i + 1) * strategy_frequency, len(market_df))
        period_data = market_df.iloc[start_idx:end_idx]
        period_news = filter_news_by_period(news_df, period_data.index[0], period_data.index[-1])

        # Prepare input data
        market_data = {
            'timestamp': str(period_data.index[-1]),
            'Close': float(period_data['Close'].iloc[-1]),
            'Volume': float(period_data['Volume'].iloc[-1]),
            'Weekly_Returns': period_data['Close'].pct_change().tail(20).tolist(),
            'HV_Close': float(period_data.get('HV_Close', pd.Series([0])).iloc[-1]),
            'Beta': 1.0,
            'Classification': 'Growth'
        }

        fundamentals = {
            'current_ratio': float(period_data.get('Current_Ratio', pd.Series([1.5])).iloc[-1]),
            'debt_to_equity': float(period_data.get('Debt_to_Equity', pd.Series([0.5])).iloc[-1]),
            'pe_ratio': float(period_data.get('PE_Ratio', pd.Series([20])).iloc[-1]),
            'gross_margin': float(period_data.get('Gross_Margin', pd.Series([0.4])).iloc[-1]),
            'operating_margin': float(period_data.get('Operating_Margin', pd.Series([0.2])).iloc[-1]),
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
            'SPX_Close': float(period_data.get('SPX_Close', pd.Series([0])).iloc[-1]),
            'VIX_Close': float(period_data.get('VIX_Close', pd.Series([0])).iloc[-1]),
            'GDP_QoQ': 0.0,
            'PMI': 50.0
        }

        task_params.append({
            'task_id': i,
            'period_news': period_news,
            'market_data': market_data,
            'fundamentals': fundamentals,
            'analytics': analytics,
            'macro_data': macro_data
        })

    # Worker function
    def generate_single_strategy(params):
        task_id = params['task_id']

        # Process news
        if skip_news or len(params['period_news']) == 0 or analyst is None:
            news_signals = {'sentiment': 'neutral', 'confidence': 0.5, 'key_topics': []}
        else:
            news_signals = analyst.process_news(params['period_news'].to_dict('records'))

        # Check cache
        cached = cache.get(
            ticker=ticker,
            market_data=params['market_data'],
            fundamentals=params['fundamentals'],
            analytics=params['analytics'],
            macro_data=params['macro_data'],
            news_signals=news_signals,
            model_name=config['llm']['llm_model'],
            temperature=config['llm']['temperature']
        )

        if cached is not None:
            return {'task_id': task_id, 'strategy': TradingStrategy(**cached), 'from_cache': True}

        # Generate with rate limiting
        rate_limiter.wait()
        monitor.record_request()

        try:
            strategy = retry_with_exponential_backoff(
                lambda: strategist.generate_strategy(
                    market_data=params['market_data'],
                    fundamentals=params['fundamentals'],
                    analytics=params['analytics'],
                    macro_data=params['macro_data'],
                    news_signals=news_signals,
                    last_strategy=None
                ),
                max_retries=3,
                initial_wait=2.0,
                max_wait=30.0
            )

            # Save to cache
            cache.set(
                ticker=ticker,
                market_data=params['market_data'],
                fundamentals=params['fundamentals'],
                analytics=params['analytics'],
                macro_data=params['macro_data'],
                news_signals=news_signals,
                model_name=config['llm']['llm_model'],
                temperature=config['llm']['temperature'],
                strategy=strategy
            )

            return {'task_id': task_id, 'strategy': strategy, 'from_cache': False}

        except Exception as e:
            print(f"\n❌ Failed strategy {task_id}: {e}")
            return {
                'task_id': task_id,
                'strategy': TradingStrategy(
                    direction=1, confidence=1.5, strength=0.5,
                    explanation=f'Fallback: {str(e)}',
                    features_used=[], timestamp=params['market_data']['timestamp']
                ),
                'from_cache': False, 'error': True
            }

    # Execute in parallel
    print(f"\n🚀 Starting parallel generation...")
    start_time = time.time()

    strategies_dict = {}
    cache_hits = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(generate_single_strategy, p): p['task_id'] for p in task_params}

        with tqdm(total=len(task_params), desc=f"Generating {ticker}") as pbar:
            for future in as_completed(futures):
                result = future.result()
                strategies_dict[result['task_id']] = result['strategy']
                if result['from_cache']:
                    cache_hits += 1
                pbar.update(1)

    # Reorder strategies
    strategies = [strategies_dict[i] for i in range(len(task_params))]

    elapsed = time.time() - start_time
    print(f"\n✓ Generated {len(strategies)} strategies in {elapsed:.1f}s")
    print(f"  Cache hits: {cache_hits} ({100*cache_hits/len(strategies):.1f}%)")
    print(f"  API calls saved: {cache_hits}")

    # Save strategies
    os.makedirs('data/llm_strategies', exist_ok=True)
    with open(strategies_path, 'wb') as f:
        pickle.dump(strategies, f)
    print(f"✓ Saved to {strategies_path}")

    return strategies


def main():
    """Main regeneration script"""

    import argparse
    parser = argparse.ArgumentParser(description='Regenerate LLM strategies')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    parser.add_argument('--tickers', nargs='+', help='Specific tickers to regenerate')
    parser.add_argument('--config', default='configs/hybrid/rewts_llm_rl.yaml', help='Path to config YAML')
    parser.add_argument('--use-deepseek', action='store_true', help='Use DeepSeek instead of Gemini')
    parser.add_argument('--env-file', help='Path to .env file (default: .env or .env.example)')
    args = parser.parse_args()

    # Load environment variables from .env file
    env_file = args.env_file
    if not env_file:
        if Path('.env').exists():
            env_file = '.env'
        
    if env_file:
        load_dotenv(env_file)
        print(f"✓ Loaded environment variables from: {env_file}")
    else:
        print("⚠️  No .env file found, using system environment variables")

    # Load configuration from YAML
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        # Expand ${VAR_NAME} placeholders
        config = expand_env_vars(config)
        print(f"✓ Loaded config from: {config_path}")
    else:
        print(f"⚠️  Config not found: {config_path}")
        print("   Using default configuration")
        config = {
            'strategy_frequency': 20,
            'parallel_workers': 8,
            'max_requests_per_second': 8.0,
            'skip_news_processing': False
        }

    # Override LLM config for DeepSeek if requested
    if args.use_deepseek:
        print("🔄 Using DeepSeek LLM (forced via --use-deepseek)")
        config['llm']['llm_model'] = 'deepseek-chat'
        config['llm']['deepseek_api_key'] = os.getenv('DEEPSEEK_API_KEY')

    # Check if using DeepSeek model
    if 'deepseek' in config.get('llm', {}).get('llm_model', '').lower():
        print("✓ Using DeepSeek LLM")
        # Ensure API key is set
        if not config['llm'].get('deepseek_api_key'):
            config['llm']['deepseek_api_key'] = os.getenv('DEEPSEEK_API_KEY')

        # DeepSeek models were trained with strategy_frequency=20
        if config.get('strategy_frequency') != 20:
            print(f"  ⚠️  Overriding strategy_frequency: {config.get('strategy_frequency')} → 20")
            print(f"     (DeepSeek models were trained with frequency=20)")
            config['strategy_frequency'] = 20
    elif 'llm' not in config:
        # Fallback if no LLM config at all
        print("⚠️  No LLM config found, defaulting to DeepSeek")
        config['llm'] = {
            'llm_model': 'deepseek-chat',
            'temperature': 0.0,
            'deepseek_api_key': os.getenv('DEEPSEEK_API_KEY'),
        }
        config['strategy_frequency'] = 20

    # Check API key
    api_key_field = 'deepseek_api_key' if 'deepseek' in config['llm']['llm_model'] else 'gemini_api_key'
    if not config['llm'].get(api_key_field):
        print(f"❌ API key not set: {api_key_field}")
        if 'deepseek' in config['llm']['llm_model']:
            print("Set it with: export DEEPSEEK_API_KEY='sk-...'")
        else:
            print("Set it with: export GEMINI_API_KEY='...'")
        return

    # Print configuration summary
    print("\n" + "="*70)
    print("Configuration Summary:")
    print("="*70)
    print(f"  LLM Model: {config['llm']['llm_model']}")
    print(f"  Strategy Frequency: {config['strategy_frequency']} trading days")
    print(f"  Parallel Workers: {config.get('parallel_workers', 8)}")
    print(f"  Max Requests/sec: {config.get('max_requests_per_second', 8.0)}")
    print(f"  Skip News: {config.get('skip_news_processing', False)}")
    print("="*70)

    # Find tickers with models but no strategies
    print("\n" + "="*70)
    print("STRATEGY REGENERATION TOOL")
    print("="*70)

    models_dir = Path("models")
    strategies_dir = Path("data/llm_strategies")

    if not models_dir.exists():
        print("❌ No models directory found!")
        return

    # Find tickers
    model_files = list(models_dir.glob("*_rewts_ensemble.pkl"))
    tickers_with_models = [f.stem.replace('_rewts_ensemble', '') for f in model_files]

    tickers_missing_strategies = []
    for ticker in tickers_with_models:
        strategy_file = strategies_dir / f"{ticker}_strategies.pkl"
        if not strategy_file.exists():
            tickers_missing_strategies.append(ticker)

    print(f"\nModels found: {len(tickers_with_models)}")
    print(f"Missing strategies: {len(tickers_missing_strategies)}")

    if len(tickers_missing_strategies) == 0:
        print("\n✓ All tickers have strategies!")
        return

    print(f"\nTickers missing strategies: {tickers_missing_strategies}")
    print(f"\n💰 Estimated cost: ~${0.035 * len(tickers_missing_strategies):.3f}")
    print(f"   (~$0.035 per ticker with cache)")

    if not args.yes:
        response = input("\nProceed with generation? (y/n): ").lower()
        if response != 'y':
            print("Cancelled.")
            return

    # Filter tickers if specified
    if args.tickers:
        tickers_missing_strategies = [t for t in tickers_missing_strategies if t in args.tickers]
        print(f"\n📌 Filtering to: {tickers_missing_strategies}")

    # Generate strategies
    for ticker in tickers_missing_strategies:
        try:
            generate_strategies_for_ticker(ticker, config)
        except Exception as e:
            print(f"\n❌ Error generating {ticker}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*70}")
    print("✓ REGENERATION COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
