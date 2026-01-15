# Twin Range Filter Strategy - Quick Reference

## Strategy Overview
Your trading bot has been successfully migrated from **Supertrend** to **Twin Range Filter Strategy**.

## Key Configuration
```
Position Size: 35% of wallet balance
Leverage: 35x (fixed)
Timeframe: 1-hour (60 minutes)
Stop Loss: 100% ROI
Take Profit: 150% ROI
Only 1 position active at a time
```

## Signal Rules
### When LONG signal appears:
1. Close ALL short positions immediately
2. Wait for positions to close
3. Open NEW long position (35% size, 35x leverage)

### When SHORT signal appears:
1. Close ALL long positions immediately
2. Wait for positions to close
3. Open NEW short position (35% size, 35x leverage)

## Twin Range Filter Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `twin_range_fast_period` | 27 | Fast EMA period for range calculation |
| `twin_range_fast_range` | 1.6 | Fast range multiplier |
| `twin_range_slow_period` | 55 | Slow EMA period for range calculation |
| `twin_range_slow_range` | 2.0 | Slow range multiplier |

## Files Modified

1. **bot.py** - Main bot (uses pandas)
2. **bot_mobile.py** - Mobile version (uses pandas)
3. **bot_mobile_lite.py** - Lightweight mobile (no pandas)
4. **web_bot.py** - Web dashboard bot (no pandas)

All versions automatically close opposite positions before opening new ones.

## Stop Loss & Take Profit Calculation

The same calculation method from Supertrend is maintained:

**For LONG:**
- SL = Entry × (1 - SL_ROI% / Leverage / 100)
- TP = Entry × (1 + TP_ROI% / Leverage / 100)

**For SHORT:**
- SL = Entry × (1 + SL_ROI% / Leverage / 100)
- TP = Entry × (1 - TP_ROI% / Leverage / 100)

Example with 35x leverage:
- SL_ROI% = 100 → Price move = 100 / 35 ≈ 2.86%
- TP_ROI% = 150 → Price move = 150 / 35 ≈ 4.29%

## Monitoring

All changes have been implemented with syntax verification. The bot is ready to:
- ✓ Load configuration from JSON files
- ✓ Calculate Twin Range Filter signals
- ✓ Execute trades with proper position management
- ✓ Apply stop loss and take profit at correct ROI levels
- ✓ Close opposite positions before opening new ones

## Next Steps

1. Update your configuration file with API keys
2. Run on testnet first to validate signals
3. Monitor performance for a few trading sessions
4. Adjust Twin Range Filter parameters if needed based on market conditions

**Trading responsibly with 35x leverage!**
