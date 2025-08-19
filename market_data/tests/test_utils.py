"""
Test Market Data Utilities

Unit tests for data normalization, validation, and conversion utilities.
Tests data quality checks and format transformations.
"""

import pytest
import pandas as pd
from datetime import datetime, timezone
import json

from ..utils.normalizer import DataNormalizer
from ..utils.validator import DataValidator
from ..utils.converter import DataConverter
from ..models import Candle, Ticker, OrderBook, OrderBookLevel, Trade


class TestDataNormalizer:
    """Test cases for DataNormalizer."""
    
    def test_normalize_binance_kline(self):
        """Test Binance kline normalization."""
        kline_data = [
            1640995200000,  # Open time
            "47000.0",      # Open
            "47500.0",      # High
            "46500.0",      # Low
            "47200.0",      # Close
            "1000.0",       # Volume
            1640998799999,  # Close time
            "47200000.0",   # Quote volume
            100,            # Trade count
            "500.0",        # Taker buy base volume
            "23600000.0"    # Taker buy quote volume
        ]
        
        candle = DataNormalizer.normalize_binance_kline(
            kline_data, "BTCUSDT", "1h"
        )
        
        assert isinstance(candle, Candle)
        assert candle.symbol == "BTCUSDT"
        assert candle.interval == "1h"
        assert candle.timestamp == 1640995200000
        assert candle.open == 47000.0
        assert candle.high == 47500.0
        assert candle.low == 46500.0
        assert candle.close == 47200.0
        assert candle.volume == 1000.0
        assert candle.quote_volume == 47200000.0
        assert candle.trade_count == 100
    
    def test_normalize_binance_ticker(self):
        """Test Binance ticker normalization."""
        ticker_data = {
            'symbol': 'BTCUSDT',
            'lastPrice': '47200.0',
            'bidPrice': '47180.0',
            'askPrice': '47220.0',
            'bidQty': '1.5',
            'askQty': '2.0',
            'volume': '50000.0',
            'priceChange': '200.0',
            'priceChangePercent': '0.42',
            'highPrice': '47500.0',
            'lowPrice': '46500.0',
            'openPrice': '47000.0',
            'quoteVolume': '2360000000.0',
            'closeTime': 1640995200000
        }
        
        ticker = DataNormalizer.normalize_binance_ticker(ticker_data)
        
        assert isinstance(ticker, Ticker)
        assert ticker.symbol == "BTCUSDT"
        assert ticker.price == 47200.0
        assert ticker.bid == 47180.0
        assert ticker.ask == 47220.0
        assert ticker.volume_24h == 50000.0
    
    def test_normalize_binance_depth(self):
        """Test Binance depth normalization."""
        depth_data = {
            'lastUpdateId': 12345,
            'bids': [
                ['47180.0', '1.5'],
                ['47170.0', '2.0']
            ],
            'asks': [
                ['47220.0', '1.2'],
                ['47230.0', '2.5']
            ]
        }
        
        order_book = DataNormalizer.normalize_binance_depth(depth_data, "BTCUSDT")
        
        assert isinstance(order_book, OrderBook)
        assert order_book.symbol == "BTCUSDT"
        assert len(order_book.bids) == 2
        assert len(order_book.asks) == 2
        assert order_book.last_update_id == 12345
    
    def test_normalize_websocket_kline(self):
        """Test WebSocket kline normalization."""
        ws_data = {
            'k': {
                't': 1640995200000,  # Open time
                's': 'BTCUSDT',      # Symbol
                'i': '1h',           # Interval
                'o': '47000.0',      # Open
                'h': '47500.0',      # High
                'l': '46500.0',      # Low
                'c': '47200.0',      # Close
                'v': '1000.0',       # Volume
                'q': '47200000.0',   # Quote volume
                'n': 100,            # Trade count
                'V': '500.0',        # Taker buy volume
                'Q': '23600000.0'    # Taker buy quote volume
            }
        }
        
        candle = DataNormalizer.normalize_websocket_kline(ws_data)
        
        assert isinstance(candle, Candle)
        assert candle.symbol == "BTCUSDT"
        assert candle.interval == "1h"
        assert candle.open == 47000.0
        assert candle.close == 47200.0
    
    def test_fill_missing_candle_data(self):
        """Test filling missing candle data."""
        candle = Candle(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            interval="1h",
            open=47000.0,
            high=47500.0,
            low=46500.0,
            close=47200.0,
            volume=1000.0
            # Missing: quote_volume, trade_count, taker_buy_volume, taker_buy_quote_volume
        )
        
        filled_candle = DataNormalizer.fill_missing_candle_data(candle)
        
        assert filled_candle.quote_volume is not None
        assert filled_candle.trade_count is not None
        assert filled_candle.taker_buy_volume is not None
        assert filled_candle.taker_buy_quote_volume is not None
        
        # Check reasonable estimates
        avg_price = (candle.open + candle.high + candle.low + candle.close) / 4
        expected_quote_volume = candle.volume * avg_price
        assert abs(filled_candle.quote_volume - expected_quote_volume) < 0.01
    
    def test_normalize_symbol_format(self):
        """Test symbol format normalization."""
        # Test different input formats
        assert DataNormalizer.normalize_symbol_format("BTC-USDT") == "BTCUSDT"
        assert DataNormalizer.normalize_symbol_format("BTC_USDT") == "BTCUSDT"
        assert DataNormalizer.normalize_symbol_format("BTC/USDT") == "BTCUSDT"
        assert DataNormalizer.normalize_symbol_format("btcusdt") == "BTCUSDT"
        
        # Test provider-specific formats
        assert DataNormalizer.normalize_symbol_format("BTCUSDT", "binance") == "BTCUSDT"
        assert DataNormalizer.normalize_symbol_format("BTCUSD", "coinbase") == "BTC-USD"
    
    def test_normalize_interval_format(self):
        """Test interval format normalization."""
        # Test common mappings
        assert DataNormalizer.normalize_interval_format("1min") == "1m"
        assert DataNormalizer.normalize_interval_format("1hour") == "1h"
        assert DataNormalizer.normalize_interval_format("1day") == "1d"
        
        # Test provider-specific formats
        assert DataNormalizer.normalize_interval_format("1h", "binance") == "1h"
        assert DataNormalizer.normalize_interval_format("1h", "coinbase") == "3600"


class TestDataValidator:
    """Test cases for DataValidator."""
    
    @pytest.fixture
    def validator(self):
        """Test validator instance."""
        return DataValidator()
    
    def test_validate_candle_sequence_valid(self, validator):
        """Test validation of valid candle sequence."""
        candles = [
            Candle(
                timestamp=1640995200000 + i * 3600000,  # Hourly intervals
                symbol="BTCUSDT",
                interval="1h",
                open=47000.0 + i * 10,
                high=47100.0 + i * 10,
                low=46900.0 + i * 10,
                close=47050.0 + i * 10,
                volume=1000.0
            )
            for i in range(5)
        ]
        
        result = validator.validate_candle_sequence(candles)
        
        assert result['valid'] == True
        assert len(result['issues']) == 0
        assert result['statistics']['total_candles'] == 5
        assert result['statistics']['invalid_candles'] == 0
    
    def test_validate_candle_sequence_chronological_issue(self, validator):
        """Test validation with chronological order issues."""
        candles = [
            Candle(
                timestamp=1640995200000,
                symbol="BTCUSDT",
                interval="1h",
                open=47000.0,
                high=47100.0,
                low=46900.0,
                close=47050.0,
                volume=1000.0
            ),
            Candle(
                timestamp=1640991600000,  # Earlier timestamp (invalid)
                symbol="BTCUSDT",
                interval="1h",
                open=47050.0,
                high=47150.0,
                low=46950.0,
                close=47100.0,
                volume=1000.0
            )
        ]
        
        result = validator.validate_candle_sequence(candles)
        
        assert result['valid'] == False
        assert any("chronological" in issue.lower() for issue in result['issues'])
    
    def test_validate_ticker_data_valid(self, validator):
        """Test validation of valid ticker data."""
        tickers = [
            Ticker(
                timestamp=1640995200000,
                symbol="BTCUSDT",
                price=47200.0,
                bid=47180.0,
                ask=47220.0
            ),
            Ticker(
                timestamp=1640995260000,
                symbol="BTCUSDT",
                price=47250.0,
                bid=47230.0,
                ask=47270.0
            )
        ]
        
        result = validator.validate_ticker_data(tickers)
        
        assert result['valid'] == True
        assert len(result['issues']) == 0
        assert result['statistics']['total_tickers'] == 2
    
    def test_validate_order_book_valid(self, validator):
        """Test validation of valid order book."""
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
        
        result = validator.validate_order_book(order_book)
        
        assert result['valid'] == True
        assert len(result['issues']) == 0
        assert result['statistics']['bid_levels'] == 3
        assert result['statistics']['ask_levels'] == 3
    
    def test_validate_order_book_invalid_spread(self, validator):
        """Test validation of order book with invalid spread."""
        bids = [OrderBookLevel(47220.0, 1.5)]  # Bid > Ask
        asks = [OrderBookLevel(47180.0, 1.2)]
        
        order_book = OrderBook(
            timestamp=1640995200000,
            symbol="BTCUSDT",
            bids=bids,
            asks=asks
        )
        
        result = validator.validate_order_book(order_book)
        
        assert result['valid'] == False
        assert any("spread" in issue.lower() for issue in result['issues'])
    
    def test_detect_outliers(self, validator):
        """Test outlier detection."""
        # Create candles with one outlier
        candles = [
            Candle(
                timestamp=1640995200000 + i * 3600000,
                symbol="BTCUSDT",
                interval="1h",
                open=47000.0,
                high=47100.0,
                low=46900.0,
                close=47000.0 if i != 2 else 50000.0,  # Outlier at index 2
                volume=1000.0
            )
            for i in range(10)
        ]
        
        outliers = validator.detect_outliers(candles, field='close')
        
        assert 2 in outliers  # Should detect the outlier at index 2
    
    def test_validate_trade_sequence(self, validator):
        """Test trade sequence validation."""
        trades = [
            Trade(
                timestamp=1640995200000 + i * 1000,
                symbol="BTCUSDT",
                trade_id=str(i),
                price=47200.0 + i,
                quantity=1.0,
                side="buy" if i % 2 == 0 else "sell"
            )
            for i in range(5)
        ]
        
        result = validator.validate_trade_sequence(trades)
        
        assert result['valid'] == True
        assert result['statistics']['total_trades'] == 5
        assert result['statistics']['buy_trades'] == 3
        assert result['statistics']['sell_trades'] == 2


class TestDataConverter:
    """Test cases for DataConverter."""
    
    def test_candles_to_dataframe(self):
        """Test candles to DataFrame conversion."""
        candles = [
            Candle(
                timestamp=1640995200000 + i * 3600000,
                symbol="BTCUSDT",
                interval="1h",
                open=47000.0 + i,
                high=47100.0 + i,
                low=46900.0 + i,
                close=47050.0 + i,
                volume=1000.0
            )
            for i in range(3)
        ]
        
        df = DataConverter.candles_to_dataframe(candles)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert isinstance(df.index, pd.DatetimeIndex)
    
    def test_dataframe_to_candles(self):
        """Test DataFrame to candles conversion."""
        # Create test DataFrame
        data = {
            'open': [47000.0, 47010.0, 47020.0],
            'high': [47100.0, 47110.0, 47120.0],
            'low': [46900.0, 46910.0, 46920.0],
            'close': [47050.0, 47060.0, 47070.0],
            'volume': [1000.0, 1100.0, 1200.0],
            'timestamp': [1640995200000, 1640998800000, 1641002400000]
        }
        
        df = pd.DataFrame(data)
        candles = DataConverter.dataframe_to_candles(df, "BTCUSDT", "1h")
        
        assert len(candles) == 3
        assert all(isinstance(c, Candle) for c in candles)
        assert all(c.symbol == "BTCUSDT" for c in candles)
        assert all(c.interval == "1h" for c in candles)
        assert candles[0].open == 47000.0
        assert candles[1].open == 47010.0
    
    def test_candles_to_ohlcv(self):
        """Test candles to OHLCV conversion."""
        candles = [
            Candle(
                timestamp=1640995200000,
                symbol="BTCUSDT",
                interval="1h",
                open=47000.0,
                high=47100.0,
                low=46900.0,
                close=47050.0,
                volume=1000.0
            ),
            Candle(
                timestamp=1640998800000,
                symbol="BTCUSDT",
                interval="1h",
                open=47050.0,
                high=47150.0,
                low=46950.0,
                close=47100.0,
                volume=1100.0
            )
        ]
        
        ohlcv = DataConverter.candles_to_ohlcv(candles)
        
        assert 'open' in ohlcv
        assert 'high' in ohlcv
        assert 'low' in ohlcv
        assert 'close' in ohlcv
        assert 'volume' in ohlcv
        assert len(ohlcv['open']) == 2
        assert ohlcv['open'] == [47000.0, 47050.0]
        assert ohlcv['high'] == [47100.0, 47150.0]
    
    def test_order_book_to_arrays(self):
        """Test order book to arrays conversion."""
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
        
        arrays = DataConverter.order_book_to_arrays(order_book)
        
        assert 'bids' in arrays
        assert 'asks' in arrays
        assert 'spread' in arrays
        assert 'mid_price' in arrays
        assert arrays['bids']['prices'] == [47180.0, 47170.0]
        assert arrays['asks']['prices'] == [47220.0, 47230.0]
    
    def test_candles_to_json(self):
        """Test candles to JSON conversion."""
        candles = [
            Candle(
                timestamp=1640995200000,
                symbol="BTCUSDT",
                interval="1h",
                open=47000.0,
                high=47100.0,
                low=46900.0,
                close=47050.0,
                volume=1000.0
            )
        ]
        
        json_str = DataConverter.candles_to_json(candles)
        
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['symbol'] == "BTCUSDT"
        assert data[0]['open'] == 47000.0
    
    def test_merge_candles(self):
        """Test merging candle lists."""
        candles1 = [
            Candle(
                timestamp=1640995200000,
                symbol="BTCUSDT",
                interval="1h",
                open=47000.0,
                high=47100.0,
                low=46900.0,
                close=47050.0,
                volume=1000.0
            )
        ]
        
        candles2 = [
            Candle(
                timestamp=1640998800000,
                symbol="BTCUSDT",
                interval="1h",
                open=47050.0,
                high=47150.0,
                low=46950.0,
                close=47100.0,
                volume=1100.0
            )
        ]
        
        merged = DataConverter.merge_candles(candles1, candles2)
        
        assert len(merged) == 2
        assert merged[0].timestamp < merged[1].timestamp  # Should be sorted


if __name__ == "__main__":
    pytest.main([__file__])