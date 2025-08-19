"""
Unified Market Data Models

Standardized data structures for market data across all providers.
Ensures consistent data format for strategies and backtesting engines.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
import json


@dataclass
class Candle:
    """
    Standardized OHLCV candlestick data.
    
    Represents price and volume data for a specific time period,
    normalized across all market data providers.
    """
    timestamp: int  # Unix timestamp in milliseconds
    symbol: str
    interval: str  # e.g., '1m', '5m', '1h', '1d'
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: Optional[float] = None  # Volume in quote currency
    trade_count: Optional[int] = None
    taker_buy_volume: Optional[float] = None
    taker_buy_quote_volume: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000)
    
    @property
    def price_change(self) -> float:
        """Calculate price change (close - open)."""
        return self.close - self.open
    
    @property
    def price_change_percent(self) -> float:
        """Calculate percentage price change."""
        if self.open == 0:
            return 0.0
        return ((self.close - self.open) / self.open) * 100
    
    @property
    def typical_price(self) -> float:
        """Calculate typical price (HLC/3)."""
        return (self.high + self.low + self.close) / 3
    
    @property
    def weighted_price(self) -> float:
        """Calculate volume-weighted average price approximation."""
        return (self.high + self.low + self.close * 2) / 4
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert candle to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'interval': self.interval,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'quote_volume': self.quote_volume,
            'trade_count': self.trade_count,
            'taker_buy_volume': self.taker_buy_volume,
            'taker_buy_quote_volume': self.taker_buy_quote_volume,
            'price_change': self.price_change,
            'price_change_percent': self.price_change_percent
        }
    
    def to_json(self) -> str:
        """Convert candle to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candle':
        """Create Candle from dictionary data."""
        return cls(
            timestamp=int(data['timestamp']),
            symbol=data['symbol'],
            interval=data['interval'],
            open=float(data['open']),
            high=float(data['high']),
            low=float(data['low']),
            close=float(data['close']),
            volume=float(data['volume']),
            quote_volume=data.get('quote_volume'),
            trade_count=data.get('trade_count'),
            taker_buy_volume=data.get('taker_buy_volume'),
            taker_buy_quote_volume=data.get('taker_buy_quote_volume'),
            raw_data=data.get('raw_data', {})
        )


@dataclass
class Ticker:
    """
    Real-time ticker data for a symbol.
    
    Contains current market statistics including price, volume,
    and 24-hour change information.
    """
    timestamp: int  # Unix timestamp in milliseconds
    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percent_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    open_24h: Optional[float] = None
    quote_volume_24h: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000)
    
    @property
    def spread(self) -> Optional[float]:
        """Calculate bid-ask spread."""
        if self.bid is not None and self.ask is not None:
            return self.ask - self.bid
        return None
    
    @property
    def spread_percent(self) -> Optional[float]:
        """Calculate bid-ask spread as percentage of mid price."""
        if self.spread is not None and self.bid is not None and self.ask is not None:
            mid_price = (self.bid + self.ask) / 2
            if mid_price > 0:
                return (self.spread / mid_price) * 100
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ticker to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'price': self.price,
            'bid': self.bid,
            'ask': self.ask,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'volume_24h': self.volume_24h,
            'price_change_24h': self.price_change_24h,
            'price_change_percent_24h': self.price_change_percent_24h,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h,
            'open_24h': self.open_24h,
            'quote_volume_24h': self.quote_volume_24h,
            'spread': self.spread,
            'spread_percent': self.spread_percent
        }


@dataclass 
class OrderBookLevel:
    """Individual price level in order book."""
    price: float
    quantity: float
    
    @property
    def notional_value(self) -> float:
        """Calculate notional value (price * quantity)."""
        return self.price * self.quantity


@dataclass
class OrderBook:
    """
    Order book snapshot with bids and asks.
    
    Contains current market depth information for a symbol.
    """
    timestamp: int  # Unix timestamp in milliseconds
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    last_update_id: Optional[int] = None
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000)
    
    @property
    def best_bid(self) -> Optional[OrderBookLevel]:
        """Get highest bid price level."""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[OrderBookLevel]:
        """Get lowest ask price level."""
        return self.asks[0] if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        """Calculate bid-ask spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return None
    
    @property
    def mid_price(self) -> Optional[float]:
        """Calculate mid price between best bid and ask."""
        if self.best_bid and self.best_ask:
            return (self.best_bid.price + self.best_ask.price) / 2
        return None
    
    def get_bid_depth(self, max_levels: int = 10) -> float:
        """Calculate total bid depth (volume) up to max levels."""
        return sum(level.quantity for level in self.bids[:max_levels])
    
    def get_ask_depth(self, max_levels: int = 10) -> float:
        """Calculate total ask depth (volume) up to max levels."""
        return sum(level.quantity for level in self.asks[:max_levels])
    
    def get_imbalance_ratio(self, max_levels: int = 5) -> Optional[float]:
        """
        Calculate order book imbalance ratio.
        
        Returns bid_depth / (bid_depth + ask_depth).
        Values > 0.5 indicate more buying pressure.
        """
        bid_depth = self.get_bid_depth(max_levels)
        ask_depth = self.get_ask_depth(max_levels)
        total_depth = bid_depth + ask_depth
        
        if total_depth > 0:
            return bid_depth / total_depth
        return None


@dataclass
class Trade:
    """
    Individual trade execution data.
    
    Represents a completed trade on the exchange.
    """
    timestamp: int  # Unix timestamp in milliseconds
    symbol: str
    trade_id: str
    price: float
    quantity: float
    side: str  # 'buy' or 'sell' (from taker perspective)
    is_buyer_maker: Optional[bool] = None
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000)
    
    @property
    def notional_value(self) -> float:
        """Calculate trade notional value."""
        return self.price * self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'trade_id': self.trade_id,
            'price': self.price,
            'quantity': self.quantity,
            'side': self.side,
            'is_buyer_maker': self.is_buyer_maker,
            'notional_value': self.notional_value
        }


@dataclass
class MarketDataConfig:
    """Configuration for market data providers."""
    
    # API Configuration
    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    testnet: bool = False
    
    # Rate Limiting
    requests_per_minute: int = 1200
    burst_limit: int = 10
    
    # Timeouts and Retries
    timeout_seconds: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    
    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 60
    cache_max_size: int = 1000
    
    # Data Quality
    validate_data: bool = True
    fill_missing_data: bool = True
    remove_outliers: bool = False
    outlier_threshold: float = 3.0  # Standard deviations
    
    # Storage
    enable_storage: bool = False
    storage_path: Optional[str] = None
    storage_format: str = 'parquet'  # 'parquet', 'csv', 'json'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'base_url': self.base_url,
            'testnet': self.testnet,
            'requests_per_minute': self.requests_per_minute,
            'burst_limit': self.burst_limit,
            'timeout_seconds': self.timeout_seconds,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'backoff_factor': self.backoff_factor,
            'enable_cache': self.enable_cache,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'cache_max_size': self.cache_max_size,
            'validate_data': self.validate_data,
            'fill_missing_data': self.fill_missing_data,
            'remove_outliers': self.remove_outliers,
            'outlier_threshold': self.outlier_threshold,
            'enable_storage': self.enable_storage,
            'storage_path': self.storage_path,
            'storage_format': self.storage_format
        }


# Validation functions
def validate_candle(candle: Candle) -> bool:
    """
    Validate candle data for consistency.
    
    Args:
        candle (Candle): Candle to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Basic data type validation
        if not isinstance(candle.timestamp, int) or candle.timestamp <= 0:
            return False
        
        if not isinstance(candle.symbol, str) or not candle.symbol:
            return False
        
        # Price validation
        prices = [candle.open, candle.high, candle.low, candle.close]
        if any(price <= 0 for price in prices):
            return False
        
        # OHLC relationship validation
        if not (candle.low <= candle.open <= candle.high):
            return False
        if not (candle.low <= candle.close <= candle.high):
            return False
        
        # Volume validation
        if candle.volume < 0:
            return False
        
        return True
        
    except (TypeError, AttributeError):
        return False


def validate_ticker(ticker: Ticker) -> bool:
    """
    Validate ticker data for consistency.
    
    Args:
        ticker (Ticker): Ticker to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Basic validation
        if not isinstance(ticker.timestamp, int) or ticker.timestamp <= 0:
            return False
        
        if not isinstance(ticker.symbol, str) or not ticker.symbol:
            return False
        
        if ticker.price <= 0:
            return False
        
        # Bid/ask validation
        if ticker.bid is not None and ticker.ask is not None:
            if ticker.bid <= 0 or ticker.ask <= 0:
                return False
            if ticker.bid >= ticker.ask:
                return False
        
        return True
        
    except (TypeError, AttributeError):
        return False