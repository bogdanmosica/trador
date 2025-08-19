"""
Data Feed Module

Provides interfaces and implementations for fetching historical market data
from various sources. Supports caching and modular adapter design for
different exchange APIs.
"""

from .base_feed import BaseDataFeed
from .binance_feed import BinanceDataFeed

__all__ = [
    'BaseDataFeed',
    'BinanceDataFeed'
]