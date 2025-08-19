"""
Mock Market Data Provider

Mock implementation of MarketDataProvider for testing and development.
Generates realistic market data without external API dependencies.
"""

import asyncio
import random
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import math

from .base import MarketDataProvider
from ..models import Candle, Ticker, OrderBook, OrderBookLevel, Trade, MarketDataConfig


class MockProvider(MarketDataProvider):
    """
    Mock market data provider for testing and development.
    
    Generates realistic-looking market data without requiring external APIs.
    Useful for testing, development, and offline scenarios.
    """
    
    def __init__(self, config: Optional[MarketDataConfig] = None):
        """
        Initialize mock provider.
        
        Args:
            config (Optional[MarketDataConfig]): Provider configuration
        """
        if config is None:
            config = MarketDataConfig(
                base_url="mock://localhost",
                requests_per_minute=10000,  # No rate limiting for mock
                timeout_seconds=1
            )
        
        super().__init__(config)
        
        # Mock data parameters
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'XRPUSDT',
            'SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT'
        ]
        
        # Base prices for symbols (used for realistic price generation)
        self.base_prices = {
            'BTCUSDT': 43000.0,
            'ETHUSDT': 2600.0,
            'ADAUSDT': 0.38,
            'BNBUSDT': 310.0,
            'XRPUSDT': 0.52,
            'SOLUSDT': 98.0,
            'DOTUSDT': 7.2,
            'LINKUSDT': 14.5,
            'LTCUSDT': 72.0,
            'BCHUSDT': 245.0
        }
        
        # Market state for consistency
        self.current_prices = self.base_prices.copy()
        self.price_trends = {symbol: 0.0 for symbol in self.symbols}  # -1 to 1
        
        # Volatility settings
        self.volatility = {
            'BTCUSDT': 0.02,
            'ETHUSDT': 0.025,
            'ADAUSDT': 0.04,
            'BNBUSDT': 0.03,
            'XRPUSDT': 0.035,
            'SOLUSDT': 0.045,
            'DOTUSDT': 0.04,
            'LINKUSDT': 0.038,
            'LTCUSDT': 0.035,
            'BCHUSDT': 0.04
        }
        
        # Supported intervals
        self.supported_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        
        self.logger.info("Mock provider initialized with simulated market data")
    
    async def connect(self):
        """Initialize mock connection."""
        await super().connect()
        # Simulate connection delay
        await asyncio.sleep(0.1)
        self.logger.info("Mock provider connected")
    
    async def get_historical_candles(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """
        Generate mock historical candlestick data.
        
        Args:
            symbol (str): Trading symbol
            interval (str): Candle interval
            start_time (Optional[datetime]): Start time for data range
            end_time (Optional[datetime]): End time for data range
            limit (Optional[int]): Maximum number of candles
            
        Returns:
            List[Candle]: Mock historical candles
        """
        symbol = self._validate_symbol(symbol)
        interval = self._validate_interval(interval)
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.05, 0.2))
        
        # Determine time range
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        
        if start_time is None:
            if limit:
                # Calculate start time based on limit and interval
                interval_seconds = self._interval_to_seconds(interval)
                start_time = end_time - timedelta(seconds=interval_seconds * limit)
            else:
                # Default to 1000 candles back
                interval_seconds = self._interval_to_seconds(interval)
                start_time = end_time - timedelta(seconds=interval_seconds * 1000)
        
        # Generate candles
        candles = self._generate_candles(symbol, interval, start_time, end_time, limit)
        
        self.logger.debug(f"Generated {len(candles)} mock candles for {symbol} {interval}")
        return candles
    
    async def get_current_ticker(self, symbol: str) -> Ticker:
        """
        Generate mock current ticker data.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Ticker: Mock ticker data
        """
        symbol = self._validate_symbol(symbol)
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.02, 0.1))
        
        # Get current price (simulate small movement)
        current_price = self.current_prices[symbol]
        volatility = self.volatility[symbol]
        
        # Small random price movement
        price_change = random.gauss(0, volatility * current_price * 0.1)
        new_price = max(current_price + price_change, current_price * 0.5)  # Prevent negative prices
        self.current_prices[symbol] = new_price
        
        # Generate 24h statistics
        price_24h_change = random.gauss(0, volatility * current_price * 0.5)
        price_24h_change_percent = (price_24h_change / current_price) * 100
        
        high_24h = new_price + abs(random.gauss(0, volatility * current_price * 0.3))
        low_24h = new_price - abs(random.gauss(0, volatility * current_price * 0.3))
        open_24h = new_price - price_24h_change
        
        # Generate bid/ask spread (0.01% to 0.1%)
        spread_percent = random.uniform(0.0001, 0.001)
        spread = new_price * spread_percent
        bid = new_price - spread / 2
        ask = new_price + spread / 2
        
        # Generate volumes
        base_volume = random.uniform(1000, 50000)
        volume_24h = base_volume * random.uniform(20, 100)
        quote_volume_24h = volume_24h * new_price
        
        ticker = Ticker(
            timestamp=int(time.time() * 1000),
            symbol=symbol,
            price=new_price,
            bid=bid,
            ask=ask,
            bid_size=random.uniform(0.1, 10.0),
            ask_size=random.uniform(0.1, 10.0),
            volume_24h=volume_24h,
            price_change_24h=price_24h_change,
            price_change_percent_24h=price_24h_change_percent,
            high_24h=high_24h,
            low_24h=low_24h,
            open_24h=open_24h,
            quote_volume_24h=quote_volume_24h,
            raw_data={'mock_provider': True}
        )
        
        return ticker
    
    async def get_order_book(self, symbol: str, limit: Optional[int] = None) -> OrderBook:
        """
        Generate mock order book data.
        
        Args:
            symbol (str): Trading symbol
            limit (Optional[int]): Number of price levels
            
        Returns:
            OrderBook: Mock order book
        """
        symbol = self._validate_symbol(symbol)
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.02, 0.1))
        
        if limit is None:
            limit = 20
        
        current_price = self.current_prices[symbol]
        
        # Generate bid levels (below current price)
        bids = []
        for i in range(limit):
            price_offset = (i + 1) * random.uniform(0.0001, 0.001) * current_price
            price = current_price - price_offset
            quantity = random.uniform(0.1, 50.0)
            bids.append(OrderBookLevel(price, quantity))
        
        # Generate ask levels (above current price)
        asks = []
        for i in range(limit):
            price_offset = (i + 1) * random.uniform(0.0001, 0.001) * current_price
            price = current_price + price_offset
            quantity = random.uniform(0.1, 50.0)
            asks.append(OrderBookLevel(price, quantity))
        
        order_book = OrderBook(
            timestamp=int(time.time() * 1000),
            symbol=symbol,
            bids=bids,
            asks=asks,
            last_update_id=random.randint(1000000, 9999999),
            raw_data={'mock_provider': True}
        )
        
        return order_book
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: Optional[int] = None
    ) -> List[Trade]:
        """
        Generate mock recent trade data.
        
        Args:
            symbol (str): Trading symbol
            limit (Optional[int]): Number of trades
            
        Returns:
            List[Trade]: Mock recent trades
        """
        symbol = self._validate_symbol(symbol)
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.02, 0.1))
        
        if limit is None:
            limit = 100
        
        current_price = self.current_prices[symbol]
        volatility = self.volatility[symbol]
        
        trades = []
        base_timestamp = int(time.time() * 1000)
        
        for i in range(limit):
            # Generate trade price around current price
            price_variance = random.gauss(0, volatility * current_price * 0.01)
            trade_price = max(current_price + price_variance, current_price * 0.9)
            
            # Generate trade details
            trade = Trade(
                timestamp=base_timestamp - (limit - i) * random.randint(100, 5000),
                symbol=symbol,
                trade_id=str(random.randint(100000000, 999999999)),
                price=trade_price,
                quantity=random.uniform(0.001, 10.0),
                side=random.choice(['buy', 'sell']),
                is_buyer_maker=random.choice([True, False]),
                raw_data={'mock_provider': True}
            )
            trades.append(trade)
        
        # Sort by timestamp (oldest first)
        trades.sort(key=lambda t: t.timestamp)
        
        return trades
    
    async def get_supported_symbols(self) -> List[str]:
        """
        Get list of supported symbols.
        
        Returns:
            List[str]: List of mock symbols
        """
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.01, 0.05))
        return self.symbols.copy()
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get mock symbol information.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Mock symbol info
        """
        symbol = self._validate_symbol(symbol)
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        base_asset = symbol.replace('USDT', '').replace('BTC', '').replace('ETH', '')
        quote_asset = 'USDT'
        
        if symbol.endswith('BTC'):
            quote_asset = 'BTC'
        elif symbol.endswith('ETH'):
            quote_asset = 'ETH'
        
        symbol_info = {
            'symbol': symbol,
            'status': 'TRADING',
            'baseAsset': base_asset,
            'quoteAsset': quote_asset,
            'baseAssetPrecision': 8,
            'quoteAssetPrecision': 8,
            'orderTypes': ['LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT'],
            'icebergAllowed': True,
            'ocoAllowed': True,
            'filters': [
                {
                    'filterType': 'PRICE_FILTER',
                    'minPrice': '0.00000001',
                    'maxPrice': '1000000.00000000',
                    'tickSize': '0.00000001'
                },
                {
                    'filterType': 'LOT_SIZE',
                    'minQty': '0.00000001',
                    'maxQty': '9000000.00000000',
                    'stepSize': '0.00000001'
                },
                {
                    'filterType': 'MIN_NOTIONAL',
                    'minNotional': '10.00000000'
                }
            ]
        }
        
        return symbol_info
    
    async def ping(self) -> bool:
        """
        Mock ping test.
        
        Returns:
            bool: Always True for mock provider
        """
        await asyncio.sleep(random.uniform(0.01, 0.03))
        return True
    
    async def get_server_time(self) -> Optional[datetime]:
        """
        Get mock server time.
        
        Returns:
            Optional[datetime]: Current time
        """
        await asyncio.sleep(random.uniform(0.01, 0.03))
        return datetime.now(timezone.utc)
    
    def _generate_candles(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """Generate realistic mock candle data."""
        interval_seconds = self._interval_to_seconds(interval)
        
        # Calculate number of candles needed
        total_seconds = (end_time - start_time).total_seconds()
        num_candles = int(total_seconds // interval_seconds)
        
        if limit:
            num_candles = min(num_candles, limit)
        
        candles = []
        current_time = start_time
        current_price = self.base_prices[symbol]
        volatility = self.volatility[symbol]
        
        # Generate trend for this period
        trend = random.gauss(0, 0.3)  # Overall trend direction
        
        for i in range(num_candles):
            # Generate OHLC with realistic relationships
            
            # Open price (close of previous candle or current price)
            open_price = current_price
            
            # Generate price movement for this candle
            price_change = random.gauss(trend * 0.1, volatility)
            close_change = price_change * current_price
            close_price = max(open_price + close_change, open_price * 0.95)  # Prevent extreme drops
            
            # Generate high and low
            range_multiplier = random.uniform(0.5, 2.0)
            price_range = abs(close_price - open_price) * range_multiplier
            
            high_offset = random.uniform(0, price_range)
            low_offset = random.uniform(0, price_range)
            
            high_price = max(open_price, close_price) + high_offset
            low_price = min(open_price, close_price) - low_offset
            
            # Ensure OHLC relationships are valid
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            # Generate volume
            base_volume = random.uniform(100, 5000)
            volume_multiplier = 1 + abs(price_change) * 10  # Higher volume with bigger moves
            volume = base_volume * volume_multiplier
            
            quote_volume = volume * ((open_price + close_price) / 2)
            
            # Generate trade count
            trade_count = int(volume / random.uniform(0.1, 2.0))
            
            # Generate taker buy volumes (typically 40-60% of total volume)
            taker_buy_ratio = random.uniform(0.4, 0.6)
            taker_buy_volume = volume * taker_buy_ratio
            taker_buy_quote_volume = quote_volume * taker_buy_ratio
            
            candle = Candle(
                timestamp=int(current_time.timestamp() * 1000),
                symbol=symbol,
                interval=interval,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                quote_volume=quote_volume,
                trade_count=trade_count,
                taker_buy_volume=taker_buy_volume,
                taker_buy_quote_volume=taker_buy_quote_volume,
                raw_data={'mock_provider': True}
            )
            
            candles.append(candle)
            
            # Update for next candle
            current_price = close_price
            current_time += timedelta(seconds=interval_seconds)
            
            # Add some noise to trend
            trend += random.gauss(0, 0.05)
            trend = max(-1, min(1, trend))  # Keep trend bounded
        
        # Update current price for this symbol
        if candles:
            self.current_prices[symbol] = candles[-1].close
        
        return candles
    
    def _interval_to_seconds(self, interval: str) -> int:
        """Convert interval string to seconds."""
        interval_map = {
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '2h': 7200,
            '4h': 14400,
            '6h': 21600,
            '8h': 28800,
            '12h': 43200,
            '1d': 86400,
            '3d': 259200,
            '1w': 604800,
            '1M': 2592000  # Approximate month
        }
        
        return interval_map.get(interval, 3600)  # Default to 1 hour
    
    def normalize_interval(self, interval: str) -> str:
        """Normalize interval format."""
        normalized = interval.lower()
        if normalized not in self.supported_intervals:
            raise ValueError(f"Unsupported interval: {interval}")
        return normalized