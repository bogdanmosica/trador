"""
Test Core Data Models

Unit tests for backtest data models including Order, Trade, Portfolio states,
and configuration objects. Validates data integrity and business logic.
"""

import pytest
from datetime import datetime, timezone
import uuid

from ..models import (
    Order, Trade, OrderType, OrderStatus, TimeInForce,
    PositionState, MarketSnapshot, BacktestConfig
)


class TestOrder:
    """Test cases for Order model."""
    
    def test_order_creation(self):
        """Test basic order creation."""
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert order.symbol == "BTCUSDT"
        assert order.side == "BUY"
        assert order.is_buy
        assert not order.is_sell
        assert order.quantity == 1.0
        assert order.remaining_quantity == 1.0
        assert order.status == OrderStatus.PENDING
        assert order.is_active
        assert not order.is_filled
    
    def test_order_properties(self):
        """Test order property methods."""
        # Buy order
        buy_order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc),
            limit_price=50000.0
        )
        
        assert buy_order.is_buy
        assert not buy_order.is_sell
        
        # Sell order
        sell_order = Order(
            symbol="BTCUSDT",
            side="SELL",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert sell_order.is_sell
        assert not sell_order.is_buy
    
    def test_order_status_changes(self):
        """Test order status transitions."""
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Initial state
        assert order.status == OrderStatus.PENDING
        assert order.is_active
        assert not order.is_filled
        assert not order.is_partial_filled
        
        # Partial fill
        order.status = OrderStatus.PARTIAL_FILLED
        order.filled_quantity = 0.5
        order.remaining_quantity = 0.5
        
        assert order.is_partial_filled
        assert order.is_active
        assert not order.is_filled
        
        # Complete fill
        order.status = OrderStatus.FILLED
        order.filled_quantity = 1.0
        order.remaining_quantity = 0.0
        
        assert order.is_filled
        assert not order.is_active
        assert not order.is_partial_filled
    
    def test_order_id_generation(self):
        """Test that orders get unique IDs."""
        order1 = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        order2 = Order(
            symbol="BTCUSDT",
            side="SELL",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert order1.order_id != order2.order_id
        assert len(order1.order_id) > 0
        assert len(order2.order_id) > 0


class TestTrade:
    """Test cases for Trade model."""
    
    def test_trade_creation(self):
        """Test basic trade creation."""
        trade = Trade(
            trade_id="trade123",
            order_id="order456",
            symbol="BTCUSDT",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            fees=50.0
        )
        
        assert trade.trade_id == "trade123"
        assert trade.order_id == "order456"
        assert trade.symbol == "BTCUSDT"
        assert trade.side == "BUY"
        assert trade.quantity == 1.0
        assert trade.price == 50000.0
        assert trade.fees == 50.0
    
    def test_trade_calculations(self):
        """Test trade value calculations."""
        # Buy trade
        buy_trade = Trade(
            trade_id="trade1",
            order_id="order1",
            symbol="BTCUSDT",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            fees=50.0
        )
        
        assert buy_trade.notional_value == 50000.0
        assert buy_trade.net_value == -50050.0  # Negative for buy (cash outflow)
        
        # Sell trade
        sell_trade = Trade(
            trade_id="trade2",
            order_id="order2",
            symbol="BTCUSDT",
            side="SELL",
            quantity=1.0,
            price=55000.0,
            timestamp=datetime.now(timezone.utc),
            fees=55.0
        )
        
        assert sell_trade.notional_value == 55000.0
        assert sell_trade.net_value == 54945.0  # Positive for sell (cash inflow)


class TestPositionState:
    """Test cases for PositionState model."""
    
    def test_position_creation(self):
        """Test position state creation."""
        position = PositionState(
            symbol="BTCUSDT",
            quantity=1.0,
            average_entry_price=50000.0,
            entry_time=datetime.now(timezone.utc)
        )
        
        assert position.symbol == "BTCUSDT"
        assert position.quantity == 1.0
        assert position.average_entry_price == 50000.0
        assert position.notional_value == 50000.0
    
    def test_position_direction_properties(self):
        """Test position direction properties."""
        # Long position
        long_position = PositionState(
            symbol="BTCUSDT",
            quantity=1.0,
            average_entry_price=50000.0,
            entry_time=datetime.now(timezone.utc)
        )
        
        assert long_position.is_long
        assert not long_position.is_short
        assert not long_position.is_flat
        
        # Short position
        short_position = PositionState(
            symbol="BTCUSDT",
            quantity=-1.0,
            average_entry_price=50000.0,
            entry_time=datetime.now(timezone.utc)
        )
        
        assert not short_position.is_long
        assert short_position.is_short
        assert not short_position.is_flat
        
        # Flat position
        flat_position = PositionState(
            symbol="BTCUSDT",
            quantity=0.0,
            average_entry_price=50000.0,
            entry_time=datetime.now(timezone.utc)
        )
        
        assert not flat_position.is_long
        assert not flat_position.is_short
        assert flat_position.is_flat


class TestMarketSnapshot:
    """Test cases for MarketSnapshot model."""
    
    def test_market_snapshot_creation(self):
        """Test market snapshot creation."""
        snapshot = MarketSnapshot(
            timestamp=datetime.now(timezone.utc),
            symbol="BTCUSDT",
            open=49000.0,
            high=51000.0,
            low=48000.0,
            close=50000.0,
            volume=1000.0,
            timeframe="1h"
        )
        
        assert snapshot.symbol == "BTCUSDT"
        assert snapshot.open == 49000.0
        assert snapshot.high == 51000.0
        assert snapshot.low == 48000.0
        assert snapshot.close == 50000.0
        assert snapshot.volume == 1000.0
        assert snapshot.timeframe == "1h"
    
    def test_bid_ask_estimation(self):
        """Test automatic bid/ask price estimation."""
        snapshot = MarketSnapshot(
            timestamp=datetime.now(timezone.utc),
            symbol="BTCUSDT",
            open=49000.0,
            high=51000.0,
            low=48000.0,
            close=50000.0,
            volume=1000.0,
            timeframe="1h"
        )
        
        # Should auto-generate bid/ask around close price
        assert snapshot.bid is not None
        assert snapshot.ask is not None
        assert snapshot.spread is not None
        assert snapshot.bid < snapshot.close < snapshot.ask
        assert snapshot.spread == snapshot.ask - snapshot.bid
    
    def test_explicit_bid_ask(self):
        """Test explicit bid/ask specification."""
        snapshot = MarketSnapshot(
            timestamp=datetime.now(timezone.utc),
            symbol="BTCUSDT",
            open=49000.0,
            high=51000.0,
            low=48000.0,
            close=50000.0,
            volume=1000.0,
            timeframe="1h",
            bid=49950.0,
            ask=50050.0
        )
        
        assert snapshot.bid == 49950.0
        assert snapshot.ask == 50050.0
        assert snapshot.spread == 100.0


class TestBacktestConfig:
    """Test cases for BacktestConfig model."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = BacktestConfig()
        
        assert config.maker_fee == 0.001
        assert config.taker_fee == 0.001
        assert config.market_order_slippage == 0.0005
        assert config.limit_order_slippage == 0.0
        assert config.execution_latency_ms == 250
        assert config.initial_balance == 10000.0
        assert config.base_currency == "USDT"
        assert config.max_leverage == 1.0
        assert config.cache_data
    
    def test_config_customization(self):
        """Test custom configuration values."""
        config = BacktestConfig(
            maker_fee=0.0005,
            taker_fee=0.0015,
            initial_balance=50000.0,
            base_currency="USD",
            max_leverage=3.0
        )
        
        assert config.maker_fee == 0.0005
        assert config.taker_fee == 0.0015
        assert config.initial_balance == 50000.0
        assert config.base_currency == "USD"
        assert config.max_leverage == 3.0
    
    def test_config_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = BacktestConfig(
            maker_fee=0.0005,
            initial_balance=25000.0
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['maker_fee'] == 0.0005
        assert config_dict['initial_balance'] == 25000.0
        assert 'taker_fee' in config_dict
        assert 'base_currency' in config_dict


class TestEnums:
    """Test cases for enum types."""
    
    def test_order_type_enum(self):
        """Test OrderType enum values."""
        assert OrderType.MARKET.value == "MARKET"
        assert OrderType.LIMIT.value == "LIMIT"
        assert OrderType.STOP_MARKET.value == "STOP_MARKET"
        assert OrderType.STOP_LIMIT.value == "STOP_LIMIT"
    
    def test_order_status_enum(self):
        """Test OrderStatus enum values."""
        assert OrderStatus.PENDING.value == "PENDING"
        assert OrderStatus.PARTIAL_FILLED.value == "PARTIAL_FILLED"
        assert OrderStatus.FILLED.value == "FILLED"
        assert OrderStatus.CANCELLED.value == "CANCELLED"
        assert OrderStatus.REJECTED.value == "REJECTED"
    
    def test_time_in_force_enum(self):
        """Test TimeInForce enum values."""
        assert TimeInForce.GTC.value == "GTC"
        assert TimeInForce.IOC.value == "IOC"
        assert TimeInForce.FOK.value == "FOK"
        assert TimeInForce.DAY.value == "DAY"


if __name__ == "__main__":
    pytest.main([__file__])