"""
Lightweight Twin Range Filter - No pandas required
Uses only built-in Python and requests
"""

def ema(values, period):
    """Calculate EMA using only lists"""
    if len(values) < period:
        return values
    
    multiplier = 2 / (period + 1)
    ema_values = [values[0]]  # Start with first value
    
    for i in range(1, len(values)):
        ema_val = (values[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
        ema_values.append(ema_val)
    
    return ema_values


def smooth_range(close_prices, period, multiplier):
    """Calculate smooth average range"""
    # Calculate price changes
    changes = [abs(close_prices[i] - close_prices[i-1]) for i in range(1, len(close_prices))]
    changes.insert(0, 0)  # First value is 0
    
    # Calculate average range with EMA
    wper = period * 2 - 1
    avrng = ema(changes, period)
    smoothrng = ema(avrng, wper)
    
    # Apply multiplier
    return [val * multiplier for val in smoothrng]


def range_filter(close_prices, smooth_range_values):
    """Calculate range filter"""
    filt = [close_prices[0]]
    
    for i in range(1, len(close_prices)):
        prev_filt = filt[-1]
        curr_src = close_prices[i]
        curr_rng = smooth_range_values[i]
        
        if curr_src > prev_filt:
            new_filt = prev_filt if curr_src - curr_rng < prev_filt else curr_src - curr_rng
        else:
            new_filt = prev_filt if curr_src + curr_rng > prev_filt else curr_src + curr_rng
        
        filt.append(new_filt)
    
    return filt


def calculate_signals(candles, fast_period=27, fast_range=1.6, slow_period=55, slow_range=2.0):
    """
    Calculate Twin Range Filter signals from candle data
    
    Args:
        candles: List of candles [[timestamp, open, high, low, close, volume], ...]
        fast_period, fast_range, slow_period, slow_range: Strategy parameters
    
    Returns:
        dict with 'long_signal', 'short_signal', 'filter_value'
    """
    if len(candles) < max(fast_period, slow_period) * 2:
        return {'long_signal': False, 'short_signal': False, 'filter_value': 0}
    
    # Extract close prices
    close_prices = [float(candle[4]) for candle in candles]
    
    # Calculate smooth ranges
    smrng1 = smooth_range(close_prices, fast_period, fast_range)
    smrng2 = smooth_range(close_prices, slow_period, slow_range)
    
    # Average of two ranges
    smrng = [(smrng1[i] + smrng2[i]) / 2 for i in range(len(smrng1))]
    
    # Calculate range filter
    filt = range_filter(close_prices, smrng)
    
    # Calculate upward/downward counters
    upward = [0]
    downward = [0]
    
    for i in range(1, len(filt)):
        if filt[i] > filt[i-1]:
            upward.append(upward[-1] + 1)
            downward.append(0)
        elif filt[i] < filt[i-1]:
            upward.append(0)
            downward.append(downward[-1] + 1)
        else:
            upward.append(upward[-1])
            downward.append(downward[-1])
    
    # Calculate long/short conditions
    long_cond = []
    short_cond = []
    
    for i in range(len(close_prices)):
        if i == 0:
            long_cond.append(False)
            short_cond.append(False)
            continue
        
        # Long condition
        lc = (close_prices[i] > filt[i] and close_prices[i] > close_prices[i-1] and upward[i] > 0) or \
             (close_prices[i] > filt[i] and close_prices[i] < close_prices[i-1] and upward[i] > 0)
        long_cond.append(lc)
        
        # Short condition
        sc = (close_prices[i] < filt[i] and close_prices[i] < close_prices[i-1] and downward[i] > 0) or \
             (close_prices[i] < filt[i] and close_prices[i] > close_prices[i-1] and downward[i] > 0)
        short_cond.append(sc)
    
    # Calculate condition initialization
    cond_ini = [0]
    for i in range(1, len(close_prices)):
        if long_cond[i]:
            cond_ini.append(1)
        elif short_cond[i]:
            cond_ini.append(-1)
        else:
            cond_ini.append(cond_ini[-1])
    
    # Generate signals (only on condition change)
    # Check last 2 candles (use -2 to avoid current forming candle)
    if len(cond_ini) >= 3:
        # Signal on completed candle
        long_signal = long_cond[-2] and cond_ini[-3] == -1
        short_signal = short_cond[-2] and cond_ini[-3] == 1
    else:
        long_signal = False
        short_signal = False
    
    return {
        'long_signal': long_signal,
        'short_signal': short_signal,
        'filter_value': filt[-1] if filt else 0,
        'current_price': close_prices[-1] if close_prices else 0
    }
