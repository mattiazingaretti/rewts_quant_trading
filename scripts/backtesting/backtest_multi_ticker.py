"""
Multi-Ticker Backtest Script
Evaluates trained ReWTSE-LLM-RL ensemble on multiple tickers
"""

import sys
import os
import pickle
import numpy as np
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.rl_agents.trading_env import TradingEnv
from src.utils.data_utils import load_market_data, load_news_data
from backtesting.backtest_utils import (
    calculate_comprehensive_metrics,
    plot_multi_ticker_comparison,
    save_backtest_report
)


def evaluate_ticker(ticker, model_path, config):
    """
    Evaluate a trained ensemble on a specific ticker

    Args:
        ticker: Stock symbol
        model_path: Path to saved ensemble model
        config: Trading configuration

    Returns:
        Dictionary with evaluation results
    """

    print(f"\n{'='*60}")
    print(f"Evaluating {ticker}")
    print(f"{'='*60}")

    # Load model
    try:
        with open(model_path, 'rb') as f:
            ensemble = pickle.load(f)
        print(f"✓ Model loaded from {model_path}")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return None

    # Load strategies
    strategies_path = f"data/llm_strategies/{ticker}_strategies.pkl"
    try:
        with open(strategies_path, 'rb') as f:
            strategies = pickle.load(f)
        print(f"✓ Loaded {len(strategies)} strategies")
    except Exception as e:
        print(f"✗ Failed to load strategies: {e}")
        return None

    # Load market data
    try:
        market_df = load_market_data(ticker)
        print(f"✓ Loaded market data: {len(market_df)} days")
    except Exception as e:
        print(f"✗ Failed to load market data: {e}")
        return None

    # Create evaluation environment
    eval_env = TradingEnv(market_df, strategies, config)

    # Initialize weights (uniform)
    if len(ensemble.chunk_models) > 0:
        ensemble.current_weights = np.ones(len(ensemble.chunk_models)) / len(ensemble.chunk_models)

    # Run evaluation
    state = eval_env.reset()
    done = False
    total_reward = 0
    actions_taken = []

    while not done:
        # Get ensemble action
        action, _ = ensemble.predict_ensemble(state)
        actions_taken.append(action)

        # Execute action
        state, reward, done, _ = eval_env.step(action)
        total_reward += reward

    # Calculate metrics usando utility condivisa
    initial_balance = config.get('initial_balance', 10000)
    final_value = eval_env.portfolio_value

    metrics = calculate_comprehensive_metrics(eval_env.portfolio_history, initial_balance)

    # Action distribution
    action_names = ['SHORT', 'HOLD', 'LONG']
    action_counts = np.bincount(actions_taken, minlength=3)
    action_distribution = {
        name: {'count': int(action_counts[i]), 'pct': action_counts[i] / len(actions_taken) * 100}
        for i, name in enumerate(action_names)
    }

    # Print results
    print(f"\n{'='*60}")
    print(f"Results for {ticker}")
    print(f"{'='*60}")
    print(f"Initial Balance:     ${initial_balance:,.2f}")
    print(f"Final Portfolio:     ${final_value:,.2f}")
    print(f"Total Return:        {metrics['total_return']:.2%}")
    print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown:        {abs(metrics['max_drawdown']):.2%}")
    print(f"Volatility:          {metrics['volatility']:.2%}")
    print(f"Win Rate:            {metrics['win_rate']:.2%}")
    print(f"Avg Return/Trade:    {metrics['avg_return_per_trade']:.4%}")
    print(f"\nAction Distribution:")
    for name, stats in action_distribution.items():
        print(f"  {name:6s}: {stats['count']:4d} ({stats['pct']:5.1f}%)")
    print(f"{'='*60}")

    return {
        'ticker': ticker,
        'initial_balance': initial_balance,
        'final_value': final_value,
        'metrics': metrics,
        'action_distribution': action_distribution,
        'portfolio_history': eval_env.portfolio_history,
        'num_chunks': len(ensemble.chunk_models)
    }




def main():
    """Main backtest execution"""

    # Configuration
    tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA']

    config = {
        'initial_balance': 10000,
        'transaction_cost': 0.0015,
        'max_position': 0.95,
        'max_drawdown_limit': 0.15
    }

    print(f"{'='*80}")
    print("MULTI-TICKER BACKTEST")
    print(f"{'='*80}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Config: {config}")
    print(f"{'='*80}")

    # Evaluate each ticker
    results = []
    for ticker in tickers:
        model_path = f"models/{ticker}_rewts_ensemble.pkl"

        if not os.path.exists(model_path):
            print(f"\n⚠ Model not found for {ticker}: {model_path}")
            print(f"  Skipping {ticker}...")
            continue

        result = evaluate_ticker(ticker, model_path, config)

        if result is not None:
            results.append(result)

    if len(results) == 0:
        print("\n✗ No results to report. Train models first!")
        return

    # Save report and plots usando utility condivise
    save_backtest_report(results)
    plot_multi_ticker_comparison(results)

    print(f"\n{'='*80}")
    print("✓ Multi-ticker backtest complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
