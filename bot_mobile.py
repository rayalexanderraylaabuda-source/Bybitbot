"""
Mobile Trading Bot - Runs directly on Android via Termux
Simplified version optimized for mobile devices
"""

import time
import logging
import json
from datetime import datetime
from typing import Dict
import os
import signal
import sys

from bybit_client import BybitClient
from supertrend import calculate_supertrend, get_latest_signal

# Configure logging for mobile
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_mobile.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MobileTradingBot:
    """Mobile-optimized trading bot"""
    
    def __init__(self, config_file='mobile_config.json'):
        """Initialize from config file"""
        self.config = self.load_config(config_file)
        
        self.client = BybitClient(
            api_key=self.config['api_key'],
            api_secret=self.config['api_secret'],
            testnet=self.config['testnet']
        )
        
        self.trading_pairs = self.config['trading_pairs']
        self.last_signals: Dict[str, str] = {pair: 'none' for pair in self.trading_pairs}
        self.running = False
        self.wallet_balance = 0.0
        
        logger.info("📱 Mobile Bot initialized")
        logger.info(f"Mode: {'TESTNET' if self.config['testnet'] else 'MAINNET'}")
        logger.info(f"Pairs: {', '.join(self.trading_pairs)}")
    
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        if not os.path.exists(config_file):
            logger.error(f"Config file not found: {config_file}")
            logger.info("Creating default config file...")
            self.create_default_config(config_file)
            logger.info(f"Please edit {config_file} with your API keys and settings")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def create_default_config(self, config_file):
        """Create default config file"""
        default_config = {
            "api_key": "YOUR_API_KEY_HERE",
            "api_secret": "YOUR_API_SECRET_HERE",
            "testnet": True,
            "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "leverage": {
                "BTCUSDT": 37,
                "ETHUSDT": 37,
                "SOLUSDT": 37
            },
            "position_size_percent": 35,
            "timeframe": "5",
            "atr_period": 5,
            "supertrend_factor": 3.0,
            "stop_loss_percent": 37,
            "take_profit_percent": 150,
            "enable_stop_loss": True,
            "enable_take_profit": True,
            "check_interval": 60
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
    
    def save_state(self):
        """Save current state to file"""
        state = {
            'last_signals': self.last_signals,
            'last_update': datetime.now().isoformat()
        }
        with open('bot_state.json', 'w') as f:
            json.dump(state, f, indent=4)
    
    def load_state(self):
        """Load previous state from file"""
        if os.path.exists('bot_state.json'):
            try:
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                    self.last_signals = state.get('last_signals', self.last_signals)
                    logger.info("Previous state restored")
            except:
                pass
    
    def setup_leverage(self):
        """Set up leverage for all pairs"""
        for symbol in self.trading_pairs:
            leverage = self.config['leverage'].get(symbol, 10)
            if self.client.set_leverage(symbol, leverage):
                logger.info(f"✓ {symbol}: {leverage}x")
    
    def update_wallet_balance(self):
        """Update wallet balance"""
        balance = self.client.get_wallet_balance()
        if balance:
            coins = balance.get('list', [{}])[0].get('coin', [])
            for coin in coins:
                if coin.get('coin') == 'USDT':
                    self.wallet_balance = float(coin.get('walletBalance', 0))
                    return self.wallet_balance
        return 0.0
    
    def calculate_position_size(self, symbol: str) -> float:
        """Calculate position size from wallet percentage"""
        self.update_wallet_balance()
        usd_amount = self.wallet_balance * (self.config['position_size_percent'] / 100)
        return usd_amount
    
    def get_position(self, symbol: str) -> Dict:
        """Get current position"""
        position = self.client.get_position(symbol)
        
        if not position:
            return {'side': 'None', 'size': 0}
        
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
            'leverage': safe_float(position.get('leverage', 0))
        }
    
    def close_position(self, symbol: str) -> bool:
        """Close position"""
        position = self.get_position(symbol)
        
        if position['size'] == 0:
            return True
        
        close_side = 'Sell' if position['side'] == 'Buy' else 'Buy'
        
        logger.info(f"Closing {position['side']} on {symbol}")
        response = self.client.place_order(
            symbol=symbol,
            side=close_side,
            qty=position['size'],
            reduce_only=True
        )
        
        return response.get('retCode') == 0
    
    def open_long(self, symbol: str) -> bool:
        """Open long position"""
        position = self.get_position(symbol)
        
        if position['side'] == 'Sell' and position['size'] > 0:
            if not self.close_position(symbol):
                return False
            time.sleep(1)
        
        usd_amount = self.calculate_position_size(symbol)
        leverage = self.config['leverage'].get(symbol, 37)
        qty = self.client.calculate_qty(symbol, usd_amount, leverage)
        
        if qty == 0:
            return False
        
        logger.info(f"🟢 LONG {symbol} - ${usd_amount:.2f} ({qty})")
        response = self.client.place_order(symbol=symbol, side='Buy', qty=qty)
        
        return response.get('retCode') == 0
    
    def open_short(self, symbol: str) -> bool:
        """Open short position"""
        position = self.get_position(symbol)
        
        if position['side'] == 'Buy' and position['size'] > 0:
            if not self.close_position(symbol):
                return False
            time.sleep(1)
        
        usd_amount = self.calculate_position_size(symbol)
        leverage = self.config['leverage'].get(symbol, 37)
        qty = self.client.calculate_qty(symbol, usd_amount, leverage)
        
        if qty == 0:
            return False
        
        logger.info(f"🔴 SHORT {symbol} - ${usd_amount:.2f} ({qty})")
        response = self.client.place_order(symbol=symbol, side='Sell', qty=qty)
        
        return response.get('retCode') == 0
    
    def check_stop_loss(self):
        """Check stop loss for all positions"""
        if not self.config['enable_stop_loss']:
            return
        
        for symbol in self.trading_pairs:
            try:
                position = self.get_position(symbol)
                
                if position['size'] == 0:
                    continue
                
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
                
                if roi <= -self.config['stop_loss_percent']:
                    logger.warning(f"🛑 STOP LOSS {symbol} - ROI: {roi:.2f}%")
                    self.close_position(symbol)
                
            except Exception as e:
                logger.error(f"Stop loss error {symbol}: {e}")
    
    def check_signals(self):
        """Check trading signals"""
        for symbol in self.trading_pairs:
            try:
                df = self.client.get_klines(symbol, self.config['timeframe'], limit=200)
                
                if df.empty:
                    continue
                
                df = calculate_supertrend(
                    df,
                    atr_period=self.config.get('atr_period', 10),
                    factor=self.config.get('supertrend_factor', 3.0)
                )
                
                signal = get_latest_signal(df)
                
                if signal != 'none' and signal != self.last_signals[symbol]:
                    self.last_signals[symbol] = signal
                    
                    if signal == 'long':
                        self.open_long(symbol)
                    elif signal == 'short':
                        self.open_short(symbol)
                    
                    self.save_state()
                elif signal == 'none':
                    self.last_signals[symbol] = 'none'
                
            except Exception as e:
                logger.error(f"Error {symbol}: {e}")
    
    def print_status(self):
        """Print current status"""
        logger.info("=" * 50)
        self.update_wallet_balance()
        logger.info(f"💰 Balance: ${self.wallet_balance:.2f}")
        
        total_pnl = 0.0
        active = 0
        
        for symbol in self.trading_pairs:
            pos = self.get_position(symbol)
            ticker = self.client.get_ticker(symbol)
            price = float(ticker.get('lastPrice', 0)) if ticker else 0
            
            if pos['size'] > 0:
                pnl_sign = '+' if pos['unrealized_pnl'] >= 0 else ''
                logger.info(
                    f"{symbol}: {pos['side']} ${pos['unrealized_pnl']:.2f} "
                    f"@ {price:.4f}"
                )
                total_pnl += pos['unrealized_pnl']
                active += 1
            else:
                logger.info(f"{symbol}: No position @ {price:.4f}")
        
        logger.info(f"📊 Active: {active} | Total PnL: ${total_pnl:.2f}")
        logger.info("=" * 50)
    
    def run(self):
        """Main bot loop"""
        logger.info("=" * 50)
        logger.info("📱 MOBILE TRADING BOT STARTED")
        logger.info("=" * 50)
        
        # Load previous state
        self.load_state()
        
        # Setup
        self.setup_leverage()
        self.print_status()
        self.running = True
        
        logger.info(f"⏰ Checking every {self.config['check_interval']}s")
        logger.info("Press Ctrl+C to stop")
        
        last_status = time.time()
        
        try:
            while self.running:
                self.check_stop_loss()
                self.check_signals()
                
                # Print status every 5 minutes
                if time.time() - last_status > 300:
                    self.print_status()
                    last_status = time.time()
                
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping bot...")
            self.running = False
        except Exception as e:
            logger.error(f"Bot error: {e}")
            self.running = False
        
        self.save_state()
        self.print_status()
        logger.info("✓ Bot stopped")


def main():
    """Main entry point"""
    bot = MobileTradingBot()
    
    # Test connection
    logger.info("Testing connection...")
    if not bot.client.get_ticker('BTCUSDT'):
        logger.error("❌ Connection failed")
        return
    
    logger.info("✅ Connection successful")
    bot.run()


if __name__ == "__main__":
    main()
