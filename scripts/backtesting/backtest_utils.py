"""
Shared utilities for backtesting
Extracted common logic from backtest scripts to avoid duplication
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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


def calculate_extended_metrics(market_df, start_idx=0, end_idx=None):
    """
    Calculate extended technical, fundamental, and macro metrics from market data

    Args:
        market_df: DataFrame with market data including technical indicators
        start_idx: Start index for the backtest period
        end_idx: End index for the backtest period (None = end of data)

    Returns:
        Dictionary with extended metrics averages/stats during backtest period
    """
    if end_idx is None:
        end_idx = len(market_df)

    # Extract backtest period data
    backtest_data = market_df.iloc[start_idx:end_idx]

    if len(backtest_data) == 0:
        return {}

    extended_metrics = {}

    # Technical Indicators - Average values during backtest
    technical_columns = ['RSI', 'MACD', 'MACD_Hist', 'ATR', 'HV_Close',
                        'SMA_20', 'SMA_50', 'SMA_200',
                        'SMA_20_Slope', 'SMA_50_Slope', 'SMA_200_Slope']

    for col in technical_columns:
        if col in backtest_data.columns:
            values = backtest_data[col].dropna()
            if len(values) > 0:
                extended_metrics[f'{col}_avg'] = values.mean()
                extended_metrics[f'{col}_std'] = values.std()

    # Calculate Beta (correlation with SPX)
    if 'Close' in backtest_data.columns and 'SPX_Close' in backtest_data.columns:
        stock_returns = backtest_data['Close'].pct_change().dropna()
        spx_returns = backtest_data['SPX_Close'].pct_change().dropna()

        # Align the series
        aligned = pd.DataFrame({'stock': stock_returns, 'spx': spx_returns}).dropna()

        if len(aligned) > 1:
            covariance = aligned['stock'].cov(aligned['spx'])
            spx_variance = aligned['spx'].var()

            if spx_variance > 0:
                extended_metrics['Beta'] = covariance / spx_variance
            else:
                extended_metrics['Beta'] = 0.0
        else:
            extended_metrics['Beta'] = 0.0

    # Macro Indicators - Average values during backtest
    macro_columns = ['VIX_Close', 'SPX_Close']

    for col in macro_columns:
        if col in backtest_data.columns:
            values = backtest_data[col].dropna()
            if len(values) > 0:
                extended_metrics[f'{col}_avg'] = values.mean()
                extended_metrics[f'{col}_std'] = values.std()
                extended_metrics[f'{col}_min'] = values.min()
                extended_metrics[f'{col}_max'] = values.max()

    # Fundamental Ratios - Average values during backtest
    fundamental_columns = ['PE_Ratio', 'Debt_to_Equity', 'Current_Ratio',
                          'ROE', 'Gross_Margin', 'Operating_Margin']

    for col in fundamental_columns:
        if col in backtest_data.columns:
            values = backtest_data[col].dropna()
            if len(values) > 0:
                extended_metrics[f'{col}_avg'] = values.mean()

    # Price metrics
    if 'Close' in backtest_data.columns:
        close_prices = backtest_data['Close']
        extended_metrics['Price_Start'] = close_prices.iloc[0]
        extended_metrics['Price_End'] = close_prices.iloc[-1]
        extended_metrics['Price_Change_%'] = ((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100
        extended_metrics['Price_Max'] = close_prices.max()
        extended_metrics['Price_Min'] = close_prices.min()

    # Volume analysis
    if 'Volume' in backtest_data.columns:
        volumes = backtest_data['Volume']
        extended_metrics['Avg_Volume'] = volumes.mean()

    return extended_metrics


def plot_backtest_results(ticker, metrics, save_path=None):
    """
    Visualize backtest results for a single ticker

    Args:
        ticker: Stock ticker symbol
        metrics: Dictionary with backtest metrics including:
                - portfolio_values: array of portfolio values
                - actions: array of actions taken
                - weights_history: array of model weights (optional)
                - dates: list of dates (optional)
        save_path: Path to save plot (if None, uses default)
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Check if we have dates for x-axis
    has_dates = 'dates' in metrics and metrics['dates'] is not None and len(metrics['dates']) > 0

    # Prepare x-axis data
    if has_dates:
        dates = pd.to_datetime(metrics['dates'], utc=True).tz_localize(None)
        # Portfolio values has one extra point (initial value), so use dates with first date prepended
        portfolio_dates = pd.DatetimeIndex([dates[0]] + dates.tolist())
        action_dates = dates

    # Portfolio value
    if has_dates:
        axes[0].plot(portfolio_dates[:len(metrics['portfolio_values'])], metrics['portfolio_values'], linewidth=2)
        axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        axes[0].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        fig.autofmt_xdate()
    else:
        axes[0].plot(metrics['portfolio_values'], linewidth=2)
    axes[0].set_title(f"{ticker} - Portfolio Value Over Time", fontsize=14, fontweight='bold')
    axes[0].set_ylabel("Value ($)")
    axes[0].grid(True, alpha=0.3)

    # Actions
    actions = np.array(metrics['actions'])
    if has_dates:
        axes[1].scatter(action_dates[:len(actions)], actions, c=actions, cmap='RdYlGn', alpha=0.6, s=10)
        axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        axes[1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    else:
        axes[1].scatter(range(len(actions)), actions, c=actions, cmap='RdYlGn', alpha=0.6, s=10)
    axes[1].set_title(f"{ticker} - Actions (0=SHORT, 1=HOLD, 2=LONG)", fontsize=14, fontweight='bold')
    axes[1].set_ylabel("Action")
    axes[1].set_ylim(-0.5, 2.5)
    axes[1].grid(True, alpha=0.3)

    # Weights evolution (if available)
    if 'weights_history' in metrics and len(metrics['weights_history']) > 0:
        weights_history = np.array(metrics['weights_history'])
        if weights_history.ndim > 1 and weights_history.shape[1] > 0:
            if has_dates:
                weight_dates = action_dates[:len(weights_history)]
                for i in range(weights_history.shape[1]):
                    axes[2].plot(weight_dates, weights_history[:, i], label=f"Model {i+1}", alpha=0.7)
                axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                axes[2].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            else:
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
    axes[2].set_xlabel("Date" if has_dates else "Time Step")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path is None:
        os.makedirs('results/visualizations', exist_ok=True)
        save_path = f"results/visualizations/{ticker}_backtest.png"

    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to {save_path}")


def plot_extended_metrics_dashboard(results, save_path='results/extended_metrics_dashboard.png'):
    """
    Plot extended metrics dashboard showing technical, fundamental, and macro indicators

    Args:
        results: List of evaluation results with extended_metrics
        save_path: Path to save plot
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Filter results that have extended metrics
    results_with_ext = [r for r in results if 'extended_metrics' in r and r['extended_metrics']]

    if len(results_with_ext) == 0:
        print("No extended metrics available for visualization")
        return

    sns.set_style('darkgrid')
    fig, axes = plt.subplots(3, 3, figsize=(20, 14))
    fig.suptitle('Extended Metrics Dashboard - Technical, Fundamental & Macro Analysis',
                 fontsize=16, fontweight='bold', y=0.995)

    tickers = [r['ticker'] for r in results_with_ext]

    # Row 1: Technical Indicators
    # 1.1 RSI Average
    rsi_values = [r['extended_metrics'].get('RSI_avg', None) for r in results_with_ext]
    if any(v is not None for v in rsi_values):
        rsi_values = [v if v is not None else 0 for v in rsi_values]
        axes[0, 0].bar(tickers, rsi_values, color='purple', edgecolor='black')
        axes[0, 0].axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought')
        axes[0, 0].axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold')
        axes[0, 0].axhline(y=50, color='gray', linestyle=':', alpha=0.5)
        axes[0, 0].set_title('Average RSI', fontweight='bold')
        axes[0, 0].set_ylabel('RSI')
        axes[0, 0].legend()
        axes[0, 0].set_ylim(0, 100)

    # 1.2 Beta
    beta_values = [r['extended_metrics'].get('Beta', None) for r in results_with_ext]
    if any(v is not None for v in beta_values):
        beta_values = [v if v is not None else 0 for v in beta_values]
        colors = ['red' if b > 1 else 'green' if b < 1 else 'gray' for b in beta_values]
        axes[0, 1].bar(tickers, beta_values, color=colors, edgecolor='black')
        axes[0, 1].axhline(y=1.0, color='black', linestyle='--', linewidth=2, label='Market Beta')
        axes[0, 1].set_title('Beta (Market Correlation)', fontweight='bold')
        axes[0, 1].set_ylabel('Beta')
        axes[0, 1].legend()

    # 1.3 Historical Volatility
    hv_values = [r['extended_metrics'].get('HV_Close_avg', None) for r in results_with_ext]
    if any(v is not None for v in hv_values):
        hv_values = [(v * 100) if v is not None else 0 for v in hv_values]
        axes[0, 2].bar(tickers, hv_values, color='orange', edgecolor='black')
        axes[0, 2].set_title('Average Historical Volatility', fontweight='bold')
        axes[0, 2].set_ylabel('Volatility (%)')

    # Row 2: Fundamental Metrics
    # 2.1 P/E Ratio
    pe_values = [r['extended_metrics'].get('PE_Ratio_avg', None) for r in results_with_ext]
    if any(v is not None for v in pe_values):
        pe_values = [v if v is not None else 0 for v in pe_values]
        axes[1, 0].bar(tickers, pe_values, color='steelblue', edgecolor='black')
        axes[1, 0].axhline(y=25, color='red', linestyle='--', alpha=0.7, label='High P/E')
        axes[1, 0].axhline(y=15, color='green', linestyle='--', alpha=0.7, label='Low P/E')
        axes[1, 0].set_title('Average P/E Ratio', fontweight='bold')
        axes[1, 0].set_ylabel('P/E Ratio')
        axes[1, 0].legend()

    # 2.2 ROE
    roe_values = [r['extended_metrics'].get('ROE_avg', None) for r in results_with_ext]
    if any(v is not None for v in roe_values):
        roe_values = [(v * 100) if v is not None else 0 for v in roe_values]
        axes[1, 1].bar(tickers, roe_values, color='green', edgecolor='black')
        axes[1, 1].axhline(y=15, color='red', linestyle='--', alpha=0.7, label='Target: >15%')
        axes[1, 1].set_title('Average ROE', fontweight='bold')
        axes[1, 1].set_ylabel('ROE (%)')
        axes[1, 1].legend()

    # 2.3 Debt to Equity
    de_values = [r['extended_metrics'].get('Debt_to_Equity_avg', None) for r in results_with_ext]
    if any(v is not None for v in de_values):
        de_values = [v if v is not None else 0 for v in de_values]
        colors = ['red' if d > 2 else 'orange' if d > 1 else 'green' for d in de_values]
        axes[1, 2].bar(tickers, de_values, color=colors, edgecolor='black')
        axes[1, 2].axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='Moderate')
        axes[1, 2].axhline(y=2.0, color='red', linestyle='--', alpha=0.7, label='High Risk')
        axes[1, 2].set_title('Average Debt-to-Equity', fontweight='bold')
        axes[1, 2].set_ylabel('Debt/Equity Ratio')
        axes[1, 2].legend()

    # Row 3: Macro & Performance
    # 3.1 VIX Average
    vix_values = [r['extended_metrics'].get('VIX_Close_avg', None) for r in results_with_ext]
    if any(v is not None for v in vix_values):
        vix_values = [v if v is not None else 0 for v in vix_values]
        axes[2, 0].bar(tickers, vix_values, color='crimson', edgecolor='black')
        axes[2, 0].axhline(y=15, color='green', linestyle='--', alpha=0.7, label='Low Fear')
        axes[2, 0].axhline(y=25, color='orange', linestyle='--', alpha=0.7, label='Elevated')
        axes[2, 0].axhline(y=40, color='red', linestyle='--', alpha=0.7, label='Panic')
        axes[2, 0].set_title('Average VIX (Fear Index)', fontweight='bold')
        axes[2, 0].set_ylabel('VIX')
        axes[2, 0].legend()

    # 3.2 Stock Price Change %
    price_change = [r['extended_metrics'].get('Price_Change_%', None) for r in results_with_ext]
    if any(v is not None for v in price_change):
        price_change = [v if v is not None else 0 for v in price_change]
        colors = ['green' if p > 0 else 'red' for p in price_change]
        axes[2, 1].bar(tickers, price_change, color=colors, edgecolor='black')
        axes[2, 1].axhline(y=0, color='black', linestyle='-', linewidth=1)
        axes[2, 1].set_title('Stock Price Change %', fontweight='bold')
        axes[2, 1].set_ylabel('Price Change (%)')

    # 3.3 Portfolio Return vs Stock Return
    portfolio_returns = [r['metrics']['total_return'] * 100 for r in results_with_ext]
    stock_returns = [r['extended_metrics'].get('Price_Change_%', 0) for r in results_with_ext]

    x = np.arange(len(tickers))
    width = 0.35

    axes[2, 2].bar(x - width/2, portfolio_returns, width, label='Portfolio Return',
                   color='steelblue', edgecolor='black')
    axes[2, 2].bar(x + width/2, stock_returns, width, label='Stock Price Change',
                   color='lightcoral', edgecolor='black')
    axes[2, 2].set_title('Portfolio vs Stock Performance', fontweight='bold')
    axes[2, 2].set_ylabel('Return (%)')
    axes[2, 2].set_xticks(x)
    axes[2, 2].set_xticklabels(tickers)
    axes[2, 2].legend()
    axes[2, 2].axhline(y=0, color='black', linestyle='-', linewidth=1)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Extended metrics dashboard saved to {save_path}")
    plt.close()


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

        # Add extended metrics if present
        if 'extended_metrics' in r:
            ext = r['extended_metrics']

            # Technical indicators
            if 'RSI_avg' in ext:
                row['RSI_Avg'] = ext['RSI_avg']
            if 'MACD_avg' in ext:
                row['MACD_Avg'] = ext['MACD_avg']
            if 'ATR_avg' in ext:
                row['ATR_Avg'] = ext['ATR_avg']
            if 'HV_Close_avg' in ext:
                row['Historical_Volatility_Avg'] = ext['HV_Close_avg']
            if 'Beta' in ext:
                row['Beta'] = ext['Beta']

            # Fundamental metrics
            if 'PE_Ratio_avg' in ext:
                row['PE_Ratio_Avg'] = ext['PE_Ratio_avg']
            if 'Debt_to_Equity_avg' in ext:
                row['Debt_to_Equity_Avg'] = ext['Debt_to_Equity_avg']
            if 'Current_Ratio_avg' in ext:
                row['Current_Ratio_Avg'] = ext['Current_Ratio_avg']
            if 'ROE_avg' in ext:
                row['ROE_Avg_%'] = ext['ROE_avg'] * 100 if ext['ROE_avg'] else None
            if 'Gross_Margin_avg' in ext:
                row['Gross_Margin_Avg_%'] = ext['Gross_Margin_avg'] * 100 if ext['Gross_Margin_avg'] else None
            if 'Operating_Margin_avg' in ext:
                row['Operating_Margin_Avg_%'] = ext['Operating_Margin_avg'] * 100 if ext['Operating_Margin_avg'] else None

            # Macro indicators
            if 'VIX_Close_avg' in ext:
                row['VIX_Avg'] = ext['VIX_Close_avg']
            if 'SPX_Close_avg' in ext:
                row['SPX_Avg'] = ext['SPX_Close_avg']

            # Price metrics
            if 'Price_Start' in ext:
                row['Price_Start'] = ext['Price_Start']
            if 'Price_End' in ext:
                row['Price_End'] = ext['Price_End']
            if 'Price_Change_%' in ext:
                row['Stock_Price_Change_%'] = ext['Price_Change_%']

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
