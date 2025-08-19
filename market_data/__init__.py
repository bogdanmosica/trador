"""
Market Data Layer

Modular, API-based market data system for crypto trading bots.
Supports both historical data fetching and live streaming with
unified data formats and pluggable providers.
"""

from .models import Candle, Ticker, OrderBook, Trade as MarketTrade
from .providers.base import MarketDataProvider
from .providers.binance_rest import BinanceRESTProvider
from .providers.mock import MockProvider
from .streaming.data_stream import DataStream, StreamConfig

__all__ = [
    'Candle',
    'Ticker', 
    'OrderBook',
    'MarketTrade',
    'MarketDataProvider',
    'BinanceRESTProvider',
    'MockProvider',
    'DataStream',
    'StreamConfig'
]