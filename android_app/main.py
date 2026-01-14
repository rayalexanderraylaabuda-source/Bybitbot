"""
Bybit Trading Bot - Android App
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty
import json
import os
import threading
import time
from datetime import datetime

# Import bot components
import sys
sys.path.append('..')
from bybit_client_lite import BybitClientLite
from supertrend_lite import calculate_supertrend


class TradingBotApp(App):
    status_text = StringProperty("Bot Stopped")
    is_running = BooleanProperty(False)
    
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        self.title = "Bybit Trading Bot"
        
        # Load config
        self.config_data = self.load_config()
        self.bot_thread = None
        self.bot_running = False
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Status bar
        self.status_label = Label(
            text=self.status_text,
            size_hint=(1, 0.05),
            color=(0, 1, 0, 1)
        )
        main_layout.add_widget(self.status_label)
        
        # Scrollable settings
        scroll = ScrollView(size_hint=(1, 0.85))
        settings_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        settings_layout.bind(minimum_height=settings_layout.setter('height'))
        
        # API Settings
        settings_layout.add_widget(self.create_section_label("API Settings"))
        
        self.api_key_input = self.create_text_input("API Key", self.config_data.get('api_key', ''))
        settings_layout.add_widget(self.api_key_input)
        
        self.api_secret_input = self.create_text_input("API Secret", self.config_data.get('api_secret', ''), password=True)
        settings_layout.add_widget(self.api_secret_input)
        
        # Testnet/Mainnet
        testnet_layout = BoxLayout(size_hint_y=None, height=40)
        testnet_layout.add_widget(Label(text="Use Testnet:", size_hint=(0.7, 1)))
        self.testnet_checkbox = CheckBox(active=self.config_data.get('testnet', False), size_hint=(0.3, 1))
        testnet_layout.add_widget(self.testnet_checkbox)
        settings_layout.add_widget(testnet_layout)
        
        # Trading Pairs
        settings_layout.add_widget(self.create_section_label("Trading Pairs"))
        
        pairs_available = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ZECUSDT", "FARTCOINUSDT"]
        self.pair_checkboxes = {}
        
        for pair in pairs_available:
            pair_layout = BoxLayout(size_hint_y=None, height=40)
            pair_layout.add_widget(Label(text=pair, size_hint=(0.7, 1)))
            checkbox = CheckBox(
                active=(pair in self.config_data.get('trading_pairs', [])),
                size_hint=(0.3, 1)
            )
            self.pair_checkboxes[pair] = checkbox
            pair_layout.add_widget(checkbox)
            settings_layout.add_widget(pair_layout)
        
        # Risk Management
        settings_layout.add_widget(self.create_section_label("Risk Management"))
        
        self.position_size_input = self.create_number_input(
            "Position Size %",
            str(self.config_data.get('position_size_percent', 35))
        )
        settings_layout.add_widget(self.position_size_input)
        
        self.stop_loss_input = self.create_number_input(
            "Stop Loss %",
            str(self.config_data.get('stop_loss_percent', 42))
        )
        settings_layout.add_widget(self.stop_loss_input)
        
        self.take_profit_input = self.create_number_input(
            "Take Profit %",
            str(self.config_data.get('take_profit_percent', 150))
        )
        settings_layout.add_widget(self.take_profit_input)
        
        # Leverage Settings
        settings_layout.add_widget(self.create_section_label("Leverage Settings"))
        
        self.leverage_inputs = {}
        for pair in pairs_available:
            lev = self.config_data.get('leverage', {}).get(pair, 25)
            self.leverage_inputs[pair] = self.create_number_input(f"{pair} Leverage", str(lev))
            settings_layout.add_widget(self.leverage_inputs[pair])
        
        # Timeframe
        settings_layout.add_widget(self.create_section_label("Strategy Settings"))
        
        timeframe_layout = BoxLayout(size_hint_y=None, height=40)
        timeframe_layout.add_widget(Label(text="Timeframe:", size_hint=(0.5, 1)))
        self.timeframe_spinner = Spinner(
            text=self.config_data.get('timeframe', '5'),
            values=['1', '3', '5', '15', '30', '60', '120', '240'],
            size_hint=(0.5, 1)
        )
        timeframe_layout.add_widget(self.timeframe_spinner)
        settings_layout.add_widget(timeframe_layout)
        
        scroll.add_widget(settings_layout)
        main_layout.add_widget(scroll)
        
        # Control buttons
        button_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        
        self.start_button = Button(
            text="Start Bot",
            background_color=(0, 1, 0, 1),
            on_press=self.start_bot
        )
        button_layout.add_widget(self.start_button)
        
        self.stop_button = Button(
            text="Stop Bot",
            background_color=(1, 0, 0, 1),
            on_press=self.stop_bot,
            disabled=True
        )
        button_layout.add_widget(self.stop_button)
        
        save_button = Button(
            text="Save Config",
            background_color=(0, 0.5, 1, 1),
            on_press=self.save_config
        )
        button_layout.add_widget(save_button)
        
        main_layout.add_widget(button_layout)
        
        return main_layout
    
    def create_section_label(self, text):
        label = Label(
            text=f"\n{text}",
            size_hint_y=None,
            height=40,
            color=(1, 1, 0, 1),
            bold=True
        )
        return label
    
    def create_text_input(self, hint, text, password=False):
        layout = BoxLayout(size_hint_y=None, height=40)
        layout.add_widget(Label(text=hint + ":", size_hint=(0.4, 1)))
        text_input = TextInput(
            text=text,
            multiline=False,
            password=password,
            size_hint=(0.6, 1)
        )
        layout.add_widget(text_input)
        return layout
    
    def create_number_input(self, hint, text):
        layout = BoxLayout(size_hint_y=None, height=40)
        layout.add_widget(Label(text=hint + ":", size_hint=(0.5, 1)))
        text_input = TextInput(
            text=text,
            multiline=False,
            input_filter='float',
            size_hint=(0.5, 1)
        )
        layout.add_widget(text_input)
        return layout
    
    def load_config(self):
        config_file = 'bot_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        
        return {
            'api_key': '',
            'api_secret': '',
            'testnet': False,
            'trading_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
            'leverage': {
                'BTCUSDT': 30,
                'ETHUSDT': 30,
                'SOLUSDT': 30,
                'XRPUSDT': 30,
                'DOGEUSDT': 30,
                'ZECUSDT': 30,
                'FARTCOINUSDT': 30
            },
            'position_size_percent': 35,
            'timeframe': '60',
            'stop_loss_percent': 100,
            'take_profit_percent': 150,
            'enable_stop_loss': True,
            'enable_take_profit': True,
            'atr_period': 10,
            'supertrend_factor': 3.0,
            'check_interval': 60
        }
    
    def save_config(self, instance):
        # Get selected pairs
        selected_pairs = [pair for pair, checkbox in self.pair_checkboxes.items() if checkbox.active]
        
        if not selected_pairs:
            self.show_popup("Error", "Please select at least one trading pair!")
            return
        
        # Get leverage for each pair
        leverage = {}
        for pair, input_layout in self.leverage_inputs.items():
            text_input = input_layout.children[0]
            leverage[pair] = int(float(text_input.text or 25))
        
        # Build config
        config = {
            'api_key': self.api_key_input.children[0].text,
            'api_secret': self.api_secret_input.children[0].text,
            'testnet': self.testnet_checkbox.active,
            'trading_pairs': selected_pairs,
            'leverage': leverage,
            'position_size_percent': float(self.position_size_input.children[0].text or 35),
            'timeframe': self.timeframe_spinner.text,
            'stop_loss_percent': float(self.stop_loss_input.children[0].text or 42),
            'take_profit_percent': float(self.take_profit_input.children[0].text or 150),
            'enable_stop_loss': True,
            'enable_take_profit': True,
            'atr_period': 10,
            'supertrend_factor': 3.0,
            'check_interval': 60
        }
        
        # Validate
        if not config['api_key'] or not config['api_secret']:
            self.show_popup("Error", "Please enter API Key and Secret!")
            return
        
        # Save to file
        with open('bot_config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        self.config_data = config
        self.show_popup("Success", "Configuration saved!")
    
    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
    
    def start_bot(self, instance):
        if not self.config_data.get('api_key') or not self.config_data.get('api_secret'):
            self.show_popup("Error", "Please save configuration first!")
            return
        
        self.bot_running = True
        self.is_running = True
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.status_text = "Bot Running..."
        
        # Start bot in thread
        self.bot_thread = threading.Thread(target=self.run_bot)
        self.bot_thread.daemon = True
        self.bot_thread.start()
    
    def stop_bot(self, instance):
        self.bot_running = False
        self.is_running = False
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.status_text = "Bot Stopped"
    
    def run_bot(self):
        try:
            client = BybitClientLite(
                api_key=self.config_data['api_key'],
                api_secret=self.config_data['api_secret'],
                testnet=self.config_data['testnet']
            )
            
            # Set position mode
            client.set_position_mode(0)
            
            # Set leverage
            for symbol in self.config_data['trading_pairs']:
                lev = self.config_data['leverage'].get(symbol, 25)
                client.set_leverage(symbol, lev)
            
            last_signals = {pair: 'none' for pair in self.config_data['trading_pairs']}
            
            while self.bot_running:
                try:
                    Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"Checking signals... {datetime.now().strftime('%H:%M:%S')}"))
                    
                    for symbol in self.config_data['trading_pairs']:
                        # Get candles
                        candles = client.get_klines(symbol, self.config_data['timeframe'], limit=200)
                        
                        if not candles:
                            continue
                        
                        # Calculate Supertrend signals
                        result = calculate_supertrend(
                            candles,
                            atr_period=self.config_data.get('atr_period', 10),
                            factor=self.config_data.get('supertrend_factor', 3.0)
                        )
                        
                        # Determine signal
                        if result['long_signal']:
                            signal = 'long'
                        elif result['short_signal']:
                            signal = 'short'
                        else:
                            signal = 'none'
                        
                        # Execute trade if signal changed
                        if signal != 'none' and signal != last_signals[symbol]:
                            last_signals[symbol] = signal
                            
                            # Get wallet and calculate position size
                            balance = client.get_wallet_balance()
                            wallet = 0.0
                            for coin in balance.get('list', [{}])[0].get('coin', []):
                                if coin.get('coin') == 'USDT':
                                    wallet = float(coin.get('walletBalance', 0))
                            
                            usd = wallet * (self.config_data['position_size_percent'] / 100)
                            lev = client.get_max_leverage(symbol)
                            
                            # Set leverage
                            client.set_leverage(symbol, lev)
                            
                            qty = client.calculate_qty(symbol, usd, lev)
                            
                            if qty > 0:
                                # Close opposite position
                                pos = client.get_position(symbol)
                                if pos:
                                    client.close_position(symbol)
                                    time.sleep(1)
                                
                                # Get entry price for SL/TP
                                ticker = client.get_ticker(symbol)
                                entry_price = float(ticker.get('lastPrice', 0))
                                
                                stop_loss = None
                                take_profit = None
                                
                                if signal == 'long':
                                    # For LONG: SL below, TP above (ROI-based)
                                    stop_loss = entry_price * (1 - (self.config_data['stop_loss_percent'] / lev) / 100)
                                    take_profit = entry_price * (1 + (self.config_data['take_profit_percent'] / lev) / 100)
                                    side = 'Buy'
                                    emoji = '🟢'
                                else:
                                    # For SHORT: SL above, TP below (ROI-based)
                                    stop_loss = entry_price * (1 + (self.config_data['stop_loss_percent'] / lev) / 100)
                                    take_profit = entry_price * (1 - (self.config_data['take_profit_percent'] / lev) / 100)
                                    side = 'Sell'
                                    emoji = '🔴'
                                
                                # Place order
                                client.place_order(symbol, side, qty, stop_loss=stop_loss, take_profit=take_profit)
                                
                                Clock.schedule_once(
                                    lambda dt: setattr(self, 'status_text', f"{emoji} {side} {symbol} ${usd:.2f}")
                                )
                    
                    time.sleep(self.config_data.get('check_interval', 60))
                    
                except Exception as e:
                    Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"Error: {str(e)}"))
                    time.sleep(5)
        
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("Error", str(e)))
            self.stop_bot(None)


if __name__ == '__main__':
    TradingBotApp().run()
