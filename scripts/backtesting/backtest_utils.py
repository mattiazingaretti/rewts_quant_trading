"""
Shared utilities for backtesting
Extracted common logic from backtest scripts to avoid duplication
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252):
    """
    Calculate annualized Sharpe Ratio

    Args:
        returns: Array/Series of returns
        risk_free_rate: Risk-free rate (default 0.0)
        periods_per_year: Trading periods per year (default 252)

    Returns:
        float: Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate
    return np.sqrt(periods_per_year) * (excess_returns.mean() / excess_returns.std())


def calculate_max_drawdown(portfolio_values):
    """
    Calculate Maximum Drawdown

    Args:
        portfolio_values: Array/Series of portfolio values over time

    Returns:
        float: Maximum drawdown (as decimal, e.g., -0.15 for 15% drawdown)
    """
    cumulative = pd.Series(portfolio_values) if not isinstance(portfolio_values, pd.Series) else portfolio_values
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()


def calculate_comprehensive_metrics(portfolio_history, initial_balance=10000):
    """
    Calculate comprehensive trading metrics

    Args:
        portfolio_history: List/array of portfolio values over time
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
            'avg_return_per_trade': 0.0,
            'final_value': initial_balance
        }

    portfolio_values = np.array(portfolio_history)

    # Total return
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_balance) / initial_balance

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
            'avg_return_per_trade': 0.0,
            'final_value': final_value
        }

    # Sharpe Ratio (annualized)
    sharpe_ratio = calculate_sharpe_ratio(returns)

    # Max Drawdown
    max_drawdown = calculate_max_drawdown(portfolio_values)

    # Volatility (annualized)
    volatility = np.std(returns) * np.sqrt(252)

    # Win rate (% of positive returns)
    win_rate = (returns > 0).sum() / len(returns)

    # Average return per trade
    avg_return_per_trade = np.mean(returns)

    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'volatility': volatility,
        'win_rate': win_rate,
        'avg_return_per_trade': avg_return_per_trade,
        'final_value': final_value
    }


def plot_backtest_results(ticker, metrics, save_path=None):
    """
    Visualize backtest results for a single ticker

    Args:
        ticker: Stock ticker symbol
        metrics: Dictionary with backtest metrics including:
                - portfolio_values: array of portfolio values
                - actions: array of actions taken
                - weights_history: array of model weights (optional)
        save_path: Path to save plot (if None, uses default)
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Portfolio value
    axes[0].plot(metrics['portfolio_values'], linewidth=2)
    axes[0].set_title(f"{ticker} - Portfolio Value Over Time", fontsize=14, fontweight='bold')
    axes[0].set_ylabel("Value ($)")
    axes[0].grid(True, alpha=0.3)

    # Actions
    actions = np.array(metrics['actions'])
    axes[1].scatter(range(len(actions)), actions, c=actions, cmap='RdYlGn', alpha=0.6, s=10)
    axes[1].set_title(f"{ticker} - Actions (0=SHORT, 1=HOLD, 2=LONG)", fontsize=14, fontweight='bold')
    axes[1].set_ylabel("Action")
    axes[1].set_ylim(-0.5, 2.5)
    axes[1].grid(True, alpha=0.3)

    # Weights evolution (if available)
    if 'weights_history' in metrics and len(metrics['weights_history']) > 0:
        weights_history = np.array(metrics['weights_history'])
        if weights_history.ndim > 1 and weights_history.shape[1] > 0:
            for i in range(weights_history.shape[1]):
                axes[2].plot(weights_history[:, i], label=f"Model {i+1}", alpha=0.7)
            axes[2].legend(loc='upper right')
            axes[2].set_title(f"{ticker} - Model Weights Over Time", fontsize=14, fontweight='bold')
        else:
            axes[2].text(0.5, 0.5, 'No weights data available',
                        ha='center', va='center', transform=axes[2].transAxes)
    else:
        axes[2].text(0.5, 0.5, 'No weights data available',
                    ha='center', va='center', transform=axes[2].transAxes)

    axes[2].set_ylabel("Weight")
    axes[2].set_xlabel("Time Step")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path is None:
        os.makedirs('results/visualizations', exist_ok=True)
        save_path = f"results/visualizations/{ticker}_backtest.png"

    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to {save_path}")


def plot_multi_ticker_comparison(results, save_path='results/multi_ticker_comparison.png'):
    """
    Plot comparison across multiple tickers

    Args:
        results: List of evaluation results, each containing:
                - ticker: ticker symbol
                - metrics: dict with performance metrics
                - portfolio_history: array of portfolio values
        save_path: Path to save plot
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    sns.set_style('darkgrid')
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    tickers = [r['ticker'] for r in results]

    # 1. Total Return
    returns = [r['metrics']['total_return'] * 100 for r in results]
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
    drawdowns = [abs(r['metrics']['max_drawdown']) * 100 for r in results]
    axes[0, 2].bar(tickers, drawdowns, color='red', edgecolor='black')
    axes[0, 2].set_title('Max Drawdown (%)', fontsize=14, fontweight='bold')
    axes[0, 2].set_ylabel('Drawdown (%)')

    # 4. Volatility
    vols = [r['metrics']['volatility'] * 100 for r in results]
    axes[1, 0].bar(tickers, vols, color='orange', edgecolor='black')
    axes[1, 0].set_title('Volatility (annualized %)', fontsize=14, fontweight='bold')
    axes[1, 0].axhline(y=15, color='red', linestyle='--', label='Target: <15%')
    axes[1, 0].set_ylabel('Volatility (%)')
    axes[1, 0].legend()

    # 5. Win Rate
    win_rates = [r['metrics']['win_rate'] * 100 for r in results]
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
    print(f"Comparison plot saved to {save_path}")
    plt.close()


def save_backtest_report(results, save_path='results/backtest_report.csv'):
    """
    Save backtest results to CSV with summary statistics

    Args:
        results: List of evaluation results
        save_path: Path to save CSV
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    data = []
    for r in results:
        row = {
            'Ticker': r['ticker'],
            'Initial_Balance': r.get('initial_balance', 10000),
            'Final_Value': r['metrics']['final_value'],
            'Total_Return_%': r['metrics']['total_return'] * 100,
            'Sharpe_Ratio': r['metrics']['sharpe_ratio'],
            'Max_Drawdown_%': abs(r['metrics']['max_drawdown']) * 100,
            'Volatility_%': r['metrics']['volatility'] * 100,
            'Win_Rate_%': r['metrics']['win_rate'] * 100,
            'Avg_Return_Per_Trade_%': r['metrics']['avg_return_per_trade'] * 100,
        }

        # Add optional fields if present
        if 'num_chunks' in r:
            row['Num_Chunks'] = r['num_chunks']
        if 'action_distribution' in r:
            row['SHORT_Count'] = r['action_distribution']['SHORT']['count']
            row['HOLD_Count'] = r['action_distribution']['HOLD']['count']
            row['LONG_Count'] = r['action_distribution']['LONG']['count']

        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(save_path, index=False)
    print(f"Report saved to {save_path}")

    # Print summary
    print(f"\n{'='*80}")
    print("BACKTEST SUMMARY")
    print(f"{'='*80}")
    print(df.to_string(index=False))
    print(f"{'='*80}")

    # Aggregate statistics
    if len(df) > 0:
        print(f"\nAGGREGATE STATISTICS:")
        print(f"  Average Sharpe Ratio:  {df['Sharpe_Ratio'].mean():.2f}")
        print(f"  Average Total Return:  {df['Total_Return_%'].mean():.2f}%")
        print(f"  Average Max Drawdown:  {df['Max_Drawdown_%'].mean():.2f}%")
        print(f"  Average Volatility:    {df['Volatility_%'].mean():.2f}%")
        print(f"  Average Win Rate:      {df['Win_Rate_%'].mean():.2f}%")
        print(f"{'='*80}")

    return df


def print_backtest_summary(ticker, metrics, initial_balance=10000):
    """
    Print formatted summary of backtest results

    Args:
        ticker: Stock ticker
        metrics: Dictionary with backtest metrics
        initial_balance: Starting balance
    """
    print(f"\n{'='*60}")
    print(f"Backtest Results for {ticker}")
    print(f"{'='*60}")
    print(f"Initial Balance:     ${initial_balance:,.2f}")
    print(f"Final Portfolio:     ${metrics['final_value']:,.2f}")
    print(f"Total Return:        {metrics['total_return']:.2%}")
    print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.4f}")
    print(f"Max Drawdown:        {metrics['max_drawdown']:.2%}")
    print(f"Volatility:          {metrics['volatility']:.2%}")
    print(f"Win Rate:            {metrics['win_rate']:.2%}")
    print(f"Avg Return/Trade:    {metrics['avg_return_per_trade']:.4%}")
    print(f"{'='*60}\n")
