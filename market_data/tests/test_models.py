"""
Test Market Data Models

Unit tests for core market data models including Candle, Ticker,
OrderBook, and Trade data structures with validation.
"""

import pytest
from datetime import datetime, timezone
import json

from ..models import (
    Candle, Ticker, OrderBook, OrderBookLevel, Trade,
    MarketDataConfig, validate_candle, validate_ticker
)


class TestCandle:
    """Test cases for Candle model."""
    
    def test_candle_creation(self):
        """Test basic candle creation."""
        candle = Candle(
            timestamp=1640995200000,  # 2022-01-01 00:00:00 UTC
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=1000.0
        )
        
        assert candle.symbol == "BTCUSDT"
        assert candle.interval == "1h"
        assert candle.open == 47000.0
        assert candle.high == 47500.0
        assert candle.low == 46500.0
        assert candle.close == 47200.0
        assert candle.volume == 1000.0
    
    def test_candle_properties(self):
        """Test candle calculated properties."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=1000.0
        )
        
        # Test datetime conversion
        expected_datetime = datetime.fromtimestamp(1640995200)
        assert candle.datetime.replace(tzinfo=None) == expected_datetime
        
        # Test price calculations
        assert candle.price_change == 200.0  # 47200 - 47000
        assert abs(candle.price_change_percent - 0.4255) < 0.001  # 200/47000 * 100
        assert candle.typical_price == (47500.0 + 46500.0 + 47200.0) / 3
        assert candle.weighted_price == (47500.0 + 46500.0 + 47200.0 * 2) / 4
    
    def test_candle_to_dict(self):
        """Test candle to dictionary conversion."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=1000.0
        )
        
        candle_dict = candle.to_dict()
        
        assert candle_dict['symbol'] == "BTCUSDT"
        assert candle_dict['open'] == 47000.0
        assert candle_dict['price_change'] == 200.0
        assert 'timestamp' in candle_dict
    
    def test_candle_from_dict(self):
        """Test candle creation from dictionary."""
        data = {
            'timestamp': 1640995200000,
            'symbol': 'BTCUSDT',
            'interval': '1h',
            'open': 47000.0,
            'high': 47500.0,
            'low': 46500.0,
            'close': 47200.0,
            'volume': 1000.0
        }
        
        candle = Candle.from_dict(data)
        
        assert candle.symbol == "BTCUSDT"
        assert candle.open == 47000.0
        assert candle.close == 47200.0
    
    def test_candle_json_serialization(self):
        """Test JSON serialization."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=1000.0
        )
        
        json_str = candle.to_json()
        data = json.loads(json_str)
        
        assert data['symbol'] == "BTCUSDT"
        assert data['open'] == 47000.0


class TestTicker:
    """Test cases for Ticker model."""
    
    def test_ticker_creation(self):
        """Test basic ticker creation."""
        ticker = Ticker(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            price=47200.0,
            bid=47180.0,
            ask=47220.0,
            volume_24h=50000.0
        )
        
        assert ticker.symbol == "BTCUSDT"
        assert ticker.price == 47200.0
        assert ticker.bid == 47180.0
        assert ticker.ask == 47220.0
    
    def test_ticker_properties(self):
        """Test ticker calculated properties."""
        ticker = Ticker(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            price=47200.0,
            bid=47180.0,
            ask=47220.0
        )
        
        # Test spread calculations
        assert ticker.spread == 40.0  # 47220 - 47180
        mid_price = (47180.0 + 47220.0) / 2
        expected_spread_percent = (40.0 / mid_price) * 100
        assert abs(ticker.spread_percent - expected_spread_percent) < 0.001
    
    def test_ticker_to_dict(self):
        """Test ticker to dictionary conversion."""
        ticker = Ticker(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            price=47200.0,
            bid=47180.0,
            ask=47220.0
        )
        
        ticker_dict = ticker.to_dict()
        
        assert ticker_dict['symbol'] == "BTCUSDT"
        assert ticker_dict['price'] == 47200.0
        assert ticker_dict['spread'] == 40.0


class TestOrderBook:
    """Test cases for OrderBook model."""
    
    def test_order_book_creation(self):
        """Test basic order book creation."""
        bids = [
            OrderBookLevel(47180.0, 1.5),
            OrderBookLevel(47170.0, 2.0),
            OrderBookLevel(47160.0, 1.8)
        ]
        
        asks = [
            OrderBookLevel(47220.0, 1.2),
            OrderBookLevel(47230.0, 2.5),
            OrderBookLevel(47240.0, 1.7)
        ]
        
        order_book = OrderBook(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            bids=bids,
            asks=asks
        )
        
        assert order_book.symbol == "BTCUSDT"
        assert len(order_book.bids) == 3
        assert len(order_book.asks) == 3
    
    def test_order_book_properties(self):
        """Test order book calculated properties."""
        bids = [
            OrderBookLevel(47180.0, 1.5),
            OrderBookLevel(47170.0, 2.0)
        ]
        
        asks = [
            OrderBookLevel(47220.0, 1.2),
            OrderBookLevel(47230.0, 2.5)
        ]
        
        order_book = OrderBook(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            bids=bids,
            asks=asks
        )
        
        # Test best bid/ask
        assert order_book.best_bid.price == 47180.0
        assert order_book.best_ask.price == 47220.0
        
        # Test spread and mid price
        assert order_book.spread == 40.0  # 47220 - 47180
        assert order_book.mid_price == 47200.0  # (47180 + 47220) / 2
        
        # Test depth calculations
        bid_depth = order_book.get_bid_depth(2)
        ask_depth = order_book.get_ask_depth(2)
        assert bid_depth == 3.5  # 1.5 + 2.0
        assert ask_depth == 3.7  # 1.2 + 2.5
    
    def test_order_book_imbalance(self):
        """Test order book imbalance calculation."""
        bids = [OrderBookLevel(47180.0, 3.0)]
        asks = [OrderBookLevel(47220.0, 1.0)]
        
        order_book = OrderBook(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            bids=bids,
            asks=asks
        )
        
        imbalance = order_book.get_imbalance_ratio(1)
        assert imbalance == 0.75  # 3.0 / (3.0 + 1.0)


class TestOrderBookLevel:
    """Test cases for OrderBookLevel model."""
    
    def test_order_book_level_creation(self):
        """Test order book level creation."""
        level = OrderBookLevel(47200.0, 1.5)
        
        assert level.price == 47200.0
        assert level.quantity == 1.5
        assert level.notional_value == 70800.0  # 47200 * 1.5


class TestTrade:
    """Test cases for Trade model."""
    
    def test_trade_creation(self):
        """Test basic trade creation."""
        trade = Trade(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            trade_id="12345",
            price=47200.0,
            quantity=1.5,
            side="buy"
        )
        
        assert trade.symbol == "BTCUSDT"
        assert trade.trade_id == "12345"
        assert trade.price == 47200.0
        assert trade.quantity == 1.5
        assert trade.side == "buy"
    
    def test_trade_properties(self):
        """Test trade calculated properties."""
        trade = Trade(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            trade_id="12345",
            price=47200.0,
            quantity=1.5,
            side="buy"
        )
        
        # Test datetime conversion
        expected_datetime = datetime.fromtimestamp(1640995200)
        assert trade.datetime.replace(tzinfo=None) == expected_datetime
        
        # Test notional value
        assert trade.notional_value == 70800.0  # 47200 * 1.5
    
    def test_trade_to_dict(self):
        """Test trade to dictionary conversion."""
        trade = Trade(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            trade_id="12345",
            price=47200.0,
            quantity=1.5,
            side="buy"
        )
        
        trade_dict = trade.to_dict()
        
        assert trade_dict['symbol'] == "BTCUSDT"
        assert trade_dict['trade_id'] == "12345"
        assert trade_dict['notional_value'] == 70800.0


class TestMarketDataConfig:
    """Test cases for MarketDataConfig model."""
    
    def test_config_creation(self):
        """Test basic config creation."""
        config = MarketDataConfig(
            base_url="https://api.binance.com",
            requests_per_minute=1200,
            timeout_seconds=10
        )
        
        assert config.base_url == "https://api.binance.com"
        assert config.requests_per_minute == 1200
        assert config.timeout_seconds == 10
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = MarketDataConfig(base_url="https://api.example.com")
        
        assert config.requests_per_minute == 1200
        assert config.timeout_seconds == 10
        assert config.max_retries == 3
        assert config.enable_cache == True
    
    def test_config_to_dict(self):
        """Test config to dictionary conversion."""
        config = MarketDataConfig(
            base_url="https://api.binance.com",
            requests_per_minute=1000
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['base_url'] == "https://api.binance.com"
        assert config_dict['requests_per_minute'] == 1000
        assert 'timeout_seconds' in config_dict


class TestValidation:
    """Test cases for data validation functions."""
    
    def test_validate_candle_valid(self):
        """Test validation of valid candle."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=1000.0
        )
        
        assert validate_candle(candle) == True
    
    def test_validate_candle_invalid_ohlc(self):
        """Test validation of candle with invalid OHLC relationships."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=46000.0,  # High < Open (invalid)
            low=46500.0,
            close=47200.0,
            volume=1000.0
        )
        
        assert validate_candle(candle) == False
    
    def test_validate_candle_negative_price(self):
        """Test validation of candle with negative prices."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=-47000.0,  # Negative price (invalid)
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=1000.0
        )
        
        assert validate_candle(candle) == False
    
    def test_validate_candle_negative_volume(self):
        """Test validation of candle with negative volume."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=-1000.0  # Negative volume (invalid)
        )
        
        assert validate_candle(candle) == False
    
    def test_validate_ticker_valid(self):
        """Test validation of valid ticker."""
        ticker = Ticker(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            price=47200.0,
            bid=47180.0,
            ask=47220.0
        )
        
        assert validate_ticker(ticker) == True
    
    def test_validate_ticker_invalid_spread(self):
        """Test validation of ticker with invalid spread."""
        ticker = Ticker(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            price=47200.0,
            bid=47220.0,  # Bid > Ask (invalid)
            ask=47180.0
        )
        
        assert validate_ticker(ticker) == False
    
    def test_validate_ticker_negative_price(self):
        """Test validation of ticker with negative price."""
        ticker = Ticker(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            price=-47200.0  # Negative price (invalid)
        )
        
        assert validate_ticker(ticker) == False


if __name__ == "__main__":
    pytest.main([__file__])