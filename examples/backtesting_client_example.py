"""
Example client for ReWTSE Backtesting API (FastAPI VM)
"""
import requests
from typing import Dict, Any
import time


class BacktestingClient:
    """Client for FastAPI VM backtesting API"""

    def __init__(self, vm_ip: str, port: int = 8000):
        """
        Initialize client

        Args:
            vm_ip: FastAPI VM IP address (e.g., "35.123.45.67")
            port: API port (default: 8000)
        """
        self.base_url = f"http://{vm_ip}:{port}"

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            print("✅ API is healthy")
            return response.json()
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            raise

    def run_backtest(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        initial_balance: float = 10000,
        transaction_cost: float = 0.001
    ) -> Dict[str, Any]:
        """
        Run backtest for a ticker

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_balance: Initial balance in USD
            transaction_cost: Transaction cost (0.1% = 0.001)

        Returns:
            Backtest results dictionary
        """
        payload = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "initial_balance": initial_balance,
            "transaction_cost": transaction_cost
        }

        print(f"📊 Running backtest for {ticker}...")
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/backtest",
                json=payload,
                timeout=600
            )
            response.raise_for_status()

            elapsed = time.time() - start_time
            print(f"✅ Completed in {elapsed:.1f}s")

            return response.json()

        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            raise

    def run_batch_backtests(
        self,
        tickers: list,
        start_date: str,
        end_date: str,
        initial_balance: float = 10000
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run backtests for multiple tickers

        Args:
            tickers: List of ticker symbols
            start_date: Start date
            end_date: End date
            initial_balance: Initial balance

        Returns:
            Dictionary mapping ticker to results
        """
        results = {}

        print(f"\n🚀 Running batch backtests for {len(tickers)} tickers...")
        print(f"Period: {start_date} to {end_date}\n")

        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] Processing {ticker}...")

            try:
                result = self.run_backtest(
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    initial_balance=initial_balance
                )
                results[ticker] = result

                # Print summary
                print(f"  Sharpe: {result['sharpe_ratio']:.3f}")
                print(f"  Return: {result['cumulative_return']:.1%}")
                print(f"  Max DD: {result['max_drawdown']:.1%}")
                print()

            except Exception as e:
                print(f"  ❌ Failed: {e}\n")
                results[ticker] = {"error": str(e)}

        return results

    def print_summary(self, results: Dict[str, Dict[str, Any]]):
        """Print summary of batch backtest results"""
        print("\n" + "="*60)
        print("📊 BACKTEST SUMMARY")
        print("="*60)

        successful = [r for r in results.values() if "error" not in r]
        failed = [r for r in results.values() if "error" in r]

        print(f"\nTotal: {len(results)} | Success: {len(successful)} | Failed: {len(failed)}")

        if not successful:
            print("No successful backtests")
            return

        print(f"\n{'Ticker':<10} {'Sharpe':<10} {'Return':<12} {'Max DD':<12} {'Trades':<10}")
        print("-"*60)

        for ticker, result in results.items():
            if "error" in result:
                print(f"{ticker:<10} ERROR: {result['error'][:40]}")
            else:
                print(
                    f"{ticker:<10} "
                    f"{result['sharpe_ratio']:<10.3f} "
                    f"{result['cumulative_return']:<12.1%} "
                    f"{result['max_drawdown']:<12.1%} "
                    f"{result['total_trades']:<10}"
                )

        # Overall statistics
        sharpes = [r['sharpe_ratio'] for r in successful]
        returns = [r['cumulative_return'] for r in successful]

        print("-"*60)
        print(f"{'AVERAGE':<10} "
              f"{sum(sharpes)/len(sharpes):<10.3f} "
              f"{sum(returns)/len(returns):<12.1%}")
        print("="*60)


# =============================================================================
# EXAMPLES
# =============================================================================

def example_single_backtest():
    """Example: Single backtest"""
    print("\n=== Example 1: Single Backtest ===\n")

    # Replace with your VM IP
    # Get it with: bash scripts/gcp/manage_fastapi_vm.sh ip
    client = BacktestingClient(vm_ip="35.123.45.67")

    # Health check
    client.health_check()

    # Run backtest
    result = client.run_backtest(
        ticker="AAPL",
        start_date="2020-01-01",
        end_date="2020-12-31"
    )

    # Print results
    print(f"\n📊 Results for AAPL:")
    print(f"  Sharpe Ratio: {result['sharpe_ratio']:.3f}")
    print(f"  Cumulative Return: {result['cumulative_return']:.2%}")
    print(f"  Max Drawdown: {result['max_drawdown']:.2%}")
    print(f"  Total Trades: {result['total_trades']}")
    print(f"  Win Rate: {result['win_rate']:.2%}")
    print(f"  Final Balance: ${result['final_balance']:.2f}")


def example_batch_backtests():
    """Example: Batch backtests for all tickers"""
    print("\n=== Example 2: Batch Backtests ===\n")

    client = BacktestingClient(vm_ip="35.123.45.67")

    # All tickers from config
    tickers = ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "TSLA"]

    # Run batch
    results = client.run_batch_backtests(
        tickers=tickers,
        start_date="2020-01-01",
        end_date="2020-12-31",
        initial_balance=10000
    )

    # Print summary
    client.print_summary(results)


def example_period_comparison():
    """Example: Compare different time periods"""
    print("\n=== Example 3: Period Comparison ===\n")

    client = BacktestingClient(vm_ip="35.123.45.67")

    ticker = "AAPL"
    periods = [
        ("2018-01-01", "2018-12-31", "2018"),
        ("2019-01-01", "2019-12-31", "2019"),
        ("2020-01-01", "2020-12-31", "2020"),
    ]

    print(f"📊 Comparing {ticker} across different years\n")

    results = {}
    for start, end, year in periods:
        print(f"Testing {year}...")

        result = client.run_backtest(
            ticker=ticker,
            start_date=start,
            end_date=end
        )

        results[year] = result

    # Print comparison
    print("\n" + "="*70)
    print(f"{'Year':<10} {'Sharpe':<10} {'Return':<12} {'Max DD':<12} {'Trades':<10}")
    print("-"*70)

    for year, result in results.items():
        print(
            f"{year:<10} "
            f"{result['sharpe_ratio']:<10.3f} "
            f"{result['cumulative_return']:<12.1%} "
            f"{result['max_drawdown']:<12.1%} "
            f"{result['total_trades']:<10}"
        )

    print("="*70)


def example_strategy_comparison():
    """Example: Compare different initial balances"""
    print("\n=== Example 4: Capital Comparison ===\n")

    client = BacktestingClient(vm_ip="35.123.45.67")

    ticker = "TSLA"
    balances = [5000, 10000, 25000, 50000]

    print(f"📊 Comparing {ticker} with different initial capital\n")

    results = {}
    for balance in balances:
        print(f"Testing with ${balance:,}...")

        result = client.run_backtest(
            ticker=ticker,
            start_date="2020-01-01",
            end_date="2020-12-31",
            initial_balance=balance
        )

        results[balance] = result

    # Print comparison
    print("\n" + "="*80)
    print(f"{'Capital':<15} {'Sharpe':<10} {'Return':<12} {'Final':<15} {'Profit':<15}")
    print("-"*80)

    for balance, result in results.items():
        profit = result['final_balance'] - balance
        print(
            f"${balance:>12,}  "
            f"{result['sharpe_ratio']:<10.3f} "
            f"{result['cumulative_return']:<12.1%} "
            f"${result['final_balance']:>12,.2f}  "
            f"${profit:>12,.2f}"
        )

    print("="*80)


if __name__ == "__main__":
    # Get your VM IP first:
    # bash scripts/gcp/manage_fastapi_vm.sh ip

    # Then run examples (uncomment the one you want)

    example_single_backtest()
    # example_batch_backtests()
    # example_period_comparison()
    # example_strategy_comparison()
