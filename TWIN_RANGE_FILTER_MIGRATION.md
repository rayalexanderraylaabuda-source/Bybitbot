# Twin Range Filter Strategy Migration

## Overview
Successfully migrated the trading bot from **Supertrend Strategy** to **Twin Range Filter Strategy** across all bot implementations.

## Key Changes

### 1. Strategy Indicator
- **Old**: Supertrend (ATR-based indicator with configurable period and factor)
- **New**: Twin Range Filter (Dual range filter with fast and slow parameters)

### 2. Configuration Parameters
The following new parameters are now used:
- `twin_range_fast_period`: 27 (default)
- `twin_range_fast_range`: 1.6 (default)
- `twin_range_slow_period`: 55 (default)
- `twin_range_slow_range`: 2.0 (default)

Old parameters removed:
- `atr_period`
- `supertrend_factor`

### 3. Position Management Rules
✓ **Only one position active at a time** (as required)
✓ **When Long signal appears**:
  - Close all short positions first
  - Then open long position

✓ **When Short signal appears**:
  - Close all long positions first
  - Then open short position

### 4. Position Sizing & Leverage
- **Position Size**: 35% of wallet balance
- **Leverage**: 35x (fixed, no longer variable)
- **Stop Loss**: 100% ROI trigger (computation stays same as Supertrend)
- **Take Profit**: 150% ROI trigger (computation stays same as Supertrend)

### 5. Timeframe
- **Trading Timeframe**: 1-hour (60 minutes)

## Modified Files

### Core Bot Files
1. **[bot.py](bot.py)** - Main trading bot
   - Imports: Changed from `supertrend` to `twin_range_filter`
   - Class: `SupertrendBot` → `TwinRangeFilterBot`
   - Configuration parameters updated
   - `open_long()` and `open_short()` now use fixed 35x leverage

2. **[bot_mobile.py](bot_mobile.py)** - Mobile-optimized bot
   - Imports: Changed from `supertrend` to `twin_range_filter`
   - Config creation updated with Twin Range Filter parameters
   - Position management logic updated
   - SL/TP calculation logic maintained

3. **[bot_mobile_lite.py](bot_mobile_lite.py)** - Lightweight mobile version
   - Imports: Changed from `supertrend_lite` to `twin_range_filter_lite`
   - Config updated with Twin Range Filter parameters
   - Leverage set to 35x (fixed)
   - SL/TP calculation maintained

4. **[web_bot.py](web_bot.py)** - Web-based bot
   - Imports: Changed from `supertrend_lite` to `twin_range_filter_lite`
   - Default configuration updated
   - Leverage set to 35x (fixed)

## Configuration Reference

### Default Configuration Structure
```json
{
  "api_key": "YOUR_API_KEY",
  "api_secret": "YOUR_API_SECRET",
  "testnet": true,
  "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "leverage": {
    "BTCUSDT": 35,
    "ETHUSDT": 35,
    "SOLUSDT": 35
  },
  "position_size_percent": 35,
  "timeframe": "60",
  "twin_range_fast_period": 27,
  "twin_range_fast_range": 1.6,
  "twin_range_slow_period": 55,
  "twin_range_slow_range": 2.0,
  "stop_loss_percent": 100,
  "take_profit_percent": 150,
  "enable_stop_loss": true,
  "enable_take_profit": true,
  "check_interval": 60
}
```

## Strategy Logic

### Twin Range Filter Indicator
- Uses **fast and slow exponential moving averages** to create smooth range filters
- Generates signals based on price crossing the filter line
- More responsive to price movements compared to Supertrend

### Signal Generation
- **Long Signal**: Generated when price crosses above the filter line with confirmation from uptrend conditions
- **Short Signal**: Generated when price crosses below the filter line with confirmation from downtrend conditions

### Risk Management
All the existing risk management features have been preserved:
- ✓ Stop Loss at 100% ROI loss
- ✓ Take Profit at 150% ROI gain
- ✓ SL/TP calculations use the same formula: `entry_price * (1 ± ROI% / leverage / 100)`
- ✓ One position at a time enforcement
- ✓ Position auto-closing before opening opposite direction trade

## Testing Recommendations

1. **Backtest** the Twin Range Filter strategy on historical data
2. **Paper trade** first on testnet to validate signal quality
3. **Monitor** the SL/TP levels with fixed 35x leverage
4. **Compare** performance with previous Supertrend configuration
5. **Adjust** Twin Range Filter parameters if needed based on market conditions

## Reverting to Supertrend (if needed)

To revert back to Supertrend:
1. Change imports back to `from supertrend import calculate_supertrend, get_latest_signal`
2. Update configuration parameters to use `atr_period` and `supertrend_factor`
3. Update the `check_signals()` method to call `calculate_supertrend()` instead

## Notes

- All position management logic (closing opposite positions before opening new ones) remains intact
- The stop loss and take profit calculations use the same methodology as before
- Only the underlying indicator has changed from Supertrend to Twin Range Filter
- The 35x fixed leverage is now enforced across all implementations
