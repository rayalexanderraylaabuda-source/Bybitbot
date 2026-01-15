"""
Lightweight Mobile Trading Bot - No pandas required!
Only needs: requests
"""

import time
import logging
import json
from datetime import datetime
import os
import sys

from bybit_client_lite import BybitClientLite
from supertrend_lite import calculate_supertrend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LiteMobileBot:
    """Ultra-lightweight mobile trading bot"""
    
    # Default risk management values
    DEFAULT_STOP_LOSS_PERCENT = 37
    DEFAULT_TAKE_PROFIT_PERCENT = 150
    
    def __init__(self):
        """Initialize bot"""
        self.config = self.load_config()
        
        self.client = BybitClientLite(
            api_key=self.config['api_key'],
            api_secret=self.config['api_secret'],
            testnet=self.config['testnet']
        )
        
        self.pairs = self.config['trading_pairs']
        self.last_signals = {pair: 'none' for pair in self.pairs}
        self.running = False
        self.wallet = 0.0
        
        logger.info("📱 Lite Bot Started")
        logger.info(f"Mode: {'TEST' if self.config['testnet'] else 'LIVE'}")
        logger.info(f"Pairs: {len(self.pairs)}")
    
    def load_config(self):
        """Load or create config"""
        config_file = 'mobile_config.json'
        
        if not os.path.exists(config_file):
            logger.info("Creating config file...")
            config = {
                "api_key": "YOUR_API_KEY",
                "api_secret": "YOUR_API_SECRET",
                "testnet": True,
                "position_mode": "one-way",
                "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ZECUSDT", "FARTCOINUSDT"],
                "leverage": {
                    "BTCUSDT": 37,
                    "ETHUSDT": 37,
                    "SOLUSDT": 37,
                    "XRPUSDT": 37,
                    "DOGEUSDT": 37,
                    "ZECUSDT": 37,
                    "FARTCOINUSDT": 37
                },
                "position_size_percent": 35,
                "timeframe": "60",
                "atr_period": 5,
                "supertrend_factor": 3.0,
                "stop_loss_percent": 37,
                "enable_stop_loss": True,
                "take_profit_percent": 150,
                "enable_take_profit": True,
                "check_interval": 60
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Edit {config_file} with your API keys!")
            logger.info("")
            logger.info("IMPORTANT:")
            logger.info("- If testnet = true, get keys from: https://testnet.bybit.com")
            logger.info("- If testnet = false, get keys from: https://www.bybit.com")
            logger.info("- Testnet keys DON'T work on mainnet and vice versa!")
            sys.exit(0)
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Validate config
        if config['api_key'] == 'YOUR_API_KEY':
            logger.error("Please edit mobile_config.json with your API keys!")
            sys.exit(1)
        
        return config
    
    def save_state(self):
        """Save state"""
        with open('bot_state.json', 'w') as f:
            json.dump({'signals': self.last_signals, 'time': datetime.now().isoformat()}, f)
    
    def has_any_position(self):
        """Check if ANY position is open"""
        for symbol in self.pairs:
            pos = self.get_position(symbol)
            if pos['size'] > 0:
                return True
        return False
    
    def load_state(self):
        """Load state"""
        if os.path.exists('bot_state.json'):
            try:
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                    self.last_signals = state.get('signals', self.last_signals)
            except:
                pass
    
    def setup_leverage(self):
        """Setup leverage"""
        for symbol in self.pairs:
            lev = self.config['leverage'].get(symbol, 10)
            if self.client.set_leverage(symbol, lev):
                logger.info(f"✓ {symbol}: {lev}x")
    
    def update_wallet(self):
        """Update balance"""
        bal = self.client.get_wallet_balance()
        if bal:
            for coin in bal.get('list', [{}])[0].get('coin', []):
                if coin.get('coin') == 'USDT':
                    self.wallet = float(coin.get('walletBalance', 0))
                    return self.wallet
        return 0.0
    
    def calc_size(self, symbol):
        """Calculate position size"""
        self.update_wallet()
        return self.wallet * (self.config['position_size_percent'] / 100)
    
    def get_position(self, symbol):
        """Get position"""
        pos = self.client.get_position(symbol)
        if not pos:
            return {'side': 'None', 'size': 0, 'entry': 0, 'pnl': 0}
        
        def safe(val, default=0):
            try:
                return float(val) if val and val != '' else default
            except:
                return default
        
        return {
            'side': pos.get('side', 'None'),
            'size': safe(pos.get('size')),
            'entry': safe(pos.get('avgPrice')),
            'pnl': safe(pos.get('unrealisedPnl')),
            'leverage': safe(pos.get('leverage'))
        }
    
    def close_pos(self, symbol):
        """Close position"""
        pos = self.get_position(symbol)
        if pos['size'] == 0:
            return True
        
        side = 'Sell' if pos['side'] == 'Buy' else 'Buy'
        logger.info(f"Closing {pos['side']} {symbol}")
        
        resp = self.client.place_order(symbol, side, pos['size'], reduce_only=True)
        return resp.get('retCode') == 0
    
    def open_long(self, symbol):
        """Open long"""
        pos = self.get_position(symbol)
        
        if pos['side'] == 'Sell' and pos['size'] > 0:
            if not self.close_pos(symbol):
                return False
            time.sleep(1)
        
        usd = self.calc_size(symbol)
        lev = self.config['leverage'].get(symbol, 37)
        qty = self.client.calculate_qty(symbol, usd, lev)
        
        if qty == 0:
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
        # IMPORTANT: Account for leverage! With 100x leverage, 1% price move = 100% ROI
        stop_loss_price = None
        take_profit_price = None
        
        if self.config.get('enable_stop_loss', False):
            sl_percent = self.config.get('stop_loss_percent', self.DEFAULT_STOP_LOSS_PERCENT)
            # Price move needed = ROI% / leverage
            price_move_percent = sl_percent / lev
            stop_loss_price = entry_price * (1 - price_move_percent / 100)
        
        if self.config.get('enable_take_profit', False):
            tp_percent = self.config.get('take_profit_percent', self.DEFAULT_TAKE_PROFIT_PERCENT)
            # Price move needed = ROI% / leverage
            price_move_percent = tp_percent / lev
            take_profit_price = entry_price * (1 + price_move_percent / 100)
        
        logger.info(f"🟢 LONG {symbol} ${usd:.2f} @ ${entry_price:.2f} | {lev}x")
        if stop_loss_price:
            actual_price_move = ((entry_price - stop_loss_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.2f} ({actual_price_move:.2f}% price = {self.config.get('stop_loss_percent', 42)}% ROI)")
        if take_profit_price:
            actual_price_move = ((take_profit_price - entry_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.2f} ({actual_price_move:.2f}% price = {self.config.get('take_profit_percent', 150)}% ROI)")
        
        resp = self.client.place_order(symbol, 'Buy', qty, stop_loss=stop_loss_price, take_profit=take_profit_price)
        return resp.get('retCode') == 0
    
    def open_short(self, symbol):
        """Open short"""
        pos = self.get_position(symbol)
        
        if pos['side'] == 'Buy' and pos['size'] > 0:
            if not self.close_pos(symbol):
                return False
            time.sleep(1)
        
        usd = self.calc_size(symbol)
        lev = self.config['leverage'].get(symbol, 37)
        qty = self.client.calculate_qty(symbol, usd, lev)
        
        if qty == 0:
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
        # IMPORTANT: Account for leverage! With 100x leverage, 1% price move = 100% ROI
        stop_loss_price = None
        take_profit_price = None
        
        if self.config.get('enable_stop_loss', False):
            sl_percent = self.config.get('stop_loss_percent', self.DEFAULT_STOP_LOSS_PERCENT)
            # For SHORT: stop loss is ABOVE entry price (price goes up = loss)
            # Price move needed = ROI% / leverage
            price_move_percent = sl_percent / lev
            stop_loss_price = entry_price * (1 + price_move_percent / 100)
        
        if self.config.get('enable_take_profit', False):
            tp_percent = self.config.get('take_profit_percent', self.DEFAULT_TAKE_PROFIT_PERCENT)
            # For SHORT: take profit is BELOW entry price (price goes down = profit)
            # Price move needed = ROI% / leverage
            price_move_percent = tp_percent / lev
            take_profit_price = entry_price * (1 - price_move_percent / 100)
        
        logger.info(f"🔴 SHORT {symbol} ${usd:.2f} @ ${entry_price:.2f} | {lev}x")
        if stop_loss_price:
            actual_price_move = ((stop_loss_price - entry_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.2f} ({actual_price_move:.2f}% price = {self.config.get('stop_loss_percent', 42)}% ROI)")
        if take_profit_price:
            actual_price_move = ((entry_price - take_profit_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.2f} ({actual_price_move:.2f}% price = {self.config.get('take_profit_percent', 150)}% ROI)")
        
        resp = self.client.place_order(symbol, 'Sell', qty, stop_loss=stop_loss_price, take_profit=take_profit_price)
        return resp.get('retCode') == 0
    
    def check_stop_loss_take_profit(self):
        """Check stop loss and take profit based on ROI"""
        if not self.config.get('enable_stop_loss', False) and not self.config.get('enable_take_profit', False):
            return
        
        for symbol in self.pairs:
            try:
                pos = self.get_position(symbol)
                if pos['size'] == 0:
                    continue
                
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    continue
                
                price = float(ticker.get('lastPrice', 0))
                if pos['entry'] == 0 or price == 0 or pos['leverage'] == 0:
                    continue
                
                # Calculate ROI (Return on Investment) percentage
                if pos['side'] == 'Buy':
                    roi = ((price - pos['entry']) / pos['entry']) * pos['leverage'] * 100
                else:
                    roi = ((pos['entry'] - price) / pos['entry']) * pos['leverage'] * 100
                
                # Check Stop Loss
                if self.config.get('enable_stop_loss', False):
                    stop_loss_percent = self.config.get('stop_loss_percent', self.DEFAULT_STOP_LOSS_PERCENT)
                    if roi <= -stop_loss_percent:
                        logger.warning(f"🛑 SL {symbol} ROI: {roi:.1f}%")
                        self.close_pos(symbol)
                        continue
                
                # Check Take Profit
                if self.config.get('enable_take_profit', False):
                    take_profit_percent = self.config.get('take_profit_percent', self.DEFAULT_TAKE_PROFIT_PERCENT)
                    if roi >= take_profit_percent:
                        logger.info(f"💰 TP {symbol} ROI: {roi:.1f}%")
                        self.close_pos(symbol)
                        
            except Exception as e:
                logger.error(f"SL/TP error {symbol}: {e}")
    
    def check_signals(self):
        """Check signals"""
        for symbol in self.pairs:
            try:
                # Get klines (already returns list of lists)
                candles = self.client.get_klines(symbol, self.config['timeframe'], limit=200)
                
                if not candles:
                    continue
                
                # Calculate Supertrend signals
                result = calculate_supertrend(
                    candles,
                    atr_period=self.config.get('atr_period', 10),
                    factor=self.config.get('supertrend_factor', 3.0)
                )
                
                # Determine signal
                if result['long_signal']:
                    signal = 'long'
                elif result['short_signal']:
                    signal = 'short'
                else:
                    signal = 'none'
                
                # Execute if new signal
                if signal != 'none' and signal != self.last_signals[symbol]:
                    self.last_signals[symbol] = signal
                    
                    # Check if we already have ANY position open
                    if self.has_any_position():
                        logger.info(f"❌ Already have an open position elsewhere, cannot trade {symbol} ({signal})")
                    elif signal == 'long':
                        self.open_long(symbol)
                    elif signal == 'short':
                        self.open_short(symbol)
                    
                    self.save_state()
                elif signal == 'none':
                    self.last_signals[symbol] = 'none'
                
            except Exception as e:
                logger.error(f"{symbol}: {e}")
    
    def status(self):
        """Print status"""
        logger.info("=" * 40)
        self.update_wallet()
        logger.info(f"💰 ${self.wallet:.2f}")
        
        total_pnl = 0
        active = 0
        
        for symbol in self.pairs:
            pos = self.get_position(symbol)
            ticker = self.client.get_ticker(symbol)
            price = float(ticker.get('lastPrice', 0)) if ticker else 0
            
            if pos['size'] > 0:
                logger.info(f"{symbol}: {pos['side']} ${pos['pnl']:.2f} @ {price:.4f}")
                total_pnl += pos['pnl']
                active += 1
            else:
                logger.info(f"{symbol}: - @ {price:.4f}")
        
        logger.info(f"Active: {active} | PnL: ${total_pnl:.2f}")
        logger.info("=" * 40)
    
    def run(self):
        """Main loop"""
        logger.info("=" * 40)
        logger.info("🤖 TRADING BOT")
        logger.info("=" * 40)
        
        self.load_state()
        self.setup_leverage()
        self.status()
        self.running = True
        
        logger.info(f"⏰ Check every {self.config['check_interval']}s")
        logger.info("Ctrl+C to stop")
        
        last_status = time.time()
        
        try:
            while self.running:
                self.check_stop_loss_take_profit()
                self.check_signals()
                
                if time.time() - last_status > 300:
                    self.status()
                    last_status = time.time()
                
                time.sleep(self.config['check_interval'])
        
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
            self.running = False
        except Exception as e:
            logger.error(f"Error: {e}")
            self.running = False
        
        self.save_state()
        self.status()
        logger.info("✓ Stopped")


def main():
    bot = LiteMobileBot()
    
    logger.info("=" * 50)
    logger.info(f"Testing {'TESTNET' if bot.config['testnet'] else 'MAINNET'} connection...")
    logger.info("=" * 50)
    
    # Test public endpoint first (doesn't need auth)
    logger.info("Step 1: Testing market data (no auth)...")
    for i in range(3):
        ticker = bot.client.get_ticker('BTCUSDT')
        if ticker and ticker.get('lastPrice'):
            logger.info(f"✅ Market data OK - BTC: ${ticker.get('lastPrice')}")
            break
        logger.warning(f"Retry {i+1}/3...")
        time.sleep(2)
    else:
        logger.error("❌ Cannot reach Bybit API")
        logger.info("Check your internet connection")
        return
    
    # Test authenticated endpoint
    logger.info("Step 2: Testing API keys...")
    balance = bot.client.get_wallet_balance()
    if balance and balance.get('list'):
        logger.info("✅ API keys valid!")
        
        # Show balance
        for coin in balance.get('list', [{}])[0].get('coin', []):
            if coin.get('coin') == 'USDT':
                logger.info(f"💰 USDT Balance: {coin.get('walletBalance', 'N/A')}")
        
        logger.info("=" * 50)
        bot.run()
    else:
        logger.error("❌ API key authentication failed")
        logger.info("")
        logger.info("⚠️ COMMON ISSUE: Bybit testnet API often has problems")
        logger.info("")
        logger.info("SOLUTION: Use MAINNET with real API keys")
        logger.info("(Don't worry - just use small position sizes!)")
        logger.info("")
        logger.info("Steps to switch to mainnet:")
        logger.info("1. Edit mobile_config.json")
        logger.info("2. Change: \"testnet\": true → \"testnet\": false")
        logger.info("3. Use API keys from: https://www.bybit.com (not testnet)")
        logger.info("4. Set small position_size_percent (like 10-20%)")
        logger.info("5. Use lower leverage (10-25x instead of 100x)")
        logger.info("")
        logger.info("Alternative troubleshooting:")
        logger.info("- Wait a few hours and try testnet again")
        logger.info("- Verify API key has 'Derivatives Contract' permission")
        logger.info("- Check API key hasn't expired")
        return


if __name__ == "__main__":
    main()
