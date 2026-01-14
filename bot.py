"""
Supertrend Trading Bot
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
        ATR_PERIOD,
        SUPERTREND_FACTOR,
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
    LEVERAGE = {"BTCUSDT": 10, "ETHUSDT": 10, "SOLUSDT": 10}
    TIMEFRAME = "5"
    ATR_PERIOD = 5
    SUPERTREND_FACTOR = 3.0
    STOP_LOSS_PERCENT = 42
    TAKE_PROFIT_PERCENT = 150
    ENABLE_STOP_LOSS = True
    ENABLE_TAKE_PROFIT = True
    CHECK_INTERVAL = 60

from bybit_client import BybitClient
from supertrend import calculate_supertrend, get_latest_signal

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


class SupertrendBot:
    """Trading bot using Supertrend strategy"""
    
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
        logger.info(f"Position sizing: {POSITION_SIZE_PERCENT}% of wallet balance")
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
        # First, close any existing short position
        position = self.get_current_position(symbol)
        
        if position['side'] == 'Sell' and position['size'] > 0:
            logger.info(f"Closing short position before opening long on {symbol}")
            if not self.close_position(symbol):
                logger.error(f"Failed to close short position on {symbol}")
                return False
            time.sleep(1)  # Wait a moment
        
        # Calculate quantity
        usd_amount = self.calculate_position_size(symbol)
        leverage = self.client.get_max_leverage(symbol)
        
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
        # Formula: entry_price * (1 ± ROI% / leverage / 100)
        stop_loss_price = None
        take_profit_price = None
        
        if ENABLE_STOP_LOSS:
            # For LONG: stop loss is BELOW entry (price goes down = loss)
            price_move_percent = STOP_LOSS_PERCENT / leverage
            stop_loss_price = entry_price * (1 - price_move_percent / 100)
        
        if ENABLE_TAKE_PROFIT:
            # For LONG: take profit is ABOVE entry (price goes up = profit)
            price_move_percent = TAKE_PROFIT_PERCENT / leverage
            take_profit_price = entry_price * (1 + price_move_percent / 100)
        
        # Place long order
        logger.info(f"Opening LONG position on {symbol} - Qty: {qty} @ ${entry_price:.2f} | {leverage}x")
        if stop_loss_price:
            actual_price_move = ((entry_price - stop_loss_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.2f} ({actual_price_move:.2f}% price = {STOP_LOSS_PERCENT}% ROI)")
        if take_profit_price:
            actual_price_move = ((take_profit_price - entry_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.2f} ({actual_price_move:.2f}% price = {TAKE_PROFIT_PERCENT}% ROI)")
        
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
        # First, close any existing long position
        position = self.get_current_position(symbol)
        
        if position['side'] == 'Buy' and position['size'] > 0:
            logger.info(f"Closing long position before opening short on {symbol}")
            if not self.close_position(symbol):
                logger.error(f"Failed to close long position on {symbol}")
                return False
            time.sleep(1)  # Wait a moment
        
        # Calculate quantity
        usd_amount = self.calculate_position_size(symbol)
        leverage = self.client.get_max_leverage(symbol)
        
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
        # Formula: entry_price * (1 ± ROI% / leverage / 100)
        stop_loss_price = None
        take_profit_price = None
        
        if ENABLE_STOP_LOSS:
            # For SHORT: stop loss is ABOVE entry (price goes up = loss)
            price_move_percent = STOP_LOSS_PERCENT / leverage
            stop_loss_price = entry_price * (1 + price_move_percent / 100)
        
        if ENABLE_TAKE_PROFIT:
            # For SHORT: take profit is BELOW entry (price goes down = profit)
            price_move_percent = TAKE_PROFIT_PERCENT / leverage
            take_profit_price = entry_price * (1 - price_move_percent / 100)
        
        # Place short order
        logger.info(f"Opening SHORT position on {symbol} - Qty: {qty} @ ${entry_price:.2f} | {leverage}x")
        if stop_loss_price:
            actual_price_move = ((stop_loss_price - entry_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.2f} ({actual_price_move:.2f}% price = {STOP_LOSS_PERCENT}% ROI)")
        if take_profit_price:
            actual_price_move = ((entry_price - take_profit_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.2f} ({actual_price_move:.2f}% price = {TAKE_PROFIT_PERCENT}% ROI)")
        
        response = self.client.place_order(
            symbol=symbol,
            side='Sell',
            qty=qty,
            stop_loss=stop_loss_price,
            take_profit=take_profit_price
        )
        
        return response.get('retCode') == 0
    
    def process_signal(self, symbol: str, signal: str):
        """Process a trading signal"""
        if signal == 'none':
            return
        
        current_position = self.get_current_position(symbol)
        
        if signal == 'long':
            # Don't open if already long
            if current_position['side'] == 'Buy' and current_position['size'] > 0:
                logger.info(f"Already in LONG position on {symbol}, skipping")
                return
            
            logger.info(f"🟢 LONG SIGNAL on {symbol}")
            if self.open_long(symbol):
                logger.info(f"✅ Successfully opened LONG on {symbol}")
            else:
                logger.error(f"❌ Failed to open LONG on {symbol}")
        
        elif signal == 'short':
            # Don't open if already short
            if current_position['side'] == 'Sell' and current_position['size'] > 0:
                logger.info(f"Already in SHORT position on {symbol}, skipping")
                return
            
            logger.info(f"🔴 SHORT SIGNAL on {symbol}")
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
                leverage = position['leverage']
                
                if entry_price == 0 or current_price == 0 or leverage == 0:
                    continue
                
                # Calculate ROI percentage
                if side == 'Buy':  # Long position
                    roi = ((current_price - entry_price) / entry_price) * leverage * 100
                else:  # Short position
                    roi = ((entry_price - current_price) / entry_price) * leverage * 100
                
                # Check if stop loss triggered (ROI <= -STOP_LOSS_PERCENT)
                if roi <= -STOP_LOSS_PERCENT:
                    logger.warning(
                        f"🛑 STOP LOSS TRIGGERED on {symbol} - "
                        f"ROI: {roi:.2f}% (Entry: {entry_price:.2f}, Current: {current_price:.2f}, Leverage: {leverage}x)"
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
                leverage = position['leverage']
                
                if entry_price == 0 or current_price == 0 or leverage == 0:
                    continue
                
                # Calculate ROI percentage
                if side == 'Buy':  # Long position
                    roi = ((current_price - entry_price) / entry_price) * leverage * 100
                else:  # Short position
                    roi = ((entry_price - current_price) / entry_price) * leverage * 100
                
                # Check if take profit triggered (ROI >= TAKE_PROFIT_PERCENT)
                if roi >= TAKE_PROFIT_PERCENT:
                    logger.warning(
                        f"🎯 TAKE PROFIT TRIGGERED on {symbol} - "
                        f"ROI: {roi:.2f}% (Entry: {entry_price:.2f}, Current: {current_price:.2f}, Leverage: {leverage}x)"
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
                
                # Calculate Supertrend
                df = calculate_supertrend(
                    df,
                    atr_period=ATR_PERIOD,
                    factor=SUPERTREND_FACTOR
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
        logger.info("SUPERTREND TRADING BOT")
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
    bot = SupertrendBot()
    
    # Test connection first
    if not bot.test_connection():
        logger.error("Connection test failed. Please check your API keys in config.py")
        return
    
    # Run the bot
    bot.run()


if __name__ == "__main__":
    main()
