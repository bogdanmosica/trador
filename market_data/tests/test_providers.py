"""
Test Market Data Providers

Unit tests for market data provider implementations including
BinanceRESTProvider and MockProvider functionality.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from ..providers.binance_rest import BinanceRESTProvider
from ..providers.mock import MockProvider
from ..models import MarketDataConfig, Candle, Ticker, OrderBook, Trade


class TestBinanceRESTProvider:
    """Test cases for BinanceRESTProvider."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return MarketDataConfig(
            base_url="https://testnet.binance.vision",
            testnet=True,
            requests_per_minute=100,
            timeout_seconds=5
        )
    
    @pytest.fixture
    def provider(self, config):
        """Test provider instance."""
        return BinanceRESTProvider(config)
    
    def test_provider_initialization(self, provider):
        """Test provider initialization."""
        assert provider.config.testnet == True
        assert provider.base_url == "https://testnet.binance.vision"
        assert len(provider.INTERVAL_MAP) > 0
    
    def test_symbol_validation(self, provider):
        """Test symbol validation."""
        # Valid symbol
        normalized = provider._validate_symbol("BTCUSDT")
        assert normalized == "BTCUSDT"
        
        # Invalid symbols
        with pytest.raises(ValueError):
            provider._validate_symbol("")
        
        with pytest.raises(ValueError):
            provider._validate_symbol("BT")  # Too short
    
    def test_interval_normalization(self, provider):
        """Test interval normalization."""
        assert provider.normalize_interval("1m") == "1m"
        assert provider.normalize_interval("1h") == "1h"
        assert provider.normalize_interval("1d") == "1d"
        
        # Invalid interval
        with pytest.raises(ValueError):
            provider.normalize_interval("invalid")
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, provider):
        """Test connection and disconnection."""
        # Mock the session and exchange info
        with patch.object(provider, '_make_request') as mock_request:
            mock_request.return_value = {
                'symbols': [
                    {'symbol': 'BTCUSDT', 'status': 'TRADING'},
                    {'symbol': 'ETHUSDT', 'status': 'TRADING'}
                ]
            }
            
            await provider.connect()
            assert provider._session is not None
            assert len(provider._symbols_cache) == 2
            
            await provider.disconnect()
            assert provider._session is None
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, provider):
        """Test rate limiting functionality."""
        # Set very low rate limit for testing
        provider.config.requests_per_minute = 2
        
        start_time = asyncio.get_event_loop().time()
        
        # Make multiple requests quickly
        for _ in range(3):
            await provider._check_rate_limit()
            provider._update_rate_limit_counters()
        
        end_time = asyncio.get_event_loop().time()
        
        # Should have taken some time due to rate limiting
        assert end_time - start_time > 0.5
    
    @pytest.mark.asyncio
    async def test_get_historical_candles_mock(self, provider):
        """Test historical candles with mocked API response."""
        # Mock API response
        mock_response = [
            [
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
        ]
        
        with patch.object(provider, '_make_request', return_value=mock_response):
            candles = await provider.get_historical_candles(
                symbol="BTCUSDT",
                interval="1h",
                limit=1
            )
            
            assert len(candles) == 1
            candle = candles[0]
            assert isinstance(candle, Candle)
            assert candle.symbol == "BTCUSDT"
            assert candle.interval == "1h"
            assert candle.open == 47000.0
            assert candle.high == 47500.0
            assert candle.low == 46500.0
            assert candle.close == 47200.0
            assert candle.volume == 1000.0
    
    @pytest.mark.asyncio
    async def test_get_current_ticker_mock(self, provider):
        """Test current ticker with mocked API response."""
        mock_response = {
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
        
        with patch.object(provider, '_make_request', return_value=mock_response):
            ticker = await provider.get_current_ticker("BTCUSDT")
            
            assert isinstance(ticker, Ticker)
            assert ticker.symbol == "BTCUSDT"
            assert ticker.price == 47200.0
            assert ticker.bid == 47180.0
            assert ticker.ask == 47220.0
    
    @pytest.mark.asyncio
    async def test_get_order_book_mock(self, provider):
        """Test order book with mocked API response."""
        mock_response = {
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
        
        with patch.object(provider, '_make_request', return_value=mock_response):
            order_book = await provider.get_order_book("BTCUSDT")
            
            assert isinstance(order_book, OrderBook)
            assert order_book.symbol == "BTCUSDT"
            assert len(order_book.bids) == 2
            assert len(order_book.asks) == 2
            assert order_book.best_bid.price == 47180.0
            assert order_book.best_ask.price == 47220.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, provider):
        """Test error handling."""
        # Mock API error
        with patch.object(provider, '_make_request', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await provider.get_current_ticker("BTCUSDT")


class TestMockProvider:
    """Test cases for MockProvider."""
    
    @pytest.fixture
    def provider(self):
        """Test provider instance."""
        return MockProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initialization."""
        assert len(provider.symbols) > 0
        assert "BTCUSDT" in provider.symbols
        assert provider.base_prices["BTCUSDT"] > 0
    
    @pytest.mark.asyncio
    async def test_get_historical_candles(self, provider):
        """Test historical candles generation."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        candles = await provider.get_historical_candles(
            symbol="BTCUSDT",
            interval="1h",
            start_time=start_time,
            end_time=end_time,
            limit=24
        )
        
        assert len(candles) <= 24
        assert all(isinstance(c, Candle) for c in candles)
        assert all(c.symbol == "BTCUSDT" for c in candles)
        assert all(c.interval == "1h" for c in candles)
        
        # Check OHLC relationships
        for candle in candles:
            assert candle.low <= candle.open <= candle.high
            assert candle.low <= candle.close <= candle.high
            assert candle.volume >= 0
    
    @pytest.mark.asyncio
    async def test_get_current_ticker(self, provider):
        """Test current ticker generation."""
        ticker = await provider.get_current_ticker("BTCUSDT")
        
        assert isinstance(ticker, Ticker)
        assert ticker.symbol == "BTCUSDT"
        assert ticker.price > 0
        assert ticker.bid < ticker.ask
        assert ticker.volume_24h > 0
    
    @pytest.mark.asyncio
    async def test_get_order_book(self, provider):
        """Test order book generation."""
        order_book = await provider.get_order_book("BTCUSDT", limit=10)
        
        assert isinstance(order_book, OrderBook)
        assert order_book.symbol == "BTCUSDT"
        assert len(order_book.bids) == 10
        assert len(order_book.asks) == 10
        
        # Check bid/ask ordering
        bid_prices = [bid.price for bid in order_book.bids]
        ask_prices = [ask.price for ask in order_book.asks]
        
        assert bid_prices == sorted(bid_prices, reverse=True)  # Descending
        assert ask_prices == sorted(ask_prices)  # Ascending
        
        # Check spread
        assert order_book.best_bid.price < order_book.best_ask.price
    
    @pytest.mark.asyncio
    async def test_get_recent_trades(self, provider):
        """Test recent trades generation."""
        trades = await provider.get_recent_trades("BTCUSDT", limit=50)
        
        assert len(trades) == 50
        assert all(isinstance(t, Trade) for t in trades)
        assert all(t.symbol == "BTCUSDT" for t in trades)
        assert all(t.price > 0 for t in trades)
        assert all(t.quantity > 0 for t in trades)
        
        # Check chronological order
        timestamps = [t.timestamp for t in trades]
        assert timestamps == sorted(timestamps)
    
    @pytest.mark.asyncio
    async def test_get_supported_symbols(self, provider):
        """Test supported symbols list."""
        symbols = await provider.get_supported_symbols()
        
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "BTCUSDT" in symbols
        assert all(isinstance(s, str) for s in symbols)
    
    @pytest.mark.asyncio
    async def test_get_symbol_info(self, provider):
        """Test symbol information."""
        symbol_info = await provider.get_symbol_info("BTCUSDT")
        
        assert isinstance(symbol_info, dict)
        assert symbol_info['symbol'] == "BTCUSDT"
        assert symbol_info['status'] == "TRADING"
        assert 'baseAsset' in symbol_info
        assert 'quoteAsset' in symbol_info
    
    @pytest.mark.asyncio
    async def test_ping(self, provider):
        """Test ping functionality."""
        result = await provider.ping()
        assert result == True
    
    @pytest.mark.asyncio
    async def test_get_server_time(self, provider):
        """Test server time retrieval."""
        server_time = await provider.get_server_time()
        
        assert isinstance(server_time, datetime)
        assert server_time.tzinfo == timezone.utc
    
    def test_interval_to_seconds(self, provider):
        """Test interval conversion."""
        assert provider._interval_to_seconds("1m") == 60
        assert provider._interval_to_seconds("1h") == 3600
        assert provider._interval_to_seconds("1d") == 86400
    
    @pytest.mark.asyncio
    async def test_consistent_data_generation(self, provider):
        """Test that generated data is consistent."""
        # Get initial price
        ticker1 = await provider.get_current_ticker("BTCUSDT")
        initial_price = ticker1.price
        
        # Get price again (should be close but may have small changes)
        ticker2 = await provider.get_current_ticker("BTCUSDT")
        price_diff = abs(ticker2.price - initial_price) / initial_price
        
        # Should be within reasonable range (small random walk)
        assert price_diff < 0.1  # Less than 10% change
    
    @pytest.mark.asyncio
    async def test_candle_sequence_consistency(self, provider):
        """Test that candle sequences are consistent."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=5)
        
        candles = await provider.get_historical_candles(
            symbol="BTCUSDT",
            interval="1h",
            start_time=start_time,
            end_time=end_time
        )
        
        # Check that each candle's open matches previous candle's close
        for i in range(1, len(candles)):
            # Allow small differences due to random generation
            price_diff = abs(candles[i].open - candles[i-1].close)
            assert price_diff < candles[i-1].close * 0.01  # Less than 1% difference


class TestProviderInterface:
    """Test common provider interface compliance."""
    
    @pytest.mark.asyncio
    async def test_mock_provider_interface(self):
        """Test that MockProvider implements the interface correctly."""
        provider = MockProvider()
        
        # Test all required methods exist and are callable
        assert hasattr(provider, 'get_historical_candles')
        assert hasattr(provider, 'get_current_ticker')
        assert hasattr(provider, 'get_order_book')
        assert hasattr(provider, 'get_recent_trades')
        assert hasattr(provider, 'get_supported_symbols')
        assert hasattr(provider, 'get_symbol_info')
        assert hasattr(provider, 'ping')
        
        # Test that methods return correct types
        candles = await provider.get_historical_candles("BTCUSDT", "1h", limit=1)
        assert isinstance(candles, list)
        
        ticker = await provider.get_current_ticker("BTCUSDT")
        assert isinstance(ticker, Ticker)
        
        order_book = await provider.get_order_book("BTCUSDT")
        assert isinstance(order_book, OrderBook)
        
        trades = await provider.get_recent_trades("BTCUSDT", limit=1)
        assert isinstance(trades, list)
        
        symbols = await provider.get_supported_symbols()
        assert isinstance(symbols, list)
        
        symbol_info = await provider.get_symbol_info("BTCUSDT")
        assert isinstance(symbol_info, dict)
        
        ping_result = await provider.ping()
        assert isinstance(ping_result, bool)


if __name__ == "__main__":
    pytest.main([__file__])