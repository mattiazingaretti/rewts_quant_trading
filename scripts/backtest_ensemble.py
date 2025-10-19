"""
Backtesting script per ReWTSE-LLM-RL ensemble
"""

import pandas as pd
import numpy as np
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rl_agents.trading_env import TradingEnv

def calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252):
    """Calcola Sharpe Ratio annualizzato"""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate
    return np.sqrt(periods_per_year) * (excess_returns.mean() / excess_returns.std())

def calculate_max_drawdown(portfolio_values):
    """Calcola Maximum Drawdown"""
    cumulative = pd.Series(portfolio_values)
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()

def backtest_ensemble(ticker, ensemble, market_df, strategies, config):
    """
    Backtest del ReWTSE ensemble su test set

    Returns:
        Dict con metriche di performance
    """

    print(f"\n{'='*60}")
    print(f"Backtesting {ticker}")
    print(f"{'='*60}")

    # Split train/test
    train_size = int(0.7 * len(market_df))
    test_df = market_df.iloc[train_size:].copy()
    test_strategies = strategies[train_size // config['strategy_frequency']:]

    if len(test_strategies) == 0:
        print("Warning: No test strategies available")
        return None

    # Crea environment di test
    test_env = TradingEnv(test_df, test_strategies, config['trading_env'])

    # Inizializza
    state = test_env.reset()
    done = False

    lookback_length = config['rewts']['lookback_length']
    lookback_buffer = []

    portfolio_values = [test_env.initial_balance]
    actions_taken = []
    weights_history = []

    step = 0

    with tqdm(total=len(test_df), desc="Backtesting") as pbar:
        while not done:
            # Accumula look-back data
            lookback_buffer.append(state)
            if len(lookback_buffer) > lookback_length:
                lookback_buffer.pop(0)

            # Ottimizza pesi se abbiamo abbastanza look-back data
            if len(lookback_buffer) == lookback_length and len(ensemble.chunk_models) > 0:
                # Estrai returns dal look-back
                lookback_returns = []
                for i in range(len(lookback_buffer) - 1):
                    if step - lookback_length + i + 1 < len(test_df) and step - lookback_length + i < len(test_df):
                        ret = (test_df.iloc[step - lookback_length + i + 1]['Close'] /
                               test_df.iloc[step - lookback_length + i]['Close']) - 1
                        lookback_returns.append(ret)

                if len(lookback_returns) > 0:
                    # Ottimizza pesi
                    weights = ensemble.optimize_weights(lookback_buffer, lookback_returns)
                    ensemble.current_weights = weights
                    weights_history.append(weights)
            else:
                # Usa uniform weights
                num_models = len(ensemble.chunk_models) if ensemble.chunk_models else 1
                weights = np.ones(num_models) / num_models
                ensemble.current_weights = weights
                weights_history.append(weights)

            # Predizione ensemble
            action, q_values = ensemble.predict_ensemble(state)

            # Execute action
            next_state, reward, done, _ = test_env.step(action)

            # Track
            portfolio_values.append(test_env.portfolio_value)
            actions_taken.append(action)

            state = next_state
            step += 1
            pbar.update(1)

    # Calcola metriche
    portfolio_values = np.array(portfolio_values)
    returns = np.diff(portfolio_values) / portfolio_values[:-1]
    returns = returns[np.isfinite(returns)]  # Remove any inf/nan

    sharpe_ratio = calculate_sharpe_ratio(returns)
    max_drawdown = calculate_max_drawdown(portfolio_values)
    cumulative_return = (portfolio_values[-1] / portfolio_values[0]) - 1

    metrics = {
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'cumulative_return': cumulative_return,
        'final_portfolio_value': portfolio_values[-1],
        'portfolio_values': portfolio_values,
        'actions': actions_taken,
        'weights_history': weights_history
    }

    print(f"\n{'='*60}")
    print(f"Backtest Results for {ticker}")
    print(f"{'='*60}")
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"Max Drawdown: {max_drawdown:.4f}")
    print(f"Cumulative Return: {cumulative_return:.2%}")
    print(f"Final Portfolio Value: ${portfolio_values[-1]:.2f}")

    return metrics

def plot_results(ticker, metrics):
    """Visualizza risultati backtest"""

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Portfolio value
    axes[0].plot(metrics['portfolio_values'])
    axes[0].set_title(f"{ticker} - Portfolio Value")
    axes[0].set_ylabel("Value ($)")
    axes[0].grid(True)

    # Actions
    actions = np.array(metrics['actions'])
    axes[1].scatter(range(len(actions)), actions, c=actions, cmap='RdYlGn', alpha=0.6)
    axes[1].set_title(f"{ticker} - Actions (0=SHORT, 1=HOLD, 2=LONG)")
    axes[1].set_ylabel("Action")
    axes[1].set_ylim(-0.5, 2.5)
    axes[1].grid(True)

    # Weights evolution
    weights_history = np.array(metrics['weights_history'])
    if weights_history.ndim > 1 and weights_history.shape[1] > 0:
        for i in range(weights_history.shape[1]):
            axes[2].plot(weights_history[:, i], label=f"Model {i+1}", alpha=0.7)
        axes[2].legend(loc='upper right')
    axes[2].set_title(f"{ticker} - Model Weights Over Time")
    axes[2].set_ylabel("Weight")
    axes[2].set_xlabel("Time Step")
    axes[2].grid(True)

    plt.tight_layout()
    os.makedirs('results/visualizations', exist_ok=True)
    plt.savefig(f"results/visualizations/{ticker}_backtest.png", dpi=300)
    plt.close()

    print(f"✓ Plot saved to results/visualizations/{ticker}_backtest.png")

def main():
    """Main backtesting pipeline"""

    config = {
        'tickers': ['AAPL'],
        'rewts': {
            'chunk_length': 500,
            'lookback_length': 100,
            'forecast_horizon': 1
        },
        'trading_env': {
            'initial_balance': 10000,
            'transaction_cost': 0.001,
            'max_position': 1.0
        },
        'strategy_frequency': 20
    }

    all_metrics = {}

    for ticker in config['tickers']:
        # Load ensemble
        try:
            with open(f"models/{ticker}_rewts_ensemble.pkl", 'rb') as f:
                ensemble = pickle.load(f)
        except FileNotFoundError:
            print(f"Error: Model file not found for {ticker}")
            continue

        # Load data e strategies
        market_df = pd.read_csv(f"data/processed/{ticker}_full_data.csv", index_col=0, parse_dates=True)
        with open(f"data/llm_strategies/{ticker}_strategies.pkl", 'rb') as f:
            strategies = pickle.load(f)

        # Backtest
        metrics = backtest_ensemble(ticker, ensemble, market_df, strategies, config)

        if metrics:
            all_metrics[ticker] = metrics

            # Plot
            plot_results(ticker, metrics)

    # Summary table
    if all_metrics:
        print(f"\n{'='*60}")
        print("Summary Across All Tickers")
        print(f"{'='*60}")

        summary_df = pd.DataFrame({
            ticker: {
                'Sharpe Ratio': metrics['sharpe_ratio'],
                'Max Drawdown': metrics['max_drawdown'],
                'Cumulative Return': metrics['cumulative_return']
            }
            for ticker, metrics in all_metrics.items()
        }).T

        print(summary_df)
        os.makedirs('results/metrics', exist_ok=True)
        summary_df.to_csv("results/metrics/summary_metrics.csv")

        print(f"\n✓ Summary saved to results/metrics/summary_metrics.csv")

if __name__ == '__main__':
    main()
