# Twin Range Filter Bot - Quick Reference

## 🎯 Strategy Overview

**Strategy:** Twin Range Filter (TRF)
**Timeframe:** 1 Hour (60-minute candles)
**Position Size:** 35% of wallet per trade
**Leverage:** 37x
**Max Positions:** 1 active at a time

## 📊 Entry & Exit Rules

### Entry Signals
- **LONG Signal:** Twin Range Filter indicators show uptrend
  - Action: Close any SHORT, then open LONG
- **SHORT Signal:** Twin Range Filter indicators show downtrend
  - Action: Close any LONG, then open SHORT

### Exit Triggers (Automatic)

| Event | Trigger | Action |
|-------|---------|--------|
| **Stop Loss** | ROI reaches -37% | Auto-close position |
| **Take Profit** | ROI reaches +150% | Auto-close position |

## 💰 Risk Management

### Position Sizing
- **Wallet:** 35% per position
- **Leverage:** 37x
- **Max Contracts:** Calculated dynamically

### Stop Loss & Take Profit

**Example: LONG on BTCUSDT @ $50,000**
```
Entry Price:        $50,000
Position Size:      ~262 contracts (35% wallet @ 37x)

Stop Loss:
  Price Level:      $49,500
  Price Move:       -1%
  ROI Loss:         -37%

Take Profit:
  Price Level:      $52,025
  Price Move:       +4.05%
  ROI Gain:         +150%
```

## 🔧 Configuration

### Setup Steps

1. **Edit config.py:**
```python
BYBIT_API_KEY = "your_key_here"
BYBIT_API_SECRET = "your_secret_here"
USE_TESTNET = True  # Start with testnet!
```

2. **Adjust if needed:**
```python
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT"]  # Your pairs
POSITION_SIZE_PERCENT = 35               # Keep as is
STOP_LOSS_PERCENT = 37                   # Keep as is
TAKE_PROFIT_PERCENT = 150                # Keep as is
TIMEFRAME = "60"                         # 1 hour
LEVERAGE = {"BTCUSDT": 37, ...}         # Per pair
```

3. **Run the bot:**
```bash
python bot.py
```

## 📋 ROI Formula (For Your Understanding)

```
For LONG Position:
  ROI% = ((current_price - entry_price) / entry_price) × leverage × 100

For SHORT Position:
  ROI% = ((entry_price - current_price) / entry_price) × leverage × 100

SL/TP Price Calculation:
  price_move = entry_price × (ROI_PERCENT / leverage / 100)
  
  LONG:   SL = entry - price_move,  TP = entry + price_move
  SHORT:  SL = entry + price_move,  TP = entry - price_move
```

## 🔍 What to Monitor

### Healthy Signs
```
✅ One position opens at a time
✅ SL/TP prices logged on entry
✅ Clear ROI percentages at triggers
✅ Positions close exactly at SL/TP levels
✅ No position flips without closing
```

### Warning Signs
```
❌ Multiple positions open simultaneously
❌ SL/TP prices seem wrong (off by 10x+)
❌ ROI% doesn't match price movement
❌ Positions never trigger at SL/TP
❌ Rapid position changes
```

## 📝 Log Examples

### Successful Entry
```
🟢 LONG SIGNAL on BTCUSDT
Opening LONG position on BTCUSDT - Qty: 262.1234 @ $50000.0000 | 37x
   ⛔ SL: $49500.0000 (1.00% price move = 37% ROI loss)
   🎯 TP: $52025.0000 (4.05% price move = 150% ROI gain)
✅ Order placed: Buy 262.1234 BTCUSDT
✅ SL/TP configured successfully for BTCUSDT
```

### Stop Loss Trigger
```
🛑 STOP LOSS TRIGGERED on BTCUSDT - ROI: -37.15%
(Entry: $50000.1234, Current: $49495.5678, Leverage: 37x, Size: 262.1234)
✅ Stop loss executed successfully on BTCUSDT
```

### Take Profit Trigger
```
🎯 TAKE PROFIT TRIGGERED on BTCUSDT - ROI: +150.25%
(Entry: $50000.1234, Current: $52026.7890, Leverage: 37x, Size: 262.1234)
✅ Take profit executed successfully on BTCUSDT
```

## ⚠️ Important Warnings

1. **High Leverage:** 37x leverage is extremely risky
   - Only use on testnet first!
   - Start with small wallet amounts
   - Test for at least 1-2 weeks before mainnet

2. **API Permissions:** Your API keys need:
   - ✅ Position/Futures trading
   - ✅ Account read access
   - ❌ Withdrawal (don't enable!)

3. **Network Issues:** Bot checks every 60 seconds
   - SL/TP are set immediately on Bybit side
   - Even if bot crashes, Bybit will honor SL/TP

4. **Position Transitions:** When switching from LONG to SHORT:
   - Old LONG is closed completely first
   - 2-second wait for confirmation
   - Then new SHORT is opened

## 🚀 Getting Started

```bash
# 1. Edit config with your API keys
nano config.py

# 2. Test on testnet
TIMEFRAME="60"  # 1 hour candles
USE_TESTNET=True

# 3. Run
python bot.py

# 4. Monitor logs
tail -f trading_bot.log

# 5. After testing, switch to mainnet
USE_TESTNET=False
```

## 📞 Troubleshooting

**Problem:** No signals detected
- ✓ Check internet connection
- ✓ Verify API credentials
- ✓ Ensure market data is fetching
- ✓ Check `TIMEFRAME = "60"` in config

**Problem:** Position doesn't close at SL/TP
- ✓ Check SL/TP prices in log
- ✓ Verify calculation: price_move = entry × (ROI% / leverage / 100)
- ✓ Ensure ENABLE_STOP_LOSS and ENABLE_TAKE_PROFIT are True

**Problem:** SL/TP prices seem wrong
- ✓ Run calculation manually: entry × (37 / 37 / 100) = 1% price move
- ✓ Check leverage is correct for the pair
- ✓ Verify ROI formula in logs

## 📚 Files

- **bot.py** - Main trading bot logic
- **bybit_client.py** - Bybit API wrapper
- **twin_range_filter.py** - TRF indicator calculation
- **config.py** - Your settings (API keys, pairs, etc.)
- **trading_bot.log** - Bot activity log
- **STRATEGY_UPDATE.md** - Detailed technical changes
