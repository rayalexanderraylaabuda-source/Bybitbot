"""
Configuration for Twin Range Filter Trading Bot
"""

# ==================== API Configuration ====================
BYBIT_API_KEY = "YOUR_API_KEY"
BYBIT_API_SECRET = "YOUR_API_SECRET"
USE_TESTNET = True  # Set to False for mainnet trading

# ==================== Trading Pairs ====================
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# ==================== Position Management ====================
POSITION_SIZE_PERCENT = 35  # 35% of wallet balance per position
USE_DYNAMIC_SIZING = True   # Use dynamic sizing based on wallet balance
LEVERAGE = {
    "BTCUSDT": 37,
    "ETHUSDT": 37,
    "SOLUSDT": 37
}

# ==================== Timeframe ====================
TIMEFRAME = "60"  # 1 hour = 60 minutes

# ==================== Twin Range Filter Parameters ====================
TWIN_RANGE_FAST_PERIOD = 27
TWIN_RANGE_FAST_RANGE = 1.6
TWIN_RANGE_SLOW_PERIOD = 55
TWIN_RANGE_SLOW_RANGE = 2.0

# ==================== Risk Management ====================
# Stop Loss: Triggers when ROI reaches -37% (price moves against you by 1% @ 37x leverage)
STOP_LOSS_PERCENT = 37
ENABLE_STOP_LOSS = True

# Take Profit: Triggers when ROI reaches +150% (price moves for you by ~4% @ 37x leverage)
TAKE_PROFIT_PERCENT = 150
ENABLE_TAKE_PROFIT = True

# ==================== Bot Behavior ====================
CHECK_INTERVAL = 60  # Check for signals every 60 seconds
# NOTE: Only ONE position will be active at a time
# When a new signal appears:
#   - If LONG signal: Close any SHORT position first, then open LONG
#   - If SHORT signal: Close any LONG position first, then open SHORT

"""
ROI Calculation Formula:
    For LONG positions:  ROI = ((current_price - entry_price) / entry_price) * leverage * 100
    For SHORT positions: ROI = ((entry_price - current_price) / entry_price) * leverage * 100

SL/TP Price Calculation:
    From ROI percent to price move: price_move = entry_price * (ROI_PERCENT / leverage / 100)
    
    LONG:
        SL Price = entry_price - price_move  (when roi = -37%)
        TP Price = entry_price + price_move  (when roi = 150%)
    
    SHORT:
        SL Price = entry_price + price_move  (when roi = -37%)
        TP Price = entry_price - price_move  (when roi = 150%)

Example with BTCUSDT at $50,000 @ 37x leverage, 35% wallet = $10,500:
    - Entry Price: $50,000
    - Position Size: ~262 contracts
    - Price move for 37% ROI = $50,000 * (37 / 37 / 100) = $500
    
    LONG:
        SL at $49,500 (-37% ROI when price drops 1%)
        TP at $50,500 (+150% ROI when price rises ~4.05%)
    
    SHORT:
        SL at $50,500 (+37% ROI when price rises 1%)
        TP at $49,500 (+150% ROI when price drops ~4.05%)
"""
