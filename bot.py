"""
Twin Range Filter Trading Bot
Automated trading on Bybit derivatives
"""

import time
import logging
from datetime import datetime
from typing import Dict

try:
    from config import (
        BYBIT_API_KEY,
        BYBIT_API_SECRET,
        USE_TESTNET,
        TRADING_PAIRS,
        POSITION_SIZE_PERCENT,
        USE_DYNAMIC_SIZING,
        LEVERAGE,
        TIMEFRAME,
        TWIN_RANGE_FAST_PERIOD,
        TWIN_RANGE_FAST_RANGE,
        TWIN_RANGE_SLOW_PERIOD,
        TWIN_RANGE_SLOW_RANGE,
        STOP_LOSS_PERCENT,
        TAKE_PROFIT_PERCENT,
        ENABLE_STOP_LOSS,
        ENABLE_TAKE_PROFIT,
        CHECK_INTERVAL
    )
except ImportError:
    # Default values if config.py doesn't exist
    BYBIT_API_KEY = "YOUR_API_KEY"
    BYBIT_API_SECRET = "YOUR_API_SECRET"
    USE_TESTNET = True
    TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    POSITION_SIZE_PERCENT = 35
    USE_DYNAMIC_SIZING = True
    LEVERAGE = {"BTCUSDT": 37, "ETHUSDT": 37, "SOLUSDT": 37}
    TIMEFRAME = "60"
    ATR_PERIOD = 5
    SUPERTREND_FACTOR = 3.0
    STOP_LOSS_PERCENT = 37
    TAKE_PROFIT_PERCENT = 150
    ENABLE_STOP_LOSS = True
    ENABLE_TAKE_PROFIT = True
    CHECK_INTERVAL = 60

from bybit_client import BybitClient
from twin_range_filter import calculate_twin_range_filter, get_latest_signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TwinRangeFilterBot:
    """Trading bot using Twin Range Filter strategy"""
    
    def __init__(self):
        """Initialize the trading bot"""
        self.client = BybitClient(
            api_key=BYBIT_API_KEY,
            api_secret=BYBIT_API_SECRET,
            testnet=USE_TESTNET
        )
        self.trading_pairs = TRADING_PAIRS
        self.last_signals: Dict[str, str] = {pair: 'none' for pair in TRADING_PAIRS}
        self.running = False
        self.wallet_balance = 0.0
        
        logger.info(f"Bot initialized - {'TESTNET' if USE_TESTNET else 'MAINNET'}")
        logger.info(f"Trading pairs: {', '.join(TRADING_PAIRS)}")
        logger.info(f"Position sizing: {POSITION_SIZE_PERCENT}% of wallet balance with 35x leverage")
        if ENABLE_STOP_LOSS:
            logger.info(f"Stop Loss enabled at {STOP_LOSS_PERCENT}% ROI loss")
        if ENABLE_TAKE_PROFIT:
            logger.info(f"Take Profit enabled at {TAKE_PROFIT_PERCENT}% ROI gain")
    
    def setup_leverage(self):
        """Set up leverage for all trading pairs"""
        for symbol in self.trading_pairs:
            leverage = LEVERAGE.get(symbol, 10)
            if self.client.set_leverage(symbol, leverage):
                logger.info(f"Leverage set to {leverage}x for {symbol}")
            else:
                logger.warning(f"Could not set leverage for {symbol}")
    
    def update_wallet_balance(self):
        """Update current wallet balance"""
        balance = self.client.get_wallet_balance()
        if balance:
            coins = balance.get('list', [{}])[0].get('coin', [])
            for coin in coins:
                if coin.get('coin') == 'USDT':
                    self.wallet_balance = float(coin.get('walletBalance', 0))
                    logger.debug(f"Wallet balance updated: {self.wallet_balance:.2f} USDT")
                    return self.wallet_balance
        return 0.0
    
    def calculate_position_size(self, symbol: str) -> float:
        """Calculate position size based on wallet balance percentage"""
        if USE_DYNAMIC_SIZING:
            # Update wallet balance
            self.update_wallet_balance()
            
            # Calculate USD amount as percentage of wallet
            usd_amount = self.wallet_balance * (POSITION_SIZE_PERCENT / 100)
            
            logger.info(f"Position size for {symbol}: ${usd_amount:.2f} ({POSITION_SIZE_PERCENT}% of ${self.wallet_balance:.2f})")
        else:
            # Fallback to fixed amount if dynamic sizing disabled
            usd_amount = 35
        
        return usd_amount
    
    def get_current_position(self, symbol: str) -> Dict:
        """Get current position info for a symbol"""
        position = self.client.get_position(symbol)
        
        if not position:
            return {'side': 'None', 'size': 0}
        
        # Helper function to safely convert to float
        def safe_float(value, default=0.0):
            try:
                return float(value) if value and value != '' else default
            except (ValueError, TypeError):
                return default
        
        return {
            'side': position.get('side', 'None'),
            'size': safe_float(position.get('size', 0)),
            'entry_price': safe_float(position.get('avgPrice', 0)),
            'unrealized_pnl': safe_float(position.get('unrealisedPnl', 0)),
            'leverage': position.get('leverage', 0)
        }
    
    def close_position(self, symbol: str) -> bool:
        """Close position for a symbol"""
        position = self.get_current_position(symbol)
        
        if position['size'] == 0:
            return True
        
        logger.info(f"Closing {position['side']} position for {symbol}")
        response = self.client.close_position(symbol)
        
        return response.get('retCode') == 0
    
    def open_long(self, symbol: str) -> bool:
        """Open a long position with proper SL/TP"""
        # Check if ANY other position is open
        if self.has_any_position():
            logger.info(f"❌ Cannot open LONG on {symbol} - another position is already active")
            return False
        
        # First, close any existing short position on this symbol
        position = self.get_current_position(symbol)
        
        if position['side'] == 'Sell' and position['size'] > 0:
            logger.info(f"Closing short position before opening long on {symbol}")
            if not self.close_position(symbol):
                logger.error(f"Failed to close short position on {symbol}")
                return False
            time.sleep(2)  # Wait for position to close
        
        # Calculate quantity
        usd_amount = self.calculate_position_size(symbol)
        leverage = LEVERAGE.get(symbol, 37)
        
        # Set leverage
        if not self.client.set_leverage(symbol, leverage):
            logger.error(f"Failed to set leverage for {symbol}")
            return False
        
        qty = self.client.calculate_qty(symbol, usd_amount, leverage)
        
        if qty == 0:
            logger.error(f"Could not calculate quantity for {symbol}")
            return False
        
        # Get current price for SL/TP calculation
        ticker = self.client.get_ticker(symbol)
        if not ticker:
            logger.error(f"Failed to get ticker for {symbol}")
            return False
        
        entry_price = float(ticker.get('lastPrice', 0))
        if entry_price == 0:
            logger.error(f"Invalid price for {symbol}")
            return False
        
        # Calculate stop loss and take profit prices for LONG
        # ROI Formula: roi = ((current_price - entry_price) / entry_price) * leverage * 100
        # So for price calculation from ROI:
        # price_move = entry_price * (ROI_PERCENT / leverage / 100)
        stop_loss_price = None
        take_profit_price = None
        
        if ENABLE_STOP_LOSS:
            # For LONG: stop loss is BELOW entry (price goes down = loss)
            # At SL trigger: roi = -STOP_LOSS_PERCENT
            price_move = entry_price * (STOP_LOSS_PERCENT / leverage / 100)
            stop_loss_price = entry_price - price_move
        
        if ENABLE_TAKE_PROFIT:
            # For LONG: take profit is ABOVE entry (price goes up = profit)
            # At TP trigger: roi = TAKE_PROFIT_PERCENT
            price_move = entry_price * (TAKE_PROFIT_PERCENT / leverage / 100)
            take_profit_price = entry_price + price_move
        
        # Place long order
        logger.info(f"Opening LONG position on {symbol} - Qty: {qty:.4f} @ ${entry_price:.4f} | {leverage}x")
        if stop_loss_price:
            price_move_percent = ((entry_price - stop_loss_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.4f} ({price_move_percent:.2f}% price move = {STOP_LOSS_PERCENT}% ROI loss)")
        if take_profit_price:
            price_move_percent = ((take_profit_price - entry_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.4f} ({price_move_percent:.2f}% price move = {TAKE_PROFIT_PERCENT}% ROI gain)")
        
        response = self.client.place_order(
            symbol=symbol,
            side='Buy',
            qty=qty,
            stop_loss=stop_loss_price,
            take_profit=take_profit_price
        )
        
        return response.get('retCode') == 0
    
    def open_short(self, symbol: str) -> bool:
        """Open a short position with proper SL/TP"""
        # Check if ANY other position is open
        if self.has_any_position():
            logger.info(f"❌ Cannot open SHORT on {symbol} - another position is already active")
            return False
        
        # First, close any existing long position on this symbol
        position = self.get_current_position(symbol)
        
        if position['side'] == 'Buy' and position['size'] > 0:
            logger.info(f"Closing long position before opening short on {symbol}")
            if not self.close_position(symbol):
                logger.error(f"Failed to close long position on {symbol}")
                return False
            time.sleep(2)  # Wait for position to close
        
        # Calculate quantity
        usd_amount = self.calculate_position_size(symbol)
        leverage = LEVERAGE.get(symbol, 37)
        
        # Set leverage
        if not self.client.set_leverage(symbol, leverage):
            logger.error(f"Failed to set leverage for {symbol}")
            return False
        
        qty = self.client.calculate_qty(symbol, usd_amount, leverage)
        
        if qty == 0:
            logger.error(f"Could not calculate quantity for {symbol}")
            return False
        
        # Get current price for SL/TP calculation
        ticker = self.client.get_ticker(symbol)
        if not ticker:
            logger.error(f"Failed to get ticker for {symbol}")
            return False
        
        entry_price = float(ticker.get('lastPrice', 0))
        if entry_price == 0:
            logger.error(f"Invalid price for {symbol}")
            return False
        
        # Calculate stop loss and take profit prices for SHORT
        # ROI Formula: roi = ((entry_price - current_price) / entry_price) * leverage * 100
        # So for price calculation from ROI:
        # price_move = entry_price * (ROI_PERCENT / leverage / 100)
        stop_loss_price = None
        take_profit_price = None
        
        if ENABLE_STOP_LOSS:
            # For SHORT: stop loss is ABOVE entry (price goes up = loss)
            # At SL trigger: roi = -STOP_LOSS_PERCENT
            price_move = entry_price * (STOP_LOSS_PERCENT / leverage / 100)
            stop_loss_price = entry_price + price_move
        
        if ENABLE_TAKE_PROFIT:
            # For SHORT: take profit is BELOW entry (price goes down = profit)
            # At TP trigger: roi = TAKE_PROFIT_PERCENT
            price_move = entry_price * (TAKE_PROFIT_PERCENT / leverage / 100)
            take_profit_price = entry_price - price_move
        
        # Place short order
        logger.info(f"Opening SHORT position on {symbol} - Qty: {qty:.4f} @ ${entry_price:.4f} | {leverage}x")
        if stop_loss_price:
            price_move_percent = ((stop_loss_price - entry_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.4f} ({price_move_percent:.2f}% price move = {STOP_LOSS_PERCENT}% ROI loss)")
        if take_profit_price:
            price_move_percent = ((entry_price - take_profit_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.4f} ({price_move_percent:.2f}% price move = {TAKE_PROFIT_PERCENT}% ROI gain)")
        
        response = self.client.place_order(
            symbol=symbol,
            side='Sell',
            qty=qty,
            stop_loss=stop_loss_price,
            take_profit=take_profit_price
        )
        
        return response.get('retCode') == 0
    
    def has_any_position(self) -> bool:
        """Check if ANY position is open across all pairs"""
        for symbol in self.trading_pairs:
            position = self.get_current_position(symbol)
            if position['size'] > 0:
                return True
        return False
    
    def process_signal(self, symbol: str, signal: str):
        """Process a trading signal - Close opposite position first, then open new position"""
        if signal == 'none':
            return
        
        current_position = self.get_current_position(symbol)
        
        if signal == 'long':
            logger.info(f"🟢 LONG SIGNAL on {symbol}")
            
            # If already in LONG on this symbol, skip
            if current_position['side'] == 'Buy' and current_position['size'] > 0:
                logger.info(f"Already in LONG position on {symbol}, skipping")
                return
            
            # If in SHORT on this symbol, close it first
            if current_position['side'] == 'Sell' and current_position['size'] > 0:
                logger.info(f"Closing SHORT position on {symbol} before opening LONG")
                if not self.close_position(symbol):
                    logger.error(f"Failed to close SHORT on {symbol}")
                    return
                time.sleep(2)
            
            # Try to open LONG
            if self.open_long(symbol):
                logger.info(f"✅ Successfully opened LONG on {symbol}")
            else:
                logger.error(f"❌ Failed to open LONG on {symbol}")
        
        elif signal == 'short':
            logger.info(f"🔴 SHORT SIGNAL on {symbol}")
            
            # If already in SHORT on this symbol, skip
            if current_position['side'] == 'Sell' and current_position['size'] > 0:
                logger.info(f"Already in SHORT position on {symbol}, skipping")
                return
            
            # If in LONG on this symbol, close it first
            if current_position['side'] == 'Buy' and current_position['size'] > 0:
                logger.info(f"Closing LONG position on {symbol} before opening SHORT")
                if not self.close_position(symbol):
                    logger.error(f"Failed to close LONG on {symbol}")
                    return
                time.sleep(2)
            
            # Try to open SHORT
            if self.open_short(symbol):
                logger.info(f"✅ Successfully opened SHORT on {symbol}")
            else:
                logger.error(f"❌ Failed to open SHORT on {symbol}")
    
    def check_stop_loss(self):
        """Check all positions for stop loss triggers"""
        if not ENABLE_STOP_LOSS:
            return
        
        for symbol in self.trading_pairs:
            try:
                position = self.get_current_position(symbol)
                
                if position['size'] == 0:
                    continue
                
                # Get current price
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    continue
                
                current_price = float(ticker.get('lastPrice', 0))
                entry_price = position['entry_price']
                side = position['side']
                leverage = float(position['leverage']) if position['leverage'] else 1
                
                if entry_price == 0 or current_price == 0 or leverage == 0:
                    continue
                
                # Calculate ROI percentage
                # Formula: roi = ((price_change / entry_price) * leverage * 100)
                if side == 'Buy':  # Long position
                    roi = ((current_price - entry_price) / entry_price) * leverage * 100
                else:  # Short position
                    roi = ((entry_price - current_price) / entry_price) * leverage * 100
                
                # Check if stop loss triggered (ROI <= -STOP_LOSS_PERCENT)
                if roi <= -STOP_LOSS_PERCENT:
                    logger.warning(
                        f"🛑 STOP LOSS TRIGGERED on {symbol} - "
                        f"ROI: {roi:.2f}% (Entry: ${entry_price:.4f}, Current: ${current_price:.4f}, Leverage: {leverage:.0f}x, Size: {position['size']:.4f})"
                    )
                    if self.close_position(symbol):
                        logger.info(f"✅ Stop loss executed successfully on {symbol}")
                    else:
                        logger.error(f"❌ Failed to execute stop loss on {symbol}")
                
            except Exception as e:
                logger.error(f"Error checking stop loss for {symbol}: {e}")
    
    def check_take_profit(self):
        """Check all positions for take profit triggers"""
        if not ENABLE_TAKE_PROFIT:
            return
        
        for symbol in self.trading_pairs:
            try:
                position = self.get_current_position(symbol)
                
                if position['size'] == 0:
                    continue
                
                # Get current price
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    continue
                
                current_price = float(ticker.get('lastPrice', 0))
                entry_price = position['entry_price']
                side = position['side']
                leverage = float(position['leverage']) if position['leverage'] else 1
                
                if entry_price == 0 or current_price == 0 or leverage == 0:
                    continue
                
                # Calculate ROI percentage
                # Formula: roi = ((price_change / entry_price) * leverage * 100)
                if side == 'Buy':  # Long position
                    roi = ((current_price - entry_price) / entry_price) * leverage * 100
                else:  # Short position
                    roi = ((entry_price - current_price) / entry_price) * leverage * 100
                
                # Check if take profit triggered (ROI >= TAKE_PROFIT_PERCENT)
                if roi >= TAKE_PROFIT_PERCENT:
                    logger.warning(
                        f"🎯 TAKE PROFIT TRIGGERED on {symbol} - "
                        f"ROI: {roi:.2f}% (Entry: ${entry_price:.4f}, Current: ${current_price:.4f}, Leverage: {leverage:.0f}x, Size: {position['size']:.4f})"
                    )
                    if self.close_position(symbol):
                        logger.info(f"✅ Take profit executed successfully on {symbol}")
                    else:
                        logger.error(f"❌ Failed to execute take profit on {symbol}")
                
            except Exception as e:
                logger.error(f"Error checking take profit for {symbol}: {e}")
    
    def check_signals(self):
        """Check for trading signals on all pairs"""
        for symbol in self.trading_pairs:
            try:
                # Fetch kline data
                df = self.client.get_klines(symbol, TIMEFRAME, limit=200)
                
                if df.empty:
                    logger.warning(f"No data received for {symbol}")
                    continue
                
                # Calculate Twin Range Filter
                df = calculate_twin_range_filter(
                    df,
                    fast_period=TWIN_RANGE_FAST_PERIOD,
                    fast_range=TWIN_RANGE_FAST_RANGE,
                    slow_period=TWIN_RANGE_SLOW_PERIOD,
                    slow_range=TWIN_RANGE_SLOW_RANGE
                )
                
                # Get latest signal
                signal = get_latest_signal(df)
                
                # Only process if it's a new signal
                if signal != 'none' and signal != self.last_signals[symbol]:
                    self.last_signals[symbol] = signal
                    self.process_signal(symbol, signal)
                elif signal == 'none':
                    self.last_signals[symbol] = 'none'
                
                # Log current state
                position = self.get_current_position(symbol)
                current_price = df['close'].iloc[-1]
                logger.debug(f"{symbol}: Price={current_price:.2f}, Position={position['side']} ({position['size']})")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
    
    def print_status(self):
        """Print current status of all positions"""
        logger.info("=" * 50)
        logger.info("CURRENT POSITIONS")
        logger.info("=" * 50)
        
        for symbol in self.trading_pairs:
            position = self.get_current_position(symbol)
            ticker = self.client.get_ticker(symbol)
            current_price = float(ticker.get('lastPrice', 0)) if ticker else 0
            
            if position['size'] > 0:
                pnl = position['unrealized_pnl']
                pnl_sign = '+' if pnl >= 0 else ''
                logger.info(
                    f"{symbol}: {position['side']} {position['size']} @ {position['entry_price']:.2f} "
                    f"| Current: {current_price:.2f} | PnL: {pnl_sign}{pnl:.2f} USDT"
                )
            else:
                logger.info(f"{symbol}: No position | Price: {current_price:.2f}")
        
        logger.info("=" * 50)
    
    def run(self):
        """Main bot loop"""
        logger.info("=" * 50)
        logger.info("TWIN RANGE FILTER TRADING BOT")
        logger.info("=" * 50)
        
        # Setup
        self.setup_leverage()
        self.running = True
        
        # Print initial status
        self.print_status()
        
        logger.info(f"Starting main loop - checking every {CHECK_INTERVAL} seconds")
        logger.info("Press Ctrl+C to stop")
        
        last_status_time = time.time()
        
        try:
            while self.running:
                # Check for stop losses first
                self.check_stop_loss()
                
                # Check for take profits
                self.check_take_profit()
                
                # Then check for new signals
                self.check_signals()
                
                # Print status every 5 minutes
                if time.time() - last_status_time > 300:
                    self.print_status()
                    last_status_time = time.time()
                
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\nBot stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Bot error: {e}")
            self.running = False
        
        self.print_status()
        logger.info("Bot shutdown complete")
    
    def test_connection(self):
        """Test connection and API credentials"""
        logger.info("Testing Bybit connection...")
        
        # Test market data
        for symbol in self.trading_pairs:
            ticker = self.client.get_ticker(symbol)
            if ticker:
                price = ticker.get('lastPrice', 'N/A')
                logger.info(f"{symbol}: {price}")
            else:
                logger.error(f"Failed to get ticker for {symbol}")
                return False
        
        # Test account access
        balance = self.client.get_wallet_balance()
        if balance:
            logger.info("✅ API connection successful!")
            coins = balance.get('list', [{}])[0].get('coin', [])
            for coin in coins:
                if coin.get('coin') == 'USDT':
                    logger.info(f"USDT Balance: {coin.get('walletBalance', 'N/A')}")
            return True
        else:
            logger.error("❌ Failed to access account. Check your API credentials.")
            return False


def main():
    """Main entry point"""
    bot = TwinRangeFilterBot()
    
    # Test connection first
    if not bot.test_connection():
        logger.error("Connection test failed. Please check your API keys in config.py")
        return
    
    # Run the bot
    bot.run()


if __name__ == "__main__":
    main()
