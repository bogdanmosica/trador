"""
Binance REST API Provider

Implementation of MarketDataProvider for Binance exchange using REST API.
Provides historical candle data, ticker information, order book snapshots,
and recent trades with proper rate limiting and error handling.
"""

import asyncio
import aiohttp
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

from .base import MarketDataProvider, DataProviderError, RateLimitError, SymbolNotFoundError
from ..models import Candle, Ticker, OrderBook, OrderBookLevel, Trade, MarketDataConfig


logger = logging.getLogger(__name__)


class BinanceRESTProvider(MarketDataProvider):
    """
    Binance REST API market data provider.
    
    Implements the MarketDataProvider interface for Binance exchange
    with proper rate limiting, error handling, and data normalization.
    """
    
    # Binance API endpoints
    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"
    
    # API endpoints
    ENDPOINTS = {
        'klines': '/api/v3/klines',
        'ticker_24hr': '/api/v3/ticker/24hr',
        'ticker_price': '/api/v3/ticker/price',
        'depth': '/api/v3/depth',
        'trades': '/api/v3/trades',
        'exchange_info': '/api/v3/exchangeInfo',
        'ping': '/api/v3/ping',
        'time': '/api/v3/time'
    }
    
    # Interval mapping from common formats to Binance format
    INTERVAL_MAP = {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
        '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
    }
    
    def __init__(self, config: Optional[MarketDataConfig] = None):
        """
        Initialize Binance REST provider.
        
        Args:
            config (Optional[MarketDataConfig]): Provider configuration
        """
        if config is None:
            config = MarketDataConfig(
                base_url=self.BASE_URL,
                requests_per_minute=1200,
                timeout_seconds=10
            )
        
        super().__init__(config)
        
        self.base_url = self.TESTNET_URL if config.testnet else self.BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
        self._request_count = 0
        self._request_window_start = time.time()
        
        # Cache for exchange info
        self._exchange_info: Optional[Dict] = None
        self._symbols_cache: Optional[List[str]] = None
        self._symbol_info_cache: Dict[str, Dict] = {}
    
    async def connect(self):
        """Initialize HTTP session and load exchange info."""
        await super().connect()
        
        # Create HTTP session with custom settings
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'TradingBot-MarketData/1.0',
                'Content-Type': 'application/json'
            }
        )
        
        # Load exchange info for symbol validation
        try:
            await self._load_exchange_info()
            self.logger.info("Successfully connected to Binance API")
        except Exception as e:
            self.logger.error(f"Failed to load exchange info: {e}")
            raise DataProviderError(f"Failed to initialize Binance provider: {e}")
    
    async def disconnect(self):
        """Clean up HTTP session."""
        await super().disconnect()
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make rate-limited HTTP request to Binance API.
        
        Args:
            endpoint (str): API endpoint
            params (Optional[Dict[str, Any]]): Request parameters
            
        Returns:
            Dict[str, Any]: API response data
            
        Raises:
            RateLimitError: If rate limits are exceeded
            DataProviderError: For other API errors
        """
        if not self._session:
            await self.connect()
        
        # Rate limiting
        await self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                async with self._session.get(url, params=params) as response:
                    self._update_rate_limit_counters()
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        # Rate limit exceeded
                        retry_after = int(response.headers.get('Retry-After', 60))
                        raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
                    elif response.status == 400:
                        error_data = await response.json()
                        error_msg = error_data.get('msg', 'Bad request')
                        if 'Invalid symbol' in error_msg:
                            raise SymbolNotFoundError(f"Invalid symbol: {error_msg}")
                        raise DataProviderError(f"Bad request: {error_msg}")
                    else:
                        response.raise_for_status()
                        
            except aiohttp.ClientError as e:
                if attempt == self.config.max_retries - 1:
                    raise DataProviderError(f"HTTP request failed: {e}")
                
                # Exponential backoff
                delay = self.config.retry_delay * (self.config.backoff_factor ** attempt)
                await asyncio.sleep(delay)
                
        raise DataProviderError("Max retries exceeded")
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        
        # Reset window if more than 1 minute has passed
        if current_time - self._request_window_start >= 60:
            self._request_count = 0
            self._request_window_start = current_time
        
        # Check if we're within rate limits
        if self._request_count >= self.config.requests_per_minute:
            sleep_time = 60 - (current_time - self._request_window_start)
            if sleep_time > 0:
                self.logger.warning(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._request_window_start = time.time()
        
        # Minimum delay between requests
        time_since_last = current_time - self._last_request_time
        min_delay = 60.0 / self.config.requests_per_minute
        
        if time_since_last < min_delay:
            await asyncio.sleep(min_delay - time_since_last)
    
    def _update_rate_limit_counters(self):
        """Update rate limiting counters."""
        self._last_request_time = time.time()
        self._request_count += 1
    
    async def _load_exchange_info(self):
        """Load and cache exchange information."""
        try:
            self._exchange_info = await self._make_request(self.ENDPOINTS['exchange_info'])
            
            # Cache symbols list
            symbols_data = self._exchange_info.get('symbols', [])
            self._symbols_cache = [s['symbol'] for s in symbols_data if s['status'] == 'TRADING']
            
            # Cache symbol info
            for symbol_data in symbols_data:
                symbol = symbol_data['symbol']
                self._symbol_info_cache[symbol] = symbol_data
                
            self.logger.info(f"Loaded info for {len(self._symbols_cache)} symbols")
            
        except Exception as e:
            raise DataProviderError(f"Failed to load exchange info: {e}")
    
    def normalize_interval(self, interval: str) -> str:
        """
        Normalize interval to Binance format.
        
        Args:
            interval (str): Input interval
            
        Returns:
            str: Binance-compatible interval
            
        Raises:
            ValueError: If interval is not supported
        """
        normalized = interval.lower()
        if normalized not in self.INTERVAL_MAP:
            raise ValueError(f"Unsupported interval: {interval}. Supported: {list(self.INTERVAL_MAP.keys())}")
        return self.INTERVAL_MAP[normalized]
    
    async def get_historical_candles(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """
        Fetch historical candlestick data from Binance.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            interval (str): Candle interval (e.g., '1m', '1h', '1d')
            start_time (Optional[datetime]): Start time for data range
            end_time (Optional[datetime]): End time for data range
            limit (Optional[int]): Maximum number of candles (max 1000)
            
        Returns:
            List[Candle]: Historical candles
        """
        symbol = self._validate_symbol(symbol)
        interval = self.normalize_interval(interval)
        
        params = {
            'symbol': symbol,
            'interval': interval
        }
        
        if start_time:
            params['startTime'] = int(start_time.timestamp() * 1000)
        
        if end_time:
            params['endTime'] = int(end_time.timestamp() * 1000)
        
        if limit:
            params['limit'] = min(limit, 1000)  # Binance max is 1000
        
        try:
            data = await self._make_request(self.ENDPOINTS['klines'], params)
            candles = []
            
            for kline in data:
                candle = Candle(
                    timestamp=int(kline[0]),
                    symbol=symbol,
                    interval=interval,
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                    quote_volume=float(kline[7]),
                    trade_count=int(kline[8]),
                    taker_buy_volume=float(kline[9]),
                    taker_buy_quote_volume=float(kline[10]),
                    raw_data={'binance_kline': kline}
                )
                candles.append(candle)
            
            self.logger.debug(f"Fetched {len(candles)} candles for {symbol} {interval}")
            return candles
            
        except Exception as e:
            raise self._handle_api_error(e, f"Failed to fetch candles for {symbol}")
    
    async def get_current_ticker(self, symbol: str) -> Ticker:
        """
        Get current 24hr ticker statistics.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Ticker: Current ticker data
        """
        symbol = self._validate_symbol(symbol)
        
        params = {'symbol': symbol}
        
        try:
            data = await self._make_request(self.ENDPOINTS['ticker_24hr'], params)
            
            ticker = Ticker(
                timestamp=int(data['closeTime']),
                symbol=symbol,
                price=float(data['lastPrice']),
                bid=float(data['bidPrice']),
                ask=float(data['askPrice']),
                bid_size=float(data['bidQty']),
                ask_size=float(data['askQty']),
                volume_24h=float(data['volume']),
                price_change_24h=float(data['priceChange']),
                price_change_percent_24h=float(data['priceChangePercent']),
                high_24h=float(data['highPrice']),
                low_24h=float(data['lowPrice']),
                open_24h=float(data['openPrice']),
                quote_volume_24h=float(data['quoteVolume']),
                raw_data={'binance_ticker': data}
            )
            
            return ticker
            
        except Exception as e:
            raise self._handle_api_error(e, f"Failed to fetch ticker for {symbol}")
    
    async def get_order_book(self, symbol: str, limit: Optional[int] = None) -> OrderBook:
        """
        Get order book snapshot.
        
        Args:
            symbol (str): Trading symbol
            limit (Optional[int]): Number of levels to return (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            OrderBook: Order book snapshot
        """
        symbol = self._validate_symbol(symbol)
        
        params = {'symbol': symbol}
        
        if limit:
            # Binance supports specific limit values
            valid_limits = [5, 10, 20, 50, 100, 500, 1000, 5000]
            params['limit'] = min(valid_limits, key=lambda x: abs(x - limit))
        
        try:
            data = await self._make_request(self.ENDPOINTS['depth'], params)
            
            # Convert bid/ask data to OrderBookLevel objects
            bids = [OrderBookLevel(float(level[0]), float(level[1])) 
                   for level in data['bids']]
            asks = [OrderBookLevel(float(level[0]), float(level[1])) 
                   for level in data['asks']]
            
            order_book = OrderBook(
                timestamp=int(time.time() * 1000),  # Binance doesn't provide timestamp
                symbol=symbol,
                bids=bids,
                asks=asks,
                last_update_id=data.get('lastUpdateId'),
                raw_data={'binance_depth': data}
            )
            
            return order_book
            
        except Exception as e:
            raise self._handle_api_error(e, f"Failed to fetch order book for {symbol}")
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: Optional[int] = None
    ) -> List[Trade]:
        """
        Get recent trade data.
        
        Args:
            symbol (str): Trading symbol
            limit (Optional[int]): Number of trades to return (max 1000)
            
        Returns:
            List[Trade]: Recent trades
        """
        symbol = self._validate_symbol(symbol)
        
        params = {'symbol': symbol}
        
        if limit:
            params['limit'] = min(limit, 1000)
        
        try:
            data = await self._make_request(self.ENDPOINTS['trades'], params)
            
            trades = []
            for trade_data in data:
                trade = Trade(
                    timestamp=int(trade_data['time']),
                    symbol=symbol,
                    trade_id=str(trade_data['id']),
                    price=float(trade_data['price']),
                    quantity=float(trade_data['qty']),
                    side='buy' if trade_data['isBuyerMaker'] else 'sell',
                    is_buyer_maker=trade_data['isBuyerMaker'],
                    raw_data={'binance_trade': trade_data}
                )
                trades.append(trade)
            
            return trades
            
        except Exception as e:
            raise self._handle_api_error(e, f"Failed to fetch trades for {symbol}")
    
    async def get_supported_symbols(self) -> List[str]:
        """
        Get list of supported trading symbols.
        
        Returns:
            List[str]: List of supported symbols
        """
        if not self._symbols_cache:
            await self._load_exchange_info()
        
        return self._symbols_cache.copy()
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed symbol information.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Symbol information
        """
        symbol = self._validate_symbol(symbol)
        
        if not self._symbol_info_cache:
            await self._load_exchange_info()
        
        if symbol not in self._symbol_info_cache:
            raise SymbolNotFoundError(f"Symbol not found: {symbol}")
        
        return self._symbol_info_cache[symbol].copy()
    
    async def ping(self) -> bool:
        """
        Test connection to Binance API.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            await self._make_request(self.ENDPOINTS['ping'])
            return True
        except Exception as e:
            self.logger.error(f"Ping failed: {e}")
            return False
    
    async def get_server_time(self) -> Optional[datetime]:
        """
        Get Binance server time.
        
        Returns:
            Optional[datetime]: Server time
        """
        try:
            data = await self._make_request(self.ENDPOINTS['time'])
            timestamp = data['serverTime'] / 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            self.logger.error(f"Failed to get server time: {e}")
            return None