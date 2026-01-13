"""
Web Dashboard for Supertrend Trading Bot
Access from any device including Android phones
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import time
import logging
from datetime import datetime
from bot import SupertrendBot

try:
    from config import TRADING_PAIRS, LEVERAGE, POSITION_SIZE_PERCENT, ENABLE_STOP_LOSS, STOP_LOSS_PERCENT
except ImportError:
    # Default values if config doesn't exist
    TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    LEVERAGE = {"BTCUSDT": 10, "ETHUSDT": 10, "SOLUSDT": 10}
    POSITION_SIZE_PERCENT = 35
    ENABLE_STOP_LOSS = True
    STOP_LOSS_PERCENT = 42

app = Flask(__name__)
CORS(app)

# Global bot instance and control variables
bot = None
bot_thread = None
bot_running = False
bot_status = {
    'running': False,
    'start_time': None,
    'positions': {},
    'last_update': None,
    'wallet_balance': 0.0,
    'total_pnl': 0.0
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_bot():
    """Run the bot in a separate thread"""
    global bot, bot_running, bot_status
    
    try:
        bot.running = True
        bot_running = True
        bot_status['running'] = True
        bot_status['start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        bot.setup_leverage()
        
        while bot_running and bot.running:
            # Check stop loss
            bot.check_stop_loss()
            
            # Check signals
            bot.check_signals()
            
            # Update status
            update_status()
            
            time.sleep(60)  # Check every minute
            
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_running = False
        bot_status['running'] = False


def update_status():
    """Update bot status information"""
    global bot, bot_status
    
    if not bot:
        return
    
    try:
        # Update wallet balance
        bot.update_wallet_balance()
        bot_status['wallet_balance'] = bot.wallet_balance
        
        # Update positions
        positions = {}
        total_pnl = 0.0
        
        for symbol in TRADING_PAIRS:
            pos = bot.get_current_position(symbol)
            ticker = bot.client.get_ticker(symbol)
            current_price = float(ticker.get('lastPrice', 0)) if ticker else 0
            
            positions[symbol] = {
                'side': pos['side'],
                'size': pos['size'],
                'entry_price': pos['entry_price'],
                'current_price': current_price,
                'unrealized_pnl': pos['unrealized_pnl']
            }
            
            total_pnl += pos['unrealized_pnl']
        
        bot_status['positions'] = positions
        bot_status['total_pnl'] = total_pnl
        bot_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        logger.error(f"Error updating status: {e}")


@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/status')
def get_status():
    """Get current bot status"""
    return jsonify(bot_status)


@app.route('/api/config')
def get_config():
    """Get bot configuration"""
    config = {
        'trading_pairs': TRADING_PAIRS,
        'leverage': LEVERAGE,
        'position_size_percent': POSITION_SIZE_PERCENT,
        'stop_loss_enabled': ENABLE_STOP_LOSS,
        'stop_loss_percent': STOP_LOSS_PERCENT
    }
    return jsonify(config)


@app.route('/api/start', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    global bot, bot_thread, bot_running
    
    if bot_running:
        return jsonify({'success': False, 'message': 'Bot is already running'})
    
    try:
        # Initialize bot
        bot = SupertrendBot()
        
        # Test connection
        if not bot.test_connection():
            return jsonify({'success': False, 'message': 'Failed to connect to Bybit'})
        
        # Start bot in separate thread
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        logger.info("Bot started via web dashboard")
        return jsonify({'success': True, 'message': 'Bot started successfully'})
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    global bot, bot_running, bot_status
    
    if not bot_running:
        return jsonify({'success': False, 'message': 'Bot is not running'})
    
    try:
        bot_running = False
        if bot:
            bot.running = False
        
        bot_status['running'] = False
        logger.info("Bot stopped via web dashboard")
        
        return jsonify({'success': True, 'message': 'Bot stopped successfully'})
        
    except Exception as e:
        logger.error(f"Failed to stop bot: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/close_position/<symbol>', methods=['POST'])
def close_position(symbol):
    """Close a specific position"""
    global bot
    
    if not bot_running or not bot:
        return jsonify({'success': False, 'message': 'Bot is not running'})
    
    try:
        result = bot.close_position(symbol)
        if result:
            return jsonify({'success': True, 'message': f'Closed position for {symbol}'})
        else:
            return jsonify({'success': False, 'message': 'Failed to close position'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/close_all', methods=['POST'])
def close_all_positions():
    """Close all open positions"""
    global bot
    
    if not bot_running or not bot:
        return jsonify({'success': False, 'message': 'Bot is not running'})
    
    try:
        closed = []
        failed = []
        
        for symbol in TRADING_PAIRS:
            try:
                if bot.close_position(symbol):
                    closed.append(symbol)
                else:
                    failed.append(symbol)
            except:
                failed.append(symbol)
        
        return jsonify({
            'success': True,
            'closed': closed,
            'failed': failed,
            'message': f'Closed {len(closed)} positions'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    print("=" * 60)
    print("TWIN RANGE FILTER BOT - WEB DASHBOARD")
    print("=" * 60)
    print("Access the dashboard from:")
    print("  Local:   http://localhost:5000")
    print("  Network: http://[YOUR_IP]:5000")
    print("")
    print("To access from Android phone:")
    print("  1. Connect phone to same WiFi network")
    print("  2. Find your computer's IP address")
    print("  3. Open browser and go to http://[YOUR_IP]:5000")
    print("=" * 60)
    
    # Run on all network interfaces so it's accessible from phone
    app.run(host='0.0.0.0', port=5000, debug=False)
