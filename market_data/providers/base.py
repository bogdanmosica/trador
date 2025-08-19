"""
Base Market Data Provider Interface

Abstract base class defining the common interface for all market data providers.
Ensures consistent API across different exchanges and data sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Iterator, AsyncIterator
from datetime import datetime
import asyncio
import logging

from ..models import Candle, Ticker, OrderBook, Trade, MarketDataConfig


logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    
    Defines the common interface that all market data providers must implement
    to ensure consistent behavior across different exchanges and data sources.
    """
    
    def __init__(self, config: MarketDataConfig):
        """
        Initialize the market data provider.
        
        Args:
            config (MarketDataConfig): Provider configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__class__.__name__}.{self.__class__.__name__}")
        self._session = None
        self._rate_limiter = None
        
    @abstractmethod
    async def get_historical_candles(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """
        Fetch historical candlestick data.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            interval (str): Candle interval (e.g., '1m', '5m', '1h', '1d')
            start_time (Optional[datetime]): Start time for data range
            end_time (Optional[datetime]): End time for data range
            limit (Optional[int]): Maximum number of candles to return
            
        Returns:
            List[Candle]: List of historical candles
        """
        pass
    
    @abstractmethod
    async def get_current_ticker(self, symbol: str) -> Ticker:
        """
        Get current ticker data for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Ticker: Current ticker data
        """
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: Optional[int] = None) -> OrderBook:
        """
        Get current order book snapshot.
        
        Args:
            symbol (str): Trading symbol
            limit (Optional[int]): Number of price levels to return
            
        Returns:
            OrderBook: Current order book snapshot
        """
        pass
    
    @abstractmethod
    async def get_recent_trades(
        self,
        symbol: str,
        limit: Optional[int] = None
    ) -> List[Trade]:
        """
        Get recent trade data.
        
        Args:
            symbol (str): Trading symbol
            limit (Optional[int]): Number of trades to return
            
        Returns:
            List[Trade]: List of recent trades
        """
        pass
    
    @abstractmethod
    async def get_supported_symbols(self) -> List[str]:
        """
        Get list of supported trading symbols.
        
        Returns:
            List[str]: List of supported symbols
        """
        pass
    
    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed information about a trading symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Symbol information including precision, filters, etc.
        """
        pass
    
    # Optional streaming methods (can be implemented by providers that support it)
    async def stream_candles(
        self,
        symbol: str,
        interval: str
    ) -> AsyncIterator[Candle]:
        """
        Stream live candlestick updates.
        
        Args:
            symbol (str): Trading symbol
            interval (str): Candle interval
            
        Yields:
            Candle: Live candle updates
        """
        raise NotImplementedError("Live candle streaming not implemented")
    
    async def stream_tickers(self, symbols: List[str]) -> AsyncIterator[Ticker]:
        """
        Stream live ticker updates.
        
        Args:
            symbols (List[str]): List of symbols to stream
            
        Yields:
            Ticker: Live ticker updates
        """
        raise NotImplementedError("Live ticker streaming not implemented")
    
    async def stream_order_book(
        self,
        symbol: str,
        update_speed: str = "1000ms"
    ) -> AsyncIterator[OrderBook]:
        """
        Stream live order book updates.
        
        Args:
            symbol (str): Trading symbol
            update_speed (str): Update frequency
            
        Yields:
            OrderBook: Live order book updates
        """
        raise NotImplementedError("Live order book streaming not implemented")
    
    async def stream_trades(self, symbol: str) -> AsyncIterator[Trade]:
        """
        Stream live trade updates.
        
        Args:
            symbol (str): Trading symbol
            
        Yields:
            Trade: Live trade updates
        """
        raise NotImplementedError("Live trade streaming not implemented")
    
    # Utility methods
    async def ping(self) -> bool:
        """
        Test connection to the data provider.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            # Try to get a list of symbols as a connectivity test
            symbols = await self.get_supported_symbols()
            return len(symbols) > 0
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_server_time(self) -> Optional[datetime]:
        """
        Get server time from the data provider.
        
        Returns:
            Optional[datetime]: Server time if available
        """
        # Default implementation returns None
        # Providers can override this if they support server time
        return None
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format for this provider.
        
        Args:
            symbol (str): Input symbol
            
        Returns:
            str: Normalized symbol format
        """
        # Default implementation returns uppercase
        # Providers can override for specific formatting
        return symbol.upper()
    
    def normalize_interval(self, interval: str) -> str:
        """
        Normalize interval format for this provider.
        
        Args:
            interval (str): Input interval
            
        Returns:
            str: Normalized interval format
        """
        # Default implementation returns as-is
        # Providers can override for specific formatting
        return interval.lower()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """
        Initialize connection to the data provider.
        
        Override in subclasses for provider-specific connection setup.
        """
        self.logger.info(f"Connecting to {self.__class__.__name__}")
    
    async def disconnect(self):
        """
        Clean up connection to the data provider.
        
        Override in subclasses for provider-specific cleanup.
        """
        self.logger.info(f"Disconnecting from {self.__class__.__name__}")
        if self._session:
            await self._session.close()
    
    def get_cache_key(self, method: str, **kwargs) -> str:
        """
        Generate cache key for data requests.
        
        Args:
            method (str): Method name
            **kwargs: Method parameters
            
        Returns:
            str: Cache key
        """
        # Create deterministic cache key from method and parameters
        params = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        return f"{self.__class__.__name__}_{method}_{params}"
    
    def _validate_symbol(self, symbol: str) -> str:
        """
        Validate and normalize symbol format.
        
        Args:
            symbol (str): Symbol to validate
            
        Returns:
            str: Validated symbol
            
        Raises:
            ValueError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        
        normalized = self.normalize_symbol(symbol)
        
        # Basic symbol format validation
        if len(normalized) < 3:
            raise ValueError(f"Symbol too short: {symbol}")
        
        return normalized
    
    def _validate_interval(self, interval: str) -> str:
        """
        Validate and normalize interval format.
        
        Args:
            interval (str): Interval to validate
            
        Returns:
            str: Validated interval
            
        Raises:
            ValueError: If interval is invalid
        """
        if not interval or not isinstance(interval, str):
            raise ValueError("Interval must be a non-empty string")
        
        normalized = self.normalize_interval(interval)
        
        # Common interval validation
        valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        if normalized not in valid_intervals:
            self.logger.warning(f"Unusual interval format: {interval}")
        
        return normalized
    
    def _handle_api_error(self, error: Exception, context: str = "") -> Exception:
        """
        Handle and transform API errors.
        
        Args:
            error (Exception): Original error
            context (str): Context description
            
        Returns:
            Exception: Transformed error
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg)
        
        # Transform common errors to more specific types
        if "rate limit" in str(error).lower():
            return RateLimitError(error_msg)
        elif "not found" in str(error).lower() or "invalid symbol" in str(error).lower():
            return SymbolNotFoundError(error_msg)
        elif "timeout" in str(error).lower():
            return TimeoutError(error_msg)
        else:
            return DataProviderError(error_msg)


# Custom exceptions for market data providers
class DataProviderError(Exception):
    """Base exception for market data provider errors."""
    pass


class RateLimitError(DataProviderError):
    """Raised when API rate limits are exceeded."""
    pass


class SymbolNotFoundError(DataProviderError):
    """Raised when a requested symbol is not found."""
    pass


class DataValidationError(DataProviderError):
    """Raised when received data fails validation."""
    pass


class ConnectionError(DataProviderError):
    """Raised when connection to provider fails."""
    pass