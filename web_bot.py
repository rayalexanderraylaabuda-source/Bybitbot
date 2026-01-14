"""
Bybit Trading Bot - Simple Web Interface
Run this on your Android phone via Termux, then access via browser!
"""
from flask import Flask, render_template, request, jsonify
import json
import os
import threading
import time
from datetime import datetime

from bybit_client_lite import BybitClientLite
from supertrend_lite import calculate_supertrend

app = Flask(__name__)

# Global bot state
bot_config = {}
bot_running = False
bot_thread = None
bot_status = "Stopped"
bot_positions = []
bot_wallet = 0.0


def load_config():
    """Load configuration"""
    if os.path.exists('web_config.json'):
        with open('web_config.json', 'r') as f:
            return json.load(f)
    
    return {
        'api_key': '',
        'api_secret': '',
        'testnet': False,
        'trading_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        'leverage': {
            'BTCUSDT': 100,
            'ETHUSDT': 100,
            'SOLUSDT': 100,
            'XRPUSDT': 50,
            'DOGEUSDT': 50,
            'ZECUSDT': 25,
            'FARTCOINUSDT': 25
        },
        'position_size_percent': 35,
        'timeframe': '5',
        'stop_loss_percent': 42,
        'take_profit_percent': 150,
        'atr_period': 5,
        'supertrend_factor': 3.0,
        'check_interval': 60
    }


def save_config(config):
    """Save configuration"""
    with open('web_config.json', 'w') as f:
        json.dump(config, f, indent=4)


def run_trading_bot():
    """Main bot loop"""
    global bot_running, bot_status, bot_positions, bot_wallet, bot_config
    
    try:
        client = BybitClientLite(
            api_key=bot_config['api_key'],
            api_secret=bot_config['api_secret'],
            testnet=bot_config['testnet']
        )
        
        # Set position mode
        client.set_position_mode(0)
        
        # Set leverage to maximum for each symbol
        for symbol in bot_config['trading_pairs']:
            max_lev = client.get_max_leverage(symbol)
            client.set_leverage(symbol, max_lev)
        
        last_signals = {pair: 'none' for pair in bot_config['trading_pairs']}
        
        while bot_running:
            try:
                bot_status = f"Checking signals... {datetime.now().strftime('%H:%M:%S')}"
                
                # Update wallet
                balance = client.get_wallet_balance()
                for coin in balance.get('list', [{}])[0].get('coin', []):
                    if coin.get('coin') == 'USDT':
                        bot_wallet = float(coin.get('walletBalance', 0))
                
                # Check each pair
                for symbol in bot_config['trading_pairs']:
                    candles = client.get_klines(symbol, bot_config['timeframe'], limit=200)
                    
                    if not candles:
                        continue
                    
                    result = calculate_supertrend(
                        candles,
                        atr_period=bot_config.get('atr_period', 10),
                        factor=bot_config.get('supertrend_factor', 3.0)
                    )
                    
                    # Determine signal
                    if result['long_signal']:
                        signal = 'long'
                    elif result['short_signal']:
                        signal = 'short'
                    else:
                        signal = 'none'
                    
                    # Execute if signal changed
                    if signal != 'none' and signal != last_signals[symbol]:
                        last_signals[symbol] = signal
                        
                        usd = bot_wallet * (bot_config['position_size_percent'] / 100)
                        lev = client.get_max_leverage(symbol)
                        qty = client.calculate_qty(symbol, usd, lev)
                        
                        if qty > 0:
                            # Close opposite position
                            client.close_position(symbol)
                            time.sleep(1)
                            
                            # Get entry price
                            ticker = client.get_ticker(symbol)
                            entry_price = float(ticker.get('lastPrice', 0))
                            
                            # Calculate SL/TP with correct ROI-based formulas
                            if signal == 'long':
                                # For LONG: SL below, TP above
                                stop_loss = entry_price * (1 - (bot_config['stop_loss_percent'] / lev) / 100)
                                take_profit = entry_price * (1 + (bot_config['take_profit_percent'] / lev) / 100)
                                side = 'Buy'
                            else:
                                # For SHORT: SL above, TP below
                                stop_loss = entry_price * (1 + (bot_config['stop_loss_percent'] / lev) / 100)
                                take_profit = entry_price * (1 - (bot_config['take_profit_percent'] / lev) / 100)
                                side = 'Sell'
                            
                            # Place order
                            client.place_order(symbol, side, qty, stop_loss=stop_loss, take_profit=take_profit)
                            bot_status = f"{'🟢' if side == 'Buy' else '🔴'} {side} {symbol} ${usd:.2f}"
                
                # Update positions
                bot_positions = []
                for symbol in bot_config['trading_pairs']:
                    pos = client.get_position(symbol)
                    if pos and float(pos.get('size', 0)) > 0:
                        bot_positions.append({
                            'symbol': symbol,
                            'side': pos.get('side'),
                            'size': float(pos.get('size', 0)),
                            'entry': float(pos.get('avgPrice', 0)),
                            'pnl': float(pos.get('unrealisedPnl', 0))
                        })
                
                time.sleep(bot_config['check_interval'])
            
            except Exception as e:
                bot_status = f"Error: {str(e)}"
                time.sleep(5)
    
    except Exception as e:
        bot_status = f"Fatal Error: {str(e)}"
        bot_running = False


@app.route('/')
def index():
    """Main page"""
    return render_template('bot_settings.html')


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or update configuration"""
    global bot_config
    
    if request.method == 'GET':
        bot_config = load_config()
        return jsonify(bot_config)
    
    elif request.method == 'POST':
        bot_config = request.json
        save_config(bot_config)
        return jsonify({'success': True})


@app.route('/api/status')
def status():
    """Get bot status"""
    return jsonify({
        'running': bot_running,
        'status': bot_status,
        'wallet': bot_wallet,
        'positions': bot_positions
    })


@app.route('/api/start', methods=['POST'])
def start():
    """Start bot"""
    global bot_running, bot_thread, bot_config
    
    bot_config = load_config()
    
    if not bot_config.get('api_key') or not bot_config.get('api_secret'):
        return jsonify({'success': False, 'error': 'API keys not configured'})
    
    if bot_running:
        return jsonify({'success': False, 'error': 'Bot already running'})
    
    bot_running = True
    bot_thread = threading.Thread(target=run_trading_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    return jsonify({'success': True})


@app.route('/api/stop', methods=['POST'])
def stop():
    """Stop bot"""
    global bot_running
    bot_running = False
    return jsonify({'success': True})


if __name__ == '__main__':
    # Run on all interfaces so accessible from phone browser
    print("\n" + "="*50)
    print("🚀 Bybit Trading Bot Web Interface")
    print("="*50)
    print("\nAccess from:")
    print("- On phone: http://localhost:5000")
    print("- From other device: http://YOUR_PHONE_IP:5000")
    print("\n" + "="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
