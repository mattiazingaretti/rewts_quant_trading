"""
Script per scaricare e preparare il dataset multi-modale
utilizzando le stesse fonti del paper LLM+RL
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class DataDownloader:
    def __init__(self, config):
        self.tickers = config['tickers']
        self.start_date = config['start_date']
        self.end_date = config['end_date']

    def download_market_data(self, ticker):
        """Scarica OHLCV + IV data"""
        print(f"Downloading market data for {ticker}...")

        # Price data da Yahoo Finance
        stock = yf.Ticker(ticker)
        df = stock.history(start=self.start_date, end=self.end_date)

        if df.empty:
            print(f"Warning: No data found for {ticker}")
            return None

        # Historical Volatility (HV) come proxy per IV
        df['HV_Close'] = df['Close'].pct_change().rolling(20).std() * (252**0.5)

        # SPX e VIX per market context
        try:
            spx = yf.Ticker('^GSPC').history(start=self.start_date, end=self.end_date)
            vix = yf.Ticker('^VIX').history(start=self.start_date, end=self.end_date)

            df['SPX_Close'] = spx['Close']
            df['VIX_Close'] = vix['Close']
        except Exception as e:
            print(f"Warning: Could not download SPX/VIX data: {e}")
            df['SPX_Close'] = np.nan
            df['VIX_Close'] = np.nan

        return df

    def download_fundamentals(self, ticker):
        """Scarica fundamentals da Yahoo Finance"""
        print(f"Downloading fundamentals for {ticker}...")

        stock = yf.Ticker(ticker)

        # Financial ratios
        try:
            info = stock.info
            fundamentals = {
                'PE_Ratio': info.get('trailingPE', None),
                'Debt_to_Equity': info.get('debtToEquity', None),
                'Current_Ratio': info.get('currentRatio', None),
                'ROE': info.get('returnOnEquity', None),
                'Gross_Margin': info.get('grossMargins', None),
                'Operating_Margin': info.get('operatingMargins', None),
            }
        except Exception as e:
            print(f"Warning: Could not download fundamentals: {e}")
            fundamentals = {}

        return fundamentals

    def compute_technical_indicators(self, df):
        """Calcola technical indicators"""
        print("Computing technical indicators...")

        # Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_100'] = df['Close'].rolling(window=100).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

        # ATR (Average True Range)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()

        # Slopes delle MA (usando diff)
        df['SMA_20_Slope'] = df['SMA_20'].diff()
        df['SMA_50_Slope'] = df['SMA_50'].diff()
        df['SMA_100_Slope'] = df['SMA_100'].diff()
        df['SMA_200_Slope'] = df['SMA_200'].diff()

        return df

    def create_mock_news_data(self, ticker, df):
        """Crea mock news data (da sostituire con dati reali se disponibili)"""
        print(f"Creating mock news data for {ticker}...")

        # Crea news sintetiche con timestamp allineati ai dati di mercato
        news_data = []

        # Crea 1 news entry al mese circa
        dates = df.index[::20]  # Ogni 20 giorni trading

        for date in dates:
            news_data.append({
                'timestamp': date,
                'headline': f'Market update for {ticker}',
                'summary': f'Trading activity and performance summary',
                'source': 'Mock Source'
            })

        return pd.DataFrame(news_data)

    def prepare_full_dataset(self):
        """Combina tutti i dati in un dataset unificato"""
        datasets = {}

        for ticker in self.tickers:
            print(f"\n{'='*60}")
            print(f"Processing {ticker}...")
            print(f"{'='*60}")

            # Market data
            market_df = self.download_market_data(ticker)

            if market_df is None or market_df.empty:
                print(f"Skipping {ticker} due to missing data")
                continue

            market_df = self.compute_technical_indicators(market_df)

            # Fundamentals
            fundamentals = self.download_fundamentals(ticker)

            # Aggiungi fundamentals (forward-fill per dati trimestrali)
            for key, value in fundamentals.items():
                market_df[key] = value

            # News (mock per ora)
            news_df = self.create_mock_news_data(ticker, market_df)

            # Drop NaN rows
            market_df = market_df.dropna()

            # Salva
            datasets[ticker] = {
                'market': market_df,
                'news': news_df,
                'fundamentals': fundamentals
            }

            # Save to disk
            os.makedirs('data/processed', exist_ok=True)
            market_df.to_csv(f'data/processed/{ticker}_full_data.csv')
            news_df.to_csv(f'data/processed/{ticker}_news.csv')

            print(f"✓ Saved {ticker} data ({len(market_df)} records)")

        return datasets

if __name__ == '__main__':
    config = {
        'tickers': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'TSLA'],
        'start_date': '2012-01-01',
        'end_date': '2020-12-31',
    }

    downloader = DataDownloader(config)
    datasets = downloader.prepare_full_dataset()
    print("\n✓ Dataset preparation complete!")
