"""
Supertrend Indicator Implementation
Converted from PineScript to Python
Based on TradingView's ta.supertrend() function
"""

import numpy as np

# Lightweight pandas replacement for Termux
try:
    import pandas as pd
except ImportError:
    class Series:
        def __init__(self, data=None, index=None, dtype=None):
            self.data = list(data) if data is not None else []
            self.index = index or list(range(len(self.data)))
        
        def shift(self, n=1):
            return Series([None]*n + self.data[:-n] if n > 0 else self.data[-n:] + [None]*(-n))
        
        def rolling(self, window):
            return RollingResult(self.data, window)
        
        def __getitem__(self, key):
            return self.data[key]
        
        def __setitem__(self, key, value):
            self.data[key] = value
    
    class RollingResult:
        def __init__(self, data, window):
            self.data = data
            self.window = window
        
        def mean(self):
            result = []
            for i in range(len(self.data)):
                if i < self.window - 1:
                    result.append(None)
                else:
                    window_data = self.data[i-self.window+1:i+1]
                    avg = sum(x for x in window_data if x is not None) / len([x for x in window_data if x is not None])
                    result.append(avg)
            return Series(result)
    
    class DataFrame:
        def __init__(self, data=None, columns=None):
            self.columns = columns or []
            self.data = data or {}
        
        def copy(self):
            return DataFrame(dict(self.data), self.columns[:])
        
        def __getitem__(self, key):
            return self.data.get(key, Series([]))
        
        def __setitem__(self, key, value):
            self.data[key] = value
            if key not in self.columns:
                self.columns.append(key)
    
    class pd:
        DataFrame = DataFrame
        Series = Series


def calculate_atr(df: pd.DataFrame, period: int = 5) -> pd.Series:
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with OHLC data (requires 'high', 'low', 'close' columns)
        period: ATR period (default: 5)
    
    Returns:
        ATR series
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate True Range components
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    # True Range is the maximum of the three
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR as RMA (Running Moving Average) of True Range
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    return atr


def calculate_supertrend(
    df: pd.DataFrame,
    atr_period: int = 5,
    factor: float = 3.0
) -> pd.DataFrame:
    """
    Calculate Supertrend indicator
    
    Args:
        df: DataFrame with OHLC data
        atr_period: ATR period (default: 5)
        factor: Multiplier for ATR (default: 3.0)
    
    Returns:
        DataFrame with added indicator columns and signals
    """
    result = df.copy()
    
    # Calculate ATR
    atr = calculate_atr(result, atr_period)
    
    # Calculate basic upper and lower bands
    hl2 = (result['high'] + result['low']) / 2
    basic_upperband = hl2 + (factor * atr)
    basic_lowerband = hl2 - (factor * atr)
    
    # Initialize final bands
    final_upperband = pd.Series(index=result.index, dtype=float)
    final_lowerband = pd.Series(index=result.index, dtype=float)
    supertrend = pd.Series(index=result.index, dtype=float)
    direction = pd.Series(index=result.index, dtype=int)
    
    # First value
    final_upperband.iloc[0] = basic_upperband.iloc[0]
    final_lowerband.iloc[0] = basic_lowerband.iloc[0]
    supertrend.iloc[0] = basic_upperband.iloc[0]
    direction.iloc[0] = -1  # Start with downtrend
    
    # Calculate final bands and supertrend
    for i in range(1, len(result)):
        # Final Upper Band
        if basic_upperband.iloc[i] < final_upperband.iloc[i-1] or result['close'].iloc[i-1] > final_upperband.iloc[i-1]:
            final_upperband.iloc[i] = basic_upperband.iloc[i]
        else:
            final_upperband.iloc[i] = final_upperband.iloc[i-1]
        
        # Final Lower Band
        if basic_lowerband.iloc[i] > final_lowerband.iloc[i-1] or result['close'].iloc[i-1] < final_lowerband.iloc[i-1]:
            final_lowerband.iloc[i] = basic_lowerband.iloc[i]
        else:
            final_lowerband.iloc[i] = final_lowerband.iloc[i-1]
        
        # Supertrend direction
        if supertrend.iloc[i-1] == final_upperband.iloc[i-1]:
            if result['close'].iloc[i] <= final_upperband.iloc[i]:
                direction.iloc[i] = -1
                supertrend.iloc[i] = final_upperband.iloc[i]
            else:
                direction.iloc[i] = 1
                supertrend.iloc[i] = final_lowerband.iloc[i]
        else:  # supertrend was final_lowerband
            if result['close'].iloc[i] >= final_lowerband.iloc[i]:
                direction.iloc[i] = 1
                supertrend.iloc[i] = final_lowerband.iloc[i]
            else:
                direction.iloc[i] = -1
                supertrend.iloc[i] = final_upperband.iloc[i]
    
    # Calculate direction change for signals
    direction_change = direction.diff()
    
    # Generate trading signals
    # Long signal: direction changes to positive (uptrend)
    long_signal = direction_change > 0
    
    # Short signal: direction changes to negative (downtrend)
    short_signal = direction_change < 0
    
    # Add to result DataFrame
    result['atr'] = atr
    result['basic_upperband'] = basic_upperband
    result['basic_lowerband'] = basic_lowerband
    result['final_upperband'] = final_upperband
    result['final_lowerband'] = final_lowerband
    result['supertrend'] = supertrend
    result['direction'] = direction
    result['long_signal'] = long_signal
    result['short_signal'] = short_signal
    
    return result


def get_latest_signal(df: pd.DataFrame) -> str:
    """
    Get the latest trading signal from the DataFrame
    
    Args:
        df: DataFrame with calculated signals
    
    Returns:
        'long', 'short', or 'none'
    """
    if len(df) < 2:
        return 'none'
    
    # Check the most recent completed candle (not the current forming one)
    latest = df.iloc[-2]  # Use -2 to check completed candle
    
    if latest['long_signal']:
        return 'long'
    elif latest['short_signal']:
        return 'short'
    else:
        return 'none'
