"""
Cache Manager

Intelligent caching system for market data with TTL, LRU eviction,
and memory management. Supports both in-memory and persistent caching.
"""

import time
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading
import logging

from ..models import Candle, Ticker, OrderBook, Trade


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = 0.0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp
    
    def touch(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_access = time.time()


class CacheManager:
    """
    High-performance cache manager for market data.
    
    Features:
    - TTL (Time To Live) expiration
    - LRU (Least Recently Used) eviction
    - Memory usage monitoring
    - Thread-safe operations
    - Persistent cache support
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 300.0,  # 5 minutes
        max_memory_mb: float = 100.0,
        persistent: bool = False,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize cache manager.
        
        Args:
            max_size (int): Maximum number of cache entries
            default_ttl (float): Default TTL in seconds
            max_memory_mb (float): Maximum memory usage in MB
            persistent (bool): Enable persistent cache
            cache_dir (Optional[str]): Directory for persistent cache
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.persistent = persistent
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._memory_usage = 0
        
        # Persistent cache setup
        if persistent:
            self.cache_dir = Path(cache_dir or "./cache")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_persistent_cache()
        else:
            self.cache_dir = None
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Any]: Cached value or None
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired:
                self._remove_entry(key)
                self._stats['misses'] += 1
                return None
            
            # Update access statistics
            entry.touch()
            self._stats['hits'] += 1
            
            return entry.value
    
    def put(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ):
        """
        Store value in cache.
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (Optional[float]): Custom TTL, uses default if None
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            # Calculate memory usage
            value_size = self._estimate_size(value)
            
            # Check if we need to evict entries
            self._ensure_capacity(value_size)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            # Remove old entry if exists
            if key in self._cache:
                self._remove_entry(key)
            
            # Add new entry
            self._cache[key] = entry
            self._memory_usage += value_size
            
            # Save to persistent cache if enabled
            if self.persistent:
                self._save_to_persistent(key, entry)
    
    def invalidate(self, key: str) -> bool:
        """
        Remove specific key from cache.
        
        Args:
            key (str): Cache key to remove
            
        Returns:
            bool: True if key was removed
        """
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._memory_usage = 0
            
            if self.persistent and self.cache_dir:
                # Clear persistent cache
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            int: Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'memory_usage_mb': self._memory_usage / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'hit_rate_percent': hit_rate,
                'total_hits': self._stats['hits'],
                'total_misses': self._stats['misses'],
                'total_evictions': self._stats['evictions'],
                'memory_evictions': self._stats['memory_evictions']
            }
    
    def _ensure_capacity(self, new_value_size: int):
        """Ensure cache has capacity for new value."""
        # Memory-based eviction
        while (self._memory_usage + new_value_size > self.max_memory_bytes and 
               len(self._cache) > 0):
            self._evict_lru()
            self._stats['memory_evictions'] += 1
        
        # Size-based eviction
        while len(self._cache) >= self.max_size:
            self._evict_lru()
            self._stats['evictions'] += 1
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_access or self._cache[k].timestamp
        )
        
        self._remove_entry(lru_key)
    
    def _remove_entry(self, key: str):
        """Remove entry and update memory usage."""
        if key in self._cache:
            entry = self._cache[key]
            size = self._estimate_size(entry.value)
            self._memory_usage = max(0, self._memory_usage - size)
            del self._cache[key]
            
            # Remove from persistent cache
            if self.persistent:
                self._remove_from_persistent(key)
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate memory size of object."""
        try:
            if isinstance(obj, (Candle, Ticker, OrderBook, Trade)):
                # Use pickle size for dataclass objects
                return len(pickle.dumps(obj))
            elif isinstance(obj, (str, bytes)):
                return len(obj)
            elif isinstance(obj, (list, tuple)):
                return sum(self._estimate_size(item) for item in obj)
            elif isinstance(obj, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v) 
                    for k, v in obj.items()
                )
            else:
                # Fallback to pickle size
                return len(pickle.dumps(obj))
        except Exception:
            # Conservative estimate
            return 1024
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _save_to_persistent(self, key: str, entry: CacheEntry):
        """Save entry to persistent cache."""
        if not self.cache_dir:
            return
        
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.warning(f"Failed to save to persistent cache: {e}")
    
    def _load_persistent_cache(self):
        """Load entries from persistent cache."""
        if not self.cache_dir or not self.cache_dir.exists():
            return
        
        loaded_count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                # Check if entry is still valid
                if not entry.is_expired:
                    key = cache_file.stem
                    self._cache[key] = entry
                    self._memory_usage += self._estimate_size(entry.value)
                    loaded_count += 1
                else:
                    # Remove expired persistent cache file
                    cache_file.unlink()
                    
            except Exception as e:
                logger.warning(f"Failed to load cache file {cache_file}: {e}")
                # Remove corrupted cache file
                try:
                    cache_file.unlink()
                except:
                    pass
        
        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} entries from persistent cache")
    
    def _remove_from_persistent(self, key: str):
        """Remove entry from persistent cache."""
        if not self.cache_dir:
            return
        
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove from persistent cache: {e}")


# Decorator for automatic caching
def cached(
    cache_manager: CacheManager,
    ttl: Optional[float] = None,
    key_prefix: str = ""
):
    """
    Decorator for automatic function result caching.
    
    Args:
        cache_manager (CacheManager): Cache manager instance
        ttl (Optional[float]): Custom TTL for cached results
        key_prefix (str): Prefix for cache keys
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': sorted(kwargs.items())
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = f"{key_prefix}_{hashlib.md5(key_str.encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.put(cache_key, result, ttl)
            
            return result
        
        # For async functions
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': sorted(kwargs.items())
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = f"{key_prefix}_{hashlib.md5(key_str.encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.put(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator