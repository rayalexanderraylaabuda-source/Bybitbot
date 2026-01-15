"""
Bybit API Client for Trading Operations
Supports USDT Perpetual futures trading
"""

import time
import hmac
import hashlib
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import urllib3

# Lightweight pandas-free DataFrame for Termux compatibility
try:
    import pandas as pd
except ImportError:
    class DataFrame:
        def __init__(self, data=None, columns=None):
            self.columns = columns or []
            self.data = data or []
            self.index = list(range(len(self.data))) if self.data else []
        
        def empty(self):
            return len(self.data) == 0
        
        def astype(self, dtype_dict):
            for col_name, col_type in dtype_dict.items():
                if col_name in self.columns:
                    idx = self.columns.index(col_name)
                    for row in self.data:
                        try:
                            row[idx] = col_type(row[idx])
                        except:
                            pass
            return self
        
        def sort_values(self, by, ascending=True):
            if isinstance(by, str):
                idx = self.columns.index(by)
                self.data.sort(key=lambda x: x[idx], reverse=not ascending)
            return self
        
        def reset_index(self, drop=False):
            return self
        
        def __getitem__(self, key):
            return self.data[key] if isinstance(key, int) else [row[self.columns.index(key)] for row in self.data]
    
    class pd:
        DataFrame = DataFrame
        @staticmethod
        def to_datetime(series, unit=None):
            if unit == 'ms':
                from datetime import datetime
                return [datetime.fromtimestamp(int(x)/1000) for x in series]
            return series

# Disable SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BybitClient:
    """Bybit API Client for derivatives trading"""
    
    MAINNET_URL = "https://api.bybit.com"
    TESTNET_URL = "https://api-testnet.bybit.com"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize Bybit client
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Use testnet if True, mainnet if False
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = self.TESTNET_URL if testnet else self.MAINNET_URL
        self.recv_window = 60000  # Increased to 60 seconds to handle clock skew and network delays
        
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC signature for request"""
        param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    def _request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """
        Make API request
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs authentication
        
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if signed:
            params['api_key'] = self.api_key
            params['timestamp'] = self._get_timestamp()
            params['recv_window'] = self.recv_window
            params['sign'] = self._generate_signature(params)
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=10, verify=False)
            else:
                response = requests.post(url, json=params, timeout=10, verify=False)
            
            data = response.json()
            
            if data.get('retCode') != 0 and data.get('retCode') != 110043:
                logger.error(f"API Error: {data.get('retMsg')} (Code: {data.get('retCode')})")
            
            return data
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {'retCode': -1, 'retMsg': str(e)}
    
    def _request_v5(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """
        Make V5 API request with proper authentication
        """
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        headers = {}
        
        if signed:
            timestamp = str(self._get_timestamp())
            
            if method == 'GET':
                param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
                sign_str = f"{timestamp}{self.api_key}{self.recv_window}{param_str}"
            else:
                import json
                param_str = json.dumps(params)
                sign_str = f"{timestamp}{self.api_key}{self.recv_window}{param_str}"
            
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                sign_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'X-BAPI-API-KEY': self.api_key,
                'X-BAPI-TIMESTAMP': timestamp,
                'X-BAPI-SIGN': signature,
                'X-BAPI-RECV-WINDOW': str(self.recv_window),
                'Content-Type': 'application/json'
            }
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
            else:
                response = requests.post(url, json=params, headers=headers, timeout=10, verify=False)
            
            data = response.json()
            
            if data.get('retCode') != 0 and data.get('retCode') != 110043:
                logger.error(f"API Error: {data.get('retMsg')} (Code: {data.get('retCode')})")
            
            return data
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {'retCode': -1, 'retMsg': str(e)}
    
    def get_klines(self, symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
        """
        Get candlestick/kline data
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Timeframe (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            limit: Number of candles to fetch (max 200)
        
        Returns:
            DataFrame with OHLCV data
        """
        endpoint = "/v5/market/kline"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = self._request_v5('GET', endpoint, params)
        
        if response.get('retCode') != 0:
            logger.error(f"Failed to get klines: {response.get('retMsg')}")
            return pd.DataFrame()
        
        data = response.get('result', {}).get('list', [])
        
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        df = df.astype({
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': float,
            'turnover': float
        })
        
        # Sort by timestamp ascending
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def get_position(self, symbol: str) -> Dict:
        """
        Get current position for a symbol
        
        Args:
            symbol: Trading pair
        
        Returns:
            Position data dictionary
        """
        endpoint = "/v5/position/list"
        params = {
            'category': 'linear',
            'symbol': symbol
        }
        
        response = self._request_v5('GET', endpoint, params, signed=True)
        
        if response.get('retCode') != 0:
            return {}
        
        positions = response.get('result', {}).get('list', [])
        return positions[0] if positions else {}
    
    def get_all_positions(self) -> List[Dict]:
        """Get all open positions"""
        endpoint = "/v5/position/list"
        params = {
            'category': 'linear',
            'settleCoin': 'USDT'
        }
        
        response = self._request_v5('GET', endpoint, params, signed=True)
        
        if response.get('retCode') != 0:
            return []
        
        return response.get('result', {}).get('list', [])
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol with automatic fallback
        
        Args:
            symbol: Trading pair
            leverage: Leverage value
        
        Returns:
            True if successful
        """
        max_attempts = 5
        current_leverage = leverage
        
        for attempt in range(max_attempts):
            endpoint = "/v5/position/set-leverage"
            params = {
                'category': 'linear',
                'symbol': symbol,
                'buyLeverage': str(current_leverage),
                'sellLeverage': str(current_leverage)
            }
            
            response = self._request_v5('POST', endpoint, params, signed=True)
            
            if response.get('retCode') == 0:
                logger.info(f"✅ Leverage set to {current_leverage}x for {symbol}")
                return True
            elif response.get('retCode') == 110043:
                # 110043 = leverage not modified (already set to this value)
                logger.debug(f"Leverage already set for {symbol}")
                return True
            elif response.get('retCode') == 110012:  # Not enough for new leverage
                if current_leverage > 1:
                    current_leverage = max(1, current_leverage // 2)
                    logger.warning(f"⚠️ Insufficient margin for {leverage}x leverage on {symbol}, trying {current_leverage}x")
                    continue
                else:
                    logger.error(f"❌ Failed to set leverage: Even 1x leverage not supported for {symbol}")
                    return False
            else:
                logger.error(f"❌ Failed to set leverage: {response.get('retMsg')} (Code: {response.get('retCode')})")
                return False
        
        logger.error(f"❌ Failed to set leverage after {max_attempts} attempts for {symbol}")
        return False
    
    def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str = 'Market',
        reduce_only: bool = False,
        stop_loss: float = None,
        take_profit: float = None
    ) -> Dict:
        """
        Place an order
        
        Args:
            symbol: Trading pair
            side: 'Buy' or 'Sell'
            qty: Order quantity
            order_type: 'Market' or 'Limit'
            reduce_only: If True, only reduces position
            stop_loss: Stop loss price
            take_profit: Take profit price
        
        Returns:
            Order response
        """
        endpoint = "/v5/order/create"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'side': side,
            'orderType': order_type,
            'qty': str(qty),
            'timeInForce': 'GTC',
            'positionIdx': 0,  # 0 = One-Way Mode
            'reduceOnly': reduce_only
        }
        
        # NOTE: Do NOT add stopLoss/takeProfit here for market orders
        # Bybit doesn't support SL/TP in market order creation
        # We'll set them separately using set_trading_stop
        
        response = self._request_v5('POST', endpoint, params, signed=True)
        
        if response.get('retCode') == 0:
            logger.info(f"✅ Order placed: {side} {qty} {symbol}")
            
            # Now set SL/TP using trading-stop endpoint
            if stop_loss or take_profit:
                time.sleep(1)  # Small delay to ensure position is open
                self.set_trading_stop(symbol, stop_loss, take_profit)
        else:
            logger.error(f"❌ Order failed: {response.get('retMsg')}")
        
        return response
    
    def set_trading_stop(self, symbol: str, stop_loss: float = None, take_profit: float = None) -> bool:
        """Set stop loss and take profit for an open position"""
        if not stop_loss and not take_profit:
            logger.debug("No SL/TP to set")
            return True
        
        endpoint = "/v5/position/trading-stop"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'positionIdx': 0
        }
        
        if stop_loss:
            params['stopLoss'] = str(round(stop_loss, 4))
            logger.info(f"  ⛔ SL set: ${stop_loss:.4f}")
        
        if take_profit:
            params['takeProfit'] = str(round(take_profit, 4))
            logger.info(f"  🎯 TP set: ${take_profit:.4f}")
        
        response = self._request_v5('POST', endpoint, params, signed=True)
        
        if response.get('retCode') == 0:
            logger.info(f"✅ SL/TP configured successfully for {symbol}")
            return True
        elif response.get('retCode') == 110001:  # Position not exist
            logger.warning(f"⚠️ Position not yet available, retrying in 2 seconds...")
            time.sleep(2)
            return self.set_trading_stop(symbol, stop_loss, take_profit)
        else:
            logger.error(f"❌ Failed to set SL/TP: {response.get('retMsg')} (Code: {response.get('retCode')})")
            return False
    
    def close_position(self, symbol: str) -> Dict:
        """
        Close entire position for a symbol
        
        Args:
            symbol: Trading pair
        
        Returns:
            Order response
        """
        position = self.get_position(symbol)
        
        if not position:
            logger.info(f"No position to close for {symbol}")
            return {'retCode': 0, 'retMsg': 'No position'}
        
        size = float(position.get('size', 0))
        side = position.get('side', '')
        
        if size == 0:
            logger.info(f"No position to close for {symbol}")
            return {'retCode': 0, 'retMsg': 'No position'}
        
        # Close by placing opposite order
        close_side = 'Sell' if side == 'Buy' else 'Buy'
        
        return self.place_order(
            symbol=symbol,
            side=close_side,
            qty=size,
            reduce_only=True
        )
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker/price for a symbol"""
        endpoint = "/v5/market/tickers"
        params = {
            'category': 'linear',
            'symbol': symbol
        }
        
        response = self._request_v5('GET', endpoint, params)
        
        if response.get('retCode') != 0:
            return {}
        
        tickers = response.get('result', {}).get('list', [])
        return tickers[0] if tickers else {}
    
    def get_instrument_info(self, symbol: str) -> Dict:
        """Get trading instrument info (min qty, tick size, etc.)"""
        endpoint = "/v5/market/instruments-info"
        params = {
            'category': 'linear',
            'symbol': symbol
        }
        
        response = self._request_v5('GET', endpoint, params)
        
        if response.get('retCode') != 0:
            return {}
        
        instruments = response.get('result', {}).get('list', [])
        return instruments[0] if instruments else {}
    
    def get_max_leverage(self, symbol: str) -> int:
        """Get maximum leverage for a symbol"""
        instrument = self.get_instrument_info(symbol)
        if not instrument:
            return 10  # Default fallback
        
        leverage_filter = instrument.get('leverageFilter', {})
        max_leverage = leverage_filter.get('maxLeverage', '10')
        return int(float(max_leverage))
    
    def calculate_qty(self, symbol: str, usd_amount: float, leverage: int = 1) -> float:
        """
        Calculate order quantity from USD amount
        
        Args:
            symbol: Trading pair
            usd_amount: Amount in USD
            leverage: Leverage to use
        
        Returns:
            Quantity to order
        """
        ticker = self.get_ticker(symbol)
        instrument = self.get_instrument_info(symbol)
        
        if not ticker or not instrument:
            return 0
        
        price = float(ticker.get('lastPrice', 0))
        
        if price == 0:
            return 0
        
        # Get lot size filter
        lot_size = instrument.get('lotSizeFilter', {})
        min_qty = float(lot_size.get('minOrderQty', 0.001))
        qty_step = float(lot_size.get('qtyStep', 0.001))
        
        # Calculate raw quantity
        raw_qty = (usd_amount * leverage) / price
        
        # Round to qty step
        qty = round(raw_qty / qty_step) * qty_step
        
        # Ensure minimum
        qty = max(qty, min_qty)
        
        # Format to proper decimal places
        decimals = len(str(qty_step).split('.')[-1]) if '.' in str(qty_step) else 0
        qty = round(qty, decimals)
        
        return qty
    
    def get_wallet_balance(self) -> Dict:
        """Get wallet balance"""
        endpoint = "/v5/account/wallet-balance"
        params = {
            'accountType': 'UNIFIED'
        }
        
        response = self._request_v5('GET', endpoint, params, signed=True)
        
        if response.get('retCode') != 0:
            return {}
        
        return response.get('result', {})
