"""
Binance Data Feed Implementation

Fetches historical market data from Binance public API.
Handles rate limiting, error retry, and data formatting for backtesting.
"""

import time
import requests
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import logging

from .base_feed import BaseDataFeed
from ..models import MarketSnapshot


logger = logging.getLogger(__name__)


class BinanceDataFeed(BaseDataFeed):
    """
    Binance API data feed implementation.
    
    Fetches historical OHLCV data from Binance's public REST API
    with proper rate limiting and error handling.
    """
    
    BASE_URL = "https://api.binance.com"
    
    # Binance API intervals mapping
    INTERVAL_MAP = {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
        '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
    }
    
    def __init__(self, cache_enabled: bool = True, cache_path: str = "./data_cache"):
        """
        Initialize Binance data feed.
        
        Args:
            cache_enabled (bool): Whether to enable data caching
            cache_path (str): Path to store cached data files
        """
        super().__init__(cache_enabled, cache_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TradingBot/1.0'
        })
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self) -> None:
        """Implement basic rate limiting to avoid API limits."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated request to Binance API with error handling.
        
        Args:
            endpoint (str): API endpoint
            params (Dict[str, Any]): Request parameters
            
        Returns:
            Dict[str, Any]: API response data
            
        Raises:
            Exception: If API request fails after retries
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to fetch data from Binance after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List[MarketSnapshot]:
        """
        Fetch historical OHLCV data from Binance API.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            timeframe (str): Timeframe for candles (e.g., '1h', '4h', '1d')
            start_time (datetime): Start time for data fetch
            end_time (datetime): End time for data fetch
            limit (Optional[int]): Maximum number of candles to fetch (max 1000)
            
        Returns:
            List[MarketSnapshot]: List of market data snapshots
        """
        # Check cache first
        cache_key = self._generate_cache_key(symbol, timeframe, start_time, end_time)
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Using cached data for {symbol} {timeframe}")
            return cached_data
        
        # Validate timeframe
        if timeframe not in self.INTERVAL_MAP:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(self.INTERVAL_MAP.keys())}")
        
        # Convert to milliseconds (Binance API requirement)
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        # Prepare API parameters
        params = {
            'symbol': symbol.upper(),
            'interval': self.INTERVAL_MAP[timeframe],
            'startTime': start_ms,
            'endTime': end_ms
        }
        
        if limit:
            params['limit'] = min(limit, 1000)  # Binance max limit is 1000
        
        logger.info(f"Fetching {symbol} {timeframe} data from {start_time} to {end_time}")
        
        try:
            # Fetch data from API
            data = self._make_request('/api/v3/klines', params)
            
            # Convert to MarketSnapshot objects
            snapshots = []
            for kline in data:
                timestamp = datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc)
                
                snapshot = MarketSnapshot(
                    timestamp=timestamp,
                    symbol=symbol.upper(),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                    timeframe=timeframe
                )
                snapshots.append(snapshot)
            
            # Cache the data
            self._cache_data(cache_key, snapshots)
            
            logger.info(f"Successfully fetched {len(snapshots)} candles for {symbol}")
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading information for a symbol from Binance.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Symbol information including filters and precision
        """
        try:
            # Get exchange info
            exchange_info = self._make_request('/api/v3/exchangeInfo', {})
            
            # Find symbol information
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol.upper():
                    return {
                        'symbol': symbol_info['symbol'],
                        'status': symbol_info['status'],
                        'baseAsset': symbol_info['baseAsset'],
                        'quoteAsset': symbol_info['quoteAsset'],
                        'baseAssetPrecision': symbol_info['baseAssetPrecision'],
                        'quoteAssetPrecision': symbol_info['quoteAssetPrecision'],
                        'filters': symbol_info['filters']
                    }
            
            raise ValueError(f"Symbol {symbol} not found")
            
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            raise
    
    def get_available_symbols(self) -> List[str]:
        """
        Get list of available trading symbols from Binance.
        
        Returns:
            List[str]: List of available symbols
        """
        try:
            exchange_info = self._make_request('/api/v3/exchangeInfo', {})
            
            symbols = []
            for symbol_info in exchange_info['symbols']:
                if symbol_info['status'] == 'TRADING':
                    symbols.append(symbol_info['symbol'])
            
            return sorted(symbols)
            
        except Exception as e:
            logger.error(f"Failed to get available symbols: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            float: Current price
        """
        try:
            ticker = self._make_request('/api/v3/ticker/price', {'symbol': symbol.upper()})
            return float(ticker['price'])
            
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            raise
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book depth for a symbol.
        
        Args:
            symbol (str): Trading symbol
            limit (int): Number of entries to return (max 5000)
            
        Returns:
            Dict[str, Any]: Order book data with bids and asks
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'limit': min(limit, 5000)
            }
            
            order_book = self._make_request('/api/v3/depth', params)
            
            return {
                'symbol': symbol.upper(),
                'bids': [[float(price), float(qty)] for price, qty in order_book['bids']],
                'asks': [[float(price), float(qty)] for price, qty in order_book['asks']],
                'lastUpdateId': order_book['lastUpdateId']
            }
            
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            raise