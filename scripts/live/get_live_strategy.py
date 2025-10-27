"""
Get live trading strategy from Strategist + Analyst agents
Real-time interrogation of LLM agents for current market conditions
"""

import sys
import os
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import json
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_agents.strategist_agent_deepseek import StrategistAgent
from src.llm_agents.analyst_agent_deepseek import AnalystAgent


def fetch_latest_market_data(ticker: str, days_back: int = 30) -> pd.DataFrame:
    """Fetch latest market data from Yahoo Finance"""
    print(f"📊 Fetching latest data for {ticker}...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    stock = yf.Ticker(ticker)

    # Get price data
    df = stock.history(start=start_date, end=end_date)

    # Calculate technical indicators
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['RSI'] = calculate_rsi(df['Close'])

    # Get fundamentals
    info = stock.info
    df['PE_Ratio'] = info.get('trailingPE', None)
    df['Beta'] = info.get('beta', None)

    print(f"✅ Fetched {len(df)} days of data")
    return df


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def fetch_latest_news(ticker: str, days_back: int = 7) -> list:
    """Fetch latest news for ticker"""
    print(f"📰 Fetching latest news for {ticker}...")

    stock = yf.Ticker(ticker)
    news = stock.news

    # Format news for analyst
    news_list = []
    for item in news[:10]:  # Top 10 news
        news_list.append({
            'title': item.get('title', ''),
            'publisher': item.get('publisher', ''),
            'link': item.get('link', ''),
            'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat()
        })

    print(f"✅ Fetched {len(news_list)} news articles")
    return news_list


def prepare_strategist_input(df: pd.DataFrame) -> dict:
    """Prepare market data for Strategist Agent"""
    latest = df.iloc[-1]
    last_week = df.iloc[-5:] if len(df) >= 5 else df

    return {
        'beta': latest.get('Beta', 1.0),
        'close': latest['Close'],
        'volume': latest['Volume'],
        'weekly_returns': last_week['Close'].pct_change().tolist(),
        'hv_close': df['Close'].pct_change().std() * (252 ** 0.5),  # Annualized
        'iv_close': latest.get('impliedVolatility', None),
        'current_ratio': None,  # Would need fundamental API
        'debt_to_equity': None,
        'pe_ratio': latest.get('PE_Ratio'),
        'gross_margin': None,
        'operating_margin': None,
        'roe': None,
        'eps_yoy': None,
        'net_income_yoy': None,
        'sma_20': latest.get('SMA_20'),
        'sma_50': latest.get('SMA_50'),
        'rsi': latest.get('RSI'),
        'macd': None,
        'atr': None,
        'spx_return': None,  # Would fetch SPX
        'vix': None,  # Would fetch VIX
        # Add more as needed
    }


def get_live_strategy(ticker: str, verbose: bool = True):
    """
    Get live trading strategy for a ticker

    Args:
        ticker: Stock ticker (e.g., "AAPL")
        verbose: Print detailed output

    Returns:
        dict with strategy, confidence, reasoning
    """

    if verbose:
        print("\n" + "="*70)
        print(f"🤖 Getting LIVE Strategy for {ticker}")
        print("="*70 + "\n")

    # Load config
    with open('configs/hybrid/rewts_llm_rl.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Ensure API key is set
    if not os.getenv('GEMINI_API_KEY'):
        raise ValueError("GEMINI_API_KEY environment variable not set")

    # Initialize agents
    if verbose:
        print("🔧 Initializing LLM Agents...")

    strategist = StrategistAgent(config['llm'])
    analyst = AnalystAgent(config['llm'])

    # Fetch latest data
    market_df = fetch_latest_market_data(ticker, days_back=60)
    news_list = fetch_latest_news(ticker, days_back=7)

    # Prepare inputs
    market_input = prepare_strategist_input(market_df)

    # Get Analyst insights (news analysis)
    if verbose:
        print("\n📰 Analyst Agent: Processing news...")

    analyst_output = analyst.analyze_news(
        ticker=ticker,
        news_data=news_list,
        verbose=verbose
    )

    if verbose:
        print(f"\n  Top Factors:")
        for i, factor in enumerate(analyst_output['top_3_factors'], 1):
            sentiment = analyst_output['sentiment'][i-1]
            impact = analyst_output['impact_score'][i-1]
            emoji = "🟢" if sentiment > 0 else "🔴" if sentiment < 0 else "⚪"
            print(f"    {i}. {emoji} {factor} (Impact: {impact}/3)")

        print(f"\n  Aggregate Sentiment: {analyst_output['aggregate_sentiment']:.2f}")
        print(f"  Average Impact: {analyst_output['aggregate_impact']:.2f}/3")

    # Get Strategist recommendation
    if verbose:
        print("\n📊 Strategist Agent: Generating strategy...")

    strategist_output = strategist.generate_strategy(
        ticker=ticker,
        market_data=market_input,
        analyst_insights=analyst_output,
        last_strategy=None,  # No previous strategy for live
        verbose=verbose
    )

    # Combine results
    strategy = {
        'ticker': ticker,
        'timestamp': datetime.now().isoformat(),
        'recommendation': 'LONG' if strategist_output['direction'] == 1 else 'SHORT',
        'confidence': strategist_output['confidence'],
        'reasoning': strategist_output['explanation'],
        'analyst_sentiment': analyst_output['aggregate_sentiment'],
        'analyst_impact': analyst_output['aggregate_impact'],
        'key_factors': analyst_output['top_3_factors'],
        'current_price': market_df.iloc[-1]['Close'],
        'rsi': market_df.iloc[-1]['RSI'],
        'pe_ratio': market_df.iloc[-1].get('PE_Ratio')
    }

    if verbose:
        print("\n" + "="*70)
        print("🎯 FINAL STRATEGY")
        print("="*70)
        print(f"\n  Ticker: {strategy['ticker']}")
        print(f"  Recommendation: {strategy['recommendation']} "
              f"({'🟢' if strategy['recommendation'] == 'LONG' else '🔴'})")
        print(f"  Confidence: {strategy['confidence']:.2f}/3.0")
        print(f"  Current Price: ${strategy['current_price']:.2f}")
        print(f"  RSI: {strategy['rsi']:.1f}")
        print(f"\n  Reasoning:")
        print(f"  {strategy['reasoning']}")
        print("\n" + "="*70 + "\n")

    return strategy


def get_batch_strategies(tickers: list, save_to_file: bool = True):
    """Get strategies for multiple tickers"""

    print("\n" + "="*70)
    print(f"🚀 Getting strategies for {len(tickers)} tickers")
    print("="*70 + "\n")

    strategies = {}

    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")

        try:
            strategy = get_live_strategy(ticker, verbose=False)
            strategies[ticker] = strategy

            # Quick summary
            rec = strategy['recommendation']
            conf = strategy['confidence']
            emoji = "🟢" if rec == "LONG" else "🔴"
            print(f"  {emoji} {rec} (Confidence: {conf:.2f}/3.0)")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            strategies[ticker] = {"error": str(e)}

    # Save to file
    if save_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"live_strategies_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(strategies, f, indent=2, default=str)

        print(f"\n✅ Strategies saved to {filename}")

    # Summary
    print("\n" + "="*70)
    print("📊 STRATEGIES SUMMARY")
    print("="*70)

    successful = [s for s in strategies.values() if "error" not in s]

    print(f"\n{'Ticker':<10} {'Rec':<8} {'Conf':<8} {'Sentiment':<12} {'Price':<12}")
    print("-"*70)

    for ticker, strategy in strategies.items():
        if "error" in strategy:
            print(f"{ticker:<10} ERROR: {strategy['error'][:50]}")
        else:
            rec = strategy['recommendation']
            emoji = "🟢" if rec == "LONG" else "🔴"
            print(
                f"{ticker:<10} "
                f"{emoji} {rec:<6} "
                f"{strategy['confidence']:<8.2f} "
                f"{strategy['analyst_sentiment']:<12.2f} "
                f"${strategy['current_price']:<11.2f}"
            )

    print("="*70 + "\n")

    return strategies


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Get live trading strategies')
    parser.add_argument('--ticker', type=str, help='Single ticker to analyze')
    parser.add_argument('--tickers', type=str, nargs='+', help='Multiple tickers')
    parser.add_argument('--all', action='store_true', help='All tickers from config')

    args = parser.parse_args()

    # Load API key from environment
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set!")
        print("Set it with: export GEMINI_API_KEY='your_key_here'")
        sys.exit(1)

    if args.ticker:
        # Single ticker
        strategy = get_live_strategy(args.ticker)

    elif args.tickers:
        # Multiple tickers
        strategies = get_batch_strategies(args.tickers)

    elif args.all:
        # All tickers from config
        with open('configs/hybrid/rewts_llm_rl.yaml', 'r') as f:
            config = yaml.safe_load(f)
        tickers = config.get('tickers', ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'TSLA'])
        strategies = get_batch_strategies(tickers)

    else:
        # Default: AAPL
        print("No ticker specified, analyzing AAPL by default")
        print("Usage: python scripts/get_live_strategy.py --ticker TSLA")
        print("   or: python scripts/get_live_strategy.py --tickers AAPL TSLA MSFT")
        print("   or: python scripts/get_live_strategy.py --all")
        print()
        strategy = get_live_strategy('AAPL')
