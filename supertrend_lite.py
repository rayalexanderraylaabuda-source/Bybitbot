"""
Lightweight Supertrend Indicator - No pandas required
Uses only built-in Python and lists
"""


def calculate_atr(high_prices, low_prices, close_prices, period=5):
    """
    Calculate Average True Range (ATR)
    
    Args:
        high_prices: List of high prices
        low_prices: List of low prices
        close_prices: List of close prices
        period: ATR period (default: 5)
    
    Returns:
        List of ATR values
    """
    if len(high_prices) < 2:
        return [0] * len(high_prices)
    
    # Calculate True Range for each candle
    tr_values = [high_prices[0] - low_prices[0]]  # First TR
    
    for i in range(1, len(high_prices)):
        tr1 = high_prices[i] - low_prices[i]
        tr2 = abs(high_prices[i] - close_prices[i-1])
        tr3 = abs(low_prices[i] - close_prices[i-1])
        tr = max(tr1, tr2, tr3)
        tr_values.append(tr)
    
    # Calculate ATR using RMA (exponential moving average)
    alpha = 1.0 / period
    atr = [tr_values[0]]  # Start with first TR
    
    for i in range(1, len(tr_values)):
        atr_val = (tr_values[i] * alpha) + (atr[-1] * (1 - alpha))
        atr.append(atr_val)
    
    return atr


def calculate_supertrend(candles, atr_period=5, factor=3.0):
    """
    Calculate Supertrend signals from candle data
    
    Args:
        candles: List of candles [[timestamp, open, high, low, close, volume], ...]
        atr_period: ATR period (default: 5)
        factor: Multiplier for ATR (default: 3.0)
    
    Returns:
        dict with 'long_signal', 'short_signal', 'supertrend_value', 'direction'
    """
    if len(candles) < atr_period * 2:
        return {
            'long_signal': False,
            'short_signal': False,
            'supertrend_value': 0,
            'direction': 0,
            'current_price': 0
        }
    
    # Extract price data
    high_prices = [float(candle[2]) for candle in candles]
    low_prices = [float(candle[3]) for candle in candles]
    close_prices = [float(candle[4]) for candle in candles]
    
    # Calculate ATR
    atr = calculate_atr(high_prices, low_prices, close_prices, atr_period)
    
    # Calculate HL2 (average of high and low)
    hl2 = [(high_prices[i] + low_prices[i]) / 2 for i in range(len(candles))]
    
    # Calculate basic bands
    basic_upperband = [hl2[i] + (factor * atr[i]) for i in range(len(candles))]
    basic_lowerband = [hl2[i] - (factor * atr[i]) for i in range(len(candles))]
    
    # Initialize final bands
    final_upperband = [basic_upperband[0]]
    final_lowerband = [basic_lowerband[0]]
    supertrend = [basic_upperband[0]]
    direction = [-1]  # Start with downtrend
    
    # Calculate final bands and supertrend
    for i in range(1, len(candles)):
        # Final Upper Band
        if basic_upperband[i] < final_upperband[-1] or close_prices[i-1] > final_upperband[-1]:
            final_upperband.append(basic_upperband[i])
        else:
            final_upperband.append(final_upperband[-1])
        
        # Final Lower Band
        if basic_lowerband[i] > final_lowerband[-1] or close_prices[i-1] < final_lowerband[-1]:
            final_lowerband.append(basic_lowerband[i])
        else:
            final_lowerband.append(final_lowerband[-1])
        
        # Determine supertrend direction
        if supertrend[-1] == final_upperband[i-1]:
            if close_prices[i] <= final_upperband[i]:
                direction.append(-1)
                supertrend.append(final_upperband[i])
            else:
                direction.append(1)
                supertrend.append(final_lowerband[i])
        else:  # supertrend was final_lowerband
            if close_prices[i] >= final_lowerband[i]:
                direction.append(1)
                supertrend.append(final_lowerband[i])
            else:
                direction.append(-1)
                supertrend.append(final_upperband[i])
    
    # Generate signals based on direction change
    # Check last 2 candles (use -2 to avoid current forming candle)
    if len(direction) >= 3:
        # Long signal: direction changes to 1 (uptrend)
        long_signal = direction[-2] == 1 and direction[-3] == -1
        # Short signal: direction changes to -1 (downtrend)
        short_signal = direction[-2] == -1 and direction[-3] == 1
    else:
        long_signal = False
        short_signal = False
    
    return {
        'long_signal': long_signal,
        'short_signal': short_signal,
        'supertrend_value': supertrend[-1] if supertrend else 0,
        'direction': direction[-1] if direction else 0,
        'current_price': close_prices[-1] if close_prices else 0
    }
