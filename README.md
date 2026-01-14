# Supertrend Trading Bot

Automated trading bot for Bybit derivatives using the Supertrend strategy.

## Features

- **Supertrend Strategy**: Implements the popular TradingView Supertrend indicator
- **Multi-symbol trading**: Supports BTCUSDT, ETHUSDT, SOLUSDT (configurable)
- **Position management**: Automatically closes opposite positions before opening new ones
- **ROI-based Stop Loss & Take Profit**: Properly calculated based on leverage
- **Bybit integration**: Connects to Bybit USDT perpetual futures
- **Testnet support**: Test your strategy safely before going live

## Strategy Overview

The Supertrend indicator uses ATR (Average True Range) to identify trend direction:

- **Long Signal**: When trend direction changes from bearish to bullish (price crosses above Supertrend line)
- **Short Signal**: When trend direction changes from bullish to bearish (price crosses below Supertrend line)

### Parameters

- **ATR Period**: 10 (default) - Period for calculating Average True Range
- **Factor**: 3.0 (default) - Multiplier for ATR to set band distance

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Bybit API Keys

1. Go to [Bybit](https://www.bybit.com)
2. Navigate to API Management (Account → API)
3. Create a new API key with the following permissions:
   - Read-Write
   - Contract (USDT Perpetual)
4. **For testing**, use the testnet: [Bybit Testnet](https://testnet.bybit.com)

### 3. Configure the Bot

Edit `config.py` (or it will use defaults):

```python
# Your API credentials
BYBIT_API_KEY = "your_api_key_here"
BYBIT_API_SECRET = "your_api_secret_here"

# Set to True for testnet, False for mainnet
USE_TESTNET = True

# Trading pairs
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# Position size as percentage of wallet balance
POSITION_SIZE_PERCENT = 35

# Leverage settings
LEVERAGE = {
    "BTCUSDT": 10,
    "ETHUSDT": 10,
    "SOLUSDT": 10
}

# Supertrend parameters
ATR_PERIOD = 5
SUPERTREND_FACTOR = 3.0

# Risk management (ROI-based)
STOP_LOSS_PERCENT = 42  # 42% ROI loss
TAKE_PROFIT_PERCENT = 150  # 150% ROI gain
ENABLE_STOP_LOSS = True
ENABLE_TAKE_PROFIT = True

# Timeframe (1, 3, 5, 15, 30, 60, 120, 240, etc.)
TIMEFRAME = "5"
```

### 4. Run the Bot

```bash
python bot.py
```

## Strategy Logic

### Supertrend Indicator

The Supertrend indicator combines price action with volatility (ATR) to identify trends:

1. **Calculate ATR**: Average True Range over specified period (default 10)
2. **Calculate Bands**: 
   - Upper Band = (High + Low) / 2 + (Factor × ATR)
   - Lower Band = (High + Low) / 2 - (Factor × ATR)
3. **Determine Direction**:
   - When price crosses above lower band → Bullish (Long signal)
   - When price crosses below upper band → Bearish (Short signal)

### Position Management

- When a **LONG** signal appears:
  1. **Close ALL short positions FIRST**
  2. Open new LONG position
  3. Set Stop Loss at 42% ROI loss
  4. Set Take Profit at 150% ROI gain

- When a **SHORT** signal appears:
  1. **Close ALL long positions FIRST**
  2. Open new SHORT position
  3. Set Stop Loss at 42% ROI loss
  4. Set Take Profit at 150% ROI gain

### Stop Loss & Take Profit (ROI-Based)

**CRITICAL**: SL/TP are calculated based on ROI (Return on Investment), accounting for leverage:

**For LONG positions:**
```
Stop Loss Price = Entry Price × (1 - (42 / Leverage) / 100)
Take Profit Price = Entry Price × (1 + (150 / Leverage) / 100)
```

**For SHORT positions:**
```
Stop Loss Price = Entry Price × (1 + (42 / Leverage) / 100)
Take Profit Price = Entry Price × (1 - (150 / Leverage) / 100)
```

**Example with 100x leverage:**
- 42% ROI loss = 0.42% price move
- 150% ROI gain = 1.5% price move

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ATR_PERIOD` | 5 | ATR calculation period |
| `SUPERTREND_FACTOR` | 3.0 | ATR multiplier for bands |
| `POSITION_SIZE_PERCENT` | 35 | % of wallet balance per trade |
| `STOP_LOSS_PERCENT` | 42 | ROI % loss to trigger stop loss |
| `TAKE_PROFIT_PERCENT` | 150 | ROI % gain to trigger take profit |
| `TIMEFRAME` | "5" | Candle timeframe in minutes |
| `CHECK_INTERVAL` | 60 | Seconds between signal checks |

## Files

```
Bybit-Auto-Bot/
├── bot.py                 # Main bot script
├── bot_mobile_lite.py     # Lightweight mobile bot
├── web_bot.py             # Web interface bot
├── bybit_client.py        # Bybit API client (pandas)
├── bybit_client_lite.py   # Bybit API client (no pandas)
├── supertrend.py          # Supertrend indicator (pandas)
├── supertrend_lite.py     # Supertrend indicator (no pandas)
├── android_app/           # Android app files
├── templates/             # Web UI templates
├── requirements.txt       # Python dependencies
├── trading_bot.log        # Log file (created on run)
└── README.md              # This file
```

## Safety Recommendations

1. **Always test on testnet first** before using real funds
2. **Start with small position sizes** when going live
3. **Monitor the bot** regularly, especially in the beginning
4. **Set appropriate leverage** - lower is safer
5. **Never share your API keys**

## Testnet vs Mainnet

- **Testnet**: Set `USE_TESTNET = True` in config.py
  - Get testnet API keys from: https://testnet.bybit.com
  - Uses fake money for testing
  
- **Mainnet**: Set `USE_TESTNET = False` in config.py
  - Get mainnet API keys from: https://www.bybit.com
  - Uses real money - BE CAREFUL!

## Troubleshooting

### "API Error: Invalid API Key"
- Check that your API key and secret are correct
- Ensure you're using testnet keys with testnet mode (or mainnet with mainnet)

### "API Error: Insufficient balance"
- Top up your account balance
- Reduce position size in config

### No signals generated
- The strategy may be waiting for a valid signal
- Check that the market is active
- Verify the timeframe is appropriate

## Disclaimer

This bot is for educational purposes. Trading cryptocurrencies involves substantial risk of loss. The Supertrend strategy is a trend-following system that works best in trending markets but can generate false signals in ranging markets. Always do your own research and never trade with money you cannot afford to lose.

## License

MIT License - See LICENSE file for details

Based on the Supertrend indicator concept from TradingView
