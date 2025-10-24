"""
Multi-Ticker Backtest Script
Evaluates trained ReWTSE-LLM-RL ensemble on multiple tickers
"""

import sys
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.rl_agents.trading_env import TradingEnv
from src.utils.data_utils import load_market_data, load_news_data


def calculate_metrics(portfolio_history, initial_balance=10000):
    """
    Calculate comprehensive trading metrics

    Args:
        portfolio_history: List of portfolio values over time
        initial_balance: Starting capital

    Returns:
        Dictionary with all metrics
    """

    if len(portfolio_history) == 0:
        return {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'win_rate': 0.0,
            'avg_return_per_trade': 0.0
        }

    portfolio_values = np.array(portfolio_history)

    # Total return
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_balance) / initial_balance * 100

    # Returns (step-by-step)
    returns = np.diff(portfolio_values) / portfolio_values[:-1]

    # Filter out any NaN or Inf
    returns = returns[np.isfinite(returns)]

    if len(returns) == 0:
        return {
            'total_return': total_return,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'win_rate': 0.0,
            'avg_return_per_trade': 0.0
        }

    # Sharpe Ratio (annualized)
    if np.std(returns) > 0:
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
    else:
        sharpe_ratio = 0.0

    # Max Drawdown
    peak = np.maximum.accumulate(portfolio_values)
    drawdowns = (peak - portfolio_values) / peak
    max_drawdown = np.max(drawdowns) * 100

    # Volatility (annualized)
    volatility = np.std(returns) * np.sqrt(252) * 100

    # Win rate (% of positive returns)
    win_rate = (returns > 0).sum() / len(returns) * 100

    # Average return per trade
    avg_return_per_trade = np.mean(returns) * 100

    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'volatility': volatility,
        'win_rate': win_rate,
        'avg_return_per_trade': avg_return_per_trade
    }


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

    # Calculate metrics
    initial_balance = config.get('initial_balance', 10000)
    final_value = eval_env.portfolio_value

    metrics = calculate_metrics(eval_env.portfolio_history, initial_balance)

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
    print(f"Total Return:        {metrics['total_return']:.2f}%")
    print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown:        {metrics['max_drawdown']:.2f}%")
    print(f"Volatility:          {metrics['volatility']:.2f}%")
    print(f"Win Rate:            {metrics['win_rate']:.2f}%")
    print(f"Avg Return/Trade:    {metrics['avg_return_per_trade']:.4f}%")
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


def plot_comparison(results, save_path='results/multi_ticker_comparison.png'):
    """
    Plot comparison across multiple tickers

    Args:
        results: List of evaluation results
        save_path: Path to save plot
    """

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    sns.set_style('darkgrid')
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    tickers = [r['ticker'] for r in results]

    # 1. Total Return
    returns = [r['metrics']['total_return'] for r in results]
    axes[0, 0].bar(tickers, returns, color='steelblue', edgecolor='black')
    axes[0, 0].set_title('Total Return (%)', fontsize=14, fontweight='bold')
    axes[0, 0].axhline(y=0, color='red', linestyle='--')
    axes[0, 0].set_ylabel('Return (%)')

    # 2. Sharpe Ratio
    sharpes = [r['metrics']['sharpe_ratio'] for r in results]
    axes[0, 1].bar(tickers, sharpes, color='green', edgecolor='black')
    axes[0, 1].set_title('Sharpe Ratio', fontsize=14, fontweight='bold')
    axes[0, 1].axhline(y=1.0, color='red', linestyle='--', label='Target: 1.0')
    axes[0, 1].set_ylabel('Sharpe Ratio')
    axes[0, 1].legend()

    # 3. Max Drawdown
    drawdowns = [r['metrics']['max_drawdown'] for r in results]
    axes[0, 2].bar(tickers, drawdowns, color='red', edgecolor='black')
    axes[0, 2].set_title('Max Drawdown (%)', fontsize=14, fontweight='bold')
    axes[0, 2].set_ylabel('Drawdown (%)')

    # 4. Volatility
    vols = [r['metrics']['volatility'] for r in results]
    axes[1, 0].bar(tickers, vols, color='orange', edgecolor='black')
    axes[1, 0].set_title('Volatility (annualized %)', fontsize=14, fontweight='bold')
    axes[1, 0].axhline(y=15, color='red', linestyle='--', label='Target: <15%')
    axes[1, 0].set_ylabel('Volatility (%)')
    axes[1, 0].legend()

    # 5. Win Rate
    win_rates = [r['metrics']['win_rate'] for r in results]
    axes[1, 1].bar(tickers, win_rates, color='purple', edgecolor='black')
    axes[1, 1].set_title('Win Rate (%)', fontsize=14, fontweight='bold')
    axes[1, 1].axhline(y=50, color='red', linestyle='--', label='Neutral: 50%')
    axes[1, 1].set_ylabel('Win Rate (%)')
    axes[1, 1].legend()

    # 6. Portfolio Value Over Time (all tickers)
    for r in results:
        axes[1, 2].plot(r['portfolio_history'], label=r['ticker'], linewidth=2)
    axes[1, 2].set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
    axes[1, 2].set_xlabel('Trading Steps')
    axes[1, 2].set_ylabel('Portfolio Value ($)')
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Comparison plot saved to {save_path}")
    plt.close()


def save_report(results, save_path='results/backtest_report.csv'):
    """
    Save backtest results to CSV

    Args:
        results: List of evaluation results
        save_path: Path to save CSV
    """

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    data = []
    for r in results:
        row = {
            'Ticker': r['ticker'],
            'Initial_Balance': r['initial_balance'],
            'Final_Value': r['final_value'],
            'Total_Return_%': r['metrics']['total_return'],
            'Sharpe_Ratio': r['metrics']['sharpe_ratio'],
            'Max_Drawdown_%': r['metrics']['max_drawdown'],
            'Volatility_%': r['metrics']['volatility'],
            'Win_Rate_%': r['metrics']['win_rate'],
            'Avg_Return_Per_Trade_%': r['metrics']['avg_return_per_trade'],
            'Num_Chunks': r['num_chunks'],
            'SHORT_Count': r['action_distribution']['SHORT']['count'],
            'HOLD_Count': r['action_distribution']['HOLD']['count'],
            'LONG_Count': r['action_distribution']['LONG']['count']
        }
        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(save_path, index=False)
    print(f"✓ Report saved to {save_path}")

    # Print summary
    print(f"\n{'='*80}")
    print("MULTI-TICKER BACKTEST SUMMARY")
    print(f"{'='*80}")
    print(df.to_string(index=False))
    print(f"{'='*80}")

    # Aggregate statistics
    print(f"\nAGGREGATE STATISTICS:")
    print(f"  Average Sharpe Ratio:  {df['Sharpe_Ratio'].mean():.2f}")
    print(f"  Average Total Return:  {df['Total_Return_%'].mean():.2f}%")
    print(f"  Average Max Drawdown:  {df['Max_Drawdown_%'].mean():.2f}%")
    print(f"  Average Volatility:    {df['Volatility_%'].mean():.2f}%")
    print(f"  Average Win Rate:      {df['Win_Rate_%'].mean():.2f}%")
    print(f"{'='*80}")


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

    # Save report and plots
    save_report(results)
    plot_comparison(results)

    print(f"\n{'='*80}")
    print("✓ Multi-ticker backtest complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
