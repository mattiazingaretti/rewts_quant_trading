"""
Data utility functions
"""

import pandas as pd
import numpy as np


def normalize_datetime(dt):
    """
    Normalize a datetime to timezone-naive

    Args:
        dt: datetime-like object

    Returns:
        Timezone-naive datetime
    """
    if dt is None:
        return None

    # Convert to pandas Timestamp
    ts = pd.Timestamp(dt)

    # Remove timezone if present
    if ts.tz is not None:
        ts = ts.tz_localize(None)

    return ts


def normalize_datetime_index(index):
    """
    Normalize a DatetimeIndex to timezone-naive

    Args:
        index: DatetimeIndex

    Returns:
        Timezone-naive DatetimeIndex
    """
    if not isinstance(index, pd.DatetimeIndex):
        return index

    # Remove timezone if present
    if index.tz is not None:
        return index.tz_localize(None)

    return index


def filter_news_by_period(news_df, period_start, period_end):
    """
    Filter news dataframe by date period, handling timezone differences

    Args:
        news_df: DataFrame with datetime index
        period_start: Start date
        period_end: End date

    Returns:
        Filtered DataFrame
    """
    try:
        # Normalize all dates to timezone-naive
        start = normalize_datetime(period_start)
        end = normalize_datetime(period_end)

        # Normalize index
        news_index = normalize_datetime_index(news_df.index)

        # Filter
        mask = (news_index >= start) & (news_index <= end)
        return news_df[mask]

    except Exception as e:
        print(f"Warning: Error filtering news: {e}")
        return pd.DataFrame()


def load_market_data(ticker, data_dir='data/processed'):
    """
    Load market data with proper date parsing

    Args:
        ticker: Stock ticker symbol
        data_dir: Directory containing processed data

    Returns:
        DataFrame with market data
    """
    filepath = f"{data_dir}/{ticker}_full_data.csv"
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)

    # Ensure index is timezone-naive for consistency
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    return df


def load_news_data(ticker, data_dir='data/processed'):
    """
    Load news data with proper date parsing

    Args:
        ticker: Stock ticker symbol
        data_dir: Directory containing processed data

    Returns:
        DataFrame with news data
    """
    filepath = f"{data_dir}/{ticker}_news.csv"
    news_df = pd.read_csv(filepath)

    # Set timestamp as index if present
    if 'timestamp' in news_df.columns:
        news_df['timestamp'] = pd.to_datetime(news_df['timestamp'], utc=True)
        news_df = news_df.set_index('timestamp')
    else:
        # Fallback: use first column as index
        news_df = pd.read_csv(filepath, index_col=0, parse_dates=True)

    # Normalize to timezone-naive
    if isinstance(news_df.index, pd.DatetimeIndex) and news_df.index.tz is not None:
        news_df.index = news_df.index.tz_localize(None)

    # Sort by date
    news_df = news_df.sort_index()

    return news_df
