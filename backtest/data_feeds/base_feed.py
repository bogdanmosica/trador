"""
Base Data Feed Interface

Abstract base class defining the interface for market data providers.
Ensures consistent data access patterns across different exchange APIs
and enables easy swapping of data sources.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd

from ..models import MarketSnapshot


class BaseDataFeed(ABC):
    """
    Abstract base class for market data feeds.
    
    Defines the interface that all data feed implementations must follow
    to ensure consistent data access and caching behavior.
    """
    
    def __init__(self, cache_enabled: bool = True, cache_path: str = "./data_cache"):
        """
        Initialize the data feed with caching configuration.
        
        Args:
            cache_enabled (bool): Whether to enable data caching
            cache_path (str): Path to store cached data files
        """
        self.cache_enabled = cache_enabled
        self.cache_path = cache_path
        self._cache: Dict[str, pd.DataFrame] = {}
    
    @abstractmethod
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List[MarketSnapshot]:
        """
        Fetch historical OHLCV data for a symbol within a time range.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            timeframe (str): Timeframe for candles (e.g., '1h', '4h', '1d')
            start_time (datetime): Start time for data fetch
            end_time (datetime): End time for data fetch
            limit (Optional[int]): Maximum number of candles to fetch
            
        Returns:
            List[MarketSnapshot]: List of market data snapshots
        """
        pass
    
    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading information for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Symbol information including min/max quantities, price precision, etc.
        """
        pass
    
    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """
        Get list of available trading symbols.
        
        Returns:
            List[str]: List of available symbols
        """
        pass
    
    def _generate_cache_key(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> str:
        """
        Generate a unique cache key for data requests.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe
            start_time (datetime): Start time
            end_time (datetime): End time
            
        Returns:
            str: Unique cache key
        """
        start_str = start_time.strftime('%Y%m%d_%H%M%S')
        end_str = end_time.strftime('%Y%m%d_%H%M%S')
        return f"{symbol}_{timeframe}_{start_str}_{end_str}"
    
    def _cache_data(self, cache_key: str, data: List[MarketSnapshot]) -> None:
        """
        Cache market data for future use.
        
        Args:
            cache_key (str): Unique identifier for cached data
            data (List[MarketSnapshot]): Market data to cache
        """
        if not self.cache_enabled:
            return
        
        # Convert to DataFrame for efficient storage
        df_data = []
        for snapshot in data:
            df_data.append({
                'timestamp': snapshot.timestamp,
                'symbol': snapshot.symbol,
                'open': snapshot.open,
                'high': snapshot.high,
                'low': snapshot.low,
                'close': snapshot.close,
                'volume': snapshot.volume,
                'timeframe': snapshot.timeframe,
                'bid': snapshot.bid,
                'ask': snapshot.ask,
                'spread': snapshot.spread
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            self._cache[cache_key] = df
    
    def _get_cached_data(self, cache_key: str) -> Optional[List[MarketSnapshot]]:
        """
        Retrieve cached market data if available.
        
        Args:
            cache_key (str): Unique identifier for cached data
            
        Returns:
            Optional[List[MarketSnapshot]]: Cached data if available, None otherwise
        """
        if not self.cache_enabled or cache_key not in self._cache:
            return None
        
        df = self._cache[cache_key]
        snapshots = []
        
        for _, row in df.iterrows():
            snapshot = MarketSnapshot(
                timestamp=row['timestamp'],
                symbol=row['symbol'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                timeframe=row['timeframe'],
                bid=row['bid'],
                ask=row['ask'],
                spread=row['spread']
            )
            snapshots.append(snapshot)
        
        return snapshots
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cached data.
        
        Returns:
            Dict[str, Any]: Cache statistics including size and keys
        """
        return {
            'cache_enabled': self.cache_enabled,
            'cached_keys': list(self._cache.keys()),
            'cache_count': len(self._cache)
        }