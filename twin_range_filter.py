"""
Twin Range Filter Indicator Implementation
Converted from PineScript to Python
Original: © colinmck
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
            self.dtype = dtype
        
        def ewm(self, span, adjust=False):
            return EWMResult(self.data, span)
        
        def shift(self, n=1):
            return Series([None]*n + self.data[:-n] if n > 0 else self.data[-n:] + [None]*(-n), index=self.index)
        
        def __abs__(self):
            return Series([abs(x) if x is not None else None for x in self.data], index=self.index)
        
        def __sub__(self, other):
            if isinstance(other, Series):
                return Series([a - b if a is not None and b is not None else None for a, b in zip(self.data, other.data)], index=self.index)
            return Series([x - other if x is not None else None for x in self.data], index=self.index)
        
        def __add__(self, other):
            if isinstance(other, Series):
                return Series([a + b if a is not None and b is not None else None for a, b in zip(self.data, other.data)], index=self.index)
            return Series([x + other if x is not None else None for x in self.data], index=self.index)
        
        def __mul__(self, other):
            if isinstance(other, Series):
                return Series([a * b if a is not None and b is not None else None for a, b in zip(self.data, other.data)], index=self.index)
            return Series([x * other if x is not None else None for x in self.data], index=self.index)
        
        def __gt__(self, other):
            if isinstance(other, Series):
                return Series([a > b if a is not None and b is not None else False for a, b in zip(self.data, other.data)], index=self.index)
            return Series([x > other if x is not None else False for x in self.data], index=self.index)
        
        def __lt__(self, other):
            if isinstance(other, Series):
                return Series([a < b if a is not None and b is not None else False for a, b in zip(self.data, other.data)], index=self.index)
            return Series([x < other if x is not None else False for x in self.data], index=self.index)
        
        def __and__(self, other):
            return Series([a and b for a, b in zip(self.data, other.data)], index=self.index)
        
        def __or__(self, other):
            return Series([a or b for a, b in zip(self.data, other.data)], index=self.index)
        
        def iloc(self):
            return self
        
        def __getitem__(self, key):
            if isinstance(key, int):
                return self.data[key]
            return Series([self.data[i] for i in key], index=[self.index[i] for i in key])
    
    class EWMResult:
        def __init__(self, data, span):
            self.data = data
            self.span = span
        
        def mean(self):
            result = []
            alpha = 2 / (self.span + 1)
            for i, x in enumerate(self.data):
                if x is None:
                    result.append(None)
                elif i == 0:
                    result.append(float(x) if x is not None else None)
                else:
                    prev = result[i-1]
                    if prev is None:
                        result.append(float(x) if x is not None else None)
                    else:
                        result.append(alpha * float(x) + (1 - alpha) * prev)
            return Series(result)
    
    class DataFrame:
        def __init__(self, data=None, columns=None):
            self.columns = columns or []
            if isinstance(data, list):
                self.data = data
            else:
                self.data = data or []
            self.index = list(range(len(self.data)))
        
        def copy(self):
            return DataFrame([row[:] if isinstance(row, list) else dict(row) for row in self.data], self.columns)
        
        def astype(self, dtype_dict):
            return self
        
        def sort_values(self, by, ascending=True):
            return self
        
        def reset_index(self, drop=False):
            return self
        
        def __getitem__(self, key):
            if isinstance(key, str):
                try:
                    idx = self.columns.index(key)
                    return Series([row[idx] if isinstance(row, (list, tuple)) else row.get(key) for row in self.data])
                except:
                    return Series([])
            return self.data[key]
        
        def __setitem__(self, key, value):
            if key not in self.columns:
                self.columns.append(key)
            if isinstance(value, Series):
                for i, v in enumerate(value.data):
                    if i < len(self.data):
                        if isinstance(self.data[i], dict):
                            self.data[i][key] = v
                        else:
                            self.data[i][key] = v
    
    class pd:
        DataFrame = DataFrame
        Series = Series
        @staticmethod
        def to_datetime(series, unit=None):
            return series
        @staticmethod
        def concat(*args, **kwargs):
            return Series([])


def ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def smooth_range(source: pd.Series, period: int, multiplier: float) -> pd.Series:
    """
    Calculate Smooth Average Range
    
    Args:
        source: Price series (typically close)
        period: Lookback period
        multiplier: Range multiplier
    
    Returns:
        Smoothed range series
    """
    wper = period * 2 - 1
    # Calculate average range
    avrng = ema(abs(source - source.shift(1)), period)
    # Calculate smooth range
    smoothrng = ema(avrng, wper) * multiplier
    return smoothrng


def range_filter(source: pd.Series, smooth_range: pd.Series) -> pd.Series:
    """
    Calculate Range Filter
    
    Args:
        source: Price series
        smooth_range: Smoothed range series
    
    Returns:
        Filtered price series
    """
    rngfilt = pd.Series(index=source.index, dtype=float)
    rngfilt.iloc[0] = source.iloc[0]
    
    for i in range(1, len(source)):
        prev_filt = rngfilt.iloc[i-1]
        curr_src = source.iloc[i]
        curr_rng = smooth_range.iloc[i]
        
        if curr_src > prev_filt:
            if curr_src - curr_rng < prev_filt:
                rngfilt.iloc[i] = prev_filt
            else:
                rngfilt.iloc[i] = curr_src - curr_rng
        else:
            if curr_src + curr_rng > prev_filt:
                rngfilt.iloc[i] = prev_filt
            else:
                rngfilt.iloc[i] = curr_src + curr_rng
    
    return rngfilt


def calculate_twin_range_filter(
    df: pd.DataFrame,
    fast_period: int = 27,
    fast_range: float = 1.6,
    slow_period: int = 55,
    slow_range: float = 2.0,
    source_col: str = 'close'
) -> pd.DataFrame:
    """
    Calculate Twin Range Filter signals
    
    Args:
        df: DataFrame with OHLCV data
        fast_period: Fast EMA period
        fast_range: Fast range multiplier
        slow_period: Slow EMA period
        slow_range: Slow range multiplier
        source_col: Column to use as source (default: close)
    
    Returns:
        DataFrame with added indicator columns and signals
    """
    result = df.copy()
    source = result[source_col]
    
    # Calculate smooth ranges
    smrng1 = smooth_range(source, fast_period, fast_range)
    smrng2 = smooth_range(source, slow_period, slow_range)
    smrng = (smrng1 + smrng2) / 2
    
    # Calculate range filter
    filt = range_filter(source, smrng)
    
    # Calculate upward/downward counters
    upward = pd.Series(index=source.index, dtype=float)
    downward = pd.Series(index=source.index, dtype=float)
    upward.iloc[0] = 0
    downward.iloc[0] = 0
    
    for i in range(1, len(filt)):
        if filt.iloc[i] > filt.iloc[i-1]:
            upward.iloc[i] = upward.iloc[i-1] + 1
            downward.iloc[i] = 0
        elif filt.iloc[i] < filt.iloc[i-1]:
            upward.iloc[i] = 0
            downward.iloc[i] = downward.iloc[i-1] + 1
        else:
            upward.iloc[i] = upward.iloc[i-1]
            downward.iloc[i] = downward.iloc[i-1]
    
    # Calculate bands
    hband = filt + smrng
    lband = filt - smrng
    
    # Calculate conditions
    long_cond = ((source > filt) & (source > source.shift(1)) & (upward > 0)) | \
                ((source > filt) & (source < source.shift(1)) & (upward > 0))
    
    short_cond = ((source < filt) & (source < source.shift(1)) & (downward > 0)) | \
                 ((source < filt) & (source > source.shift(1)) & (downward > 0))
    
    # Calculate CondIni (condition initialization)
    cond_ini = pd.Series(index=source.index, dtype=int)
    cond_ini.iloc[0] = 0
    
    for i in range(1, len(source)):
        if long_cond.iloc[i]:
            cond_ini.iloc[i] = 1
        elif short_cond.iloc[i]:
            cond_ini.iloc[i] = -1
        else:
            cond_ini.iloc[i] = cond_ini.iloc[i-1]
    
    # Generate signals (only on condition change)
    long_signal = long_cond & (cond_ini.shift(1) == -1)
    short_signal = short_cond & (cond_ini.shift(1) == 1)
    
    # Add to result DataFrame
    result['smrng'] = smrng
    result['filt'] = filt
    result['hband'] = hband
    result['lband'] = lband
    result['upward'] = upward
    result['downward'] = downward
    result['long_cond'] = long_cond
    result['short_cond'] = short_cond
    result['cond_ini'] = cond_ini
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
