"""
Backtesting script per ReWTSE-LLM-RL ensemble
"""

import pandas as pd
import numpy as np
import pickle
from tqdm import tqdm
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rl_agents.trading_env import TradingEnv
from backtesting.backtest_utils import (
    calculate_comprehensive_metrics,
    plot_backtest_results,
    save_backtest_report,
    print_backtest_summary
)

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

    # Calcola metriche usando utility condivisa
    portfolio_values = np.array(portfolio_values)
    metrics = calculate_comprehensive_metrics(portfolio_values, test_env.initial_balance)

    # Aggiungi dati specifici per plotting
    metrics['portfolio_values'] = portfolio_values
    metrics['actions'] = actions_taken
    metrics['weights_history'] = weights_history

    # Print summary
    print_backtest_summary(ticker, metrics, test_env.initial_balance)

    return metrics


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

            # Plot usando utility condivisa
            plot_backtest_results(ticker, metrics)

    # Summary table usando utility condivisa
    if all_metrics:
        # Prepara risultati nel formato atteso da save_backtest_report
        results = [
            {
                'ticker': ticker,
                'initial_balance': config['trading_env']['initial_balance'],
                'metrics': metrics,
                'portfolio_history': metrics['portfolio_values']
            }
            for ticker, metrics in all_metrics.items()
        ]

        save_backtest_report(results, 'results/metrics/summary_metrics.csv')

if __name__ == '__main__':
    main()
