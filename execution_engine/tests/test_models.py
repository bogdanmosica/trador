"""
Test Execution Engine Models

Unit tests for core execution engine models including Signal, Order,
Fill, and configuration classes with comprehensive validation tests.
"""

import pytest
from datetime import datetime, timezone
import json

from ..models import (
    Signal, Order, Fill, OrderSide, OrderType, OrderStatus, 
    TimeInForce, ExecutionConfig, validate_signal, validate_order
)


class TestSignal:
    """Test cases for Signal model."""
    
    def test_signal_creation(self):
        """Test basic signal creation."""
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            timestamp=1640995200000,
            order_type=OrderType.MARKET
        )
        
        assert signal.symbol == "BTCUSDT"
        assert signal.side == OrderSide.BUY
        assert signal.quantity == 1.0
        assert signal.order_type == OrderType.MARKET
        assert signal.strategy_id == "default"
    
    def test_signal_validation(self):
        """Test signal validation."""
        # Valid signal
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            timestamp=1640995200000
        )
        assert validate_signal(signal) == True
        
        # Invalid quantity
        with pytest.raises(ValueError):
            Signal(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                quantity=0.0,  # Invalid
                timestamp=1640995200000
            )
    
    def test_limit_order_signal(self):
        """Test limit order signal creation."""
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            timestamp=1640995200000,
            order_type=OrderType.LIMIT,
            limit_price=45000.0
        )
        
        assert signal.order_type == OrderType.LIMIT
        assert signal.limit_price == 45000.0
    
    def test_limit_order_validation(self):
        """Test limit order validation."""
        # Missing limit price
        with pytest.raises(ValueError):
            Signal(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                quantity=1.0,
                timestamp=1640995200000,
                order_type=OrderType.LIMIT
                # Missing limit_price
            )
    
    def test_signal_properties(self):
        """Test signal calculated properties."""
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            timestamp=1640995200000
        )
        
        # Test datetime conversion
        expected_datetime = datetime.fromtimestamp(1640995200, timezone.utc)
        assert signal.datetime == expected_datetime
        
        # Test side multiplier
        assert signal.side_multiplier == 1
        
        sell_signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=1.0,
            timestamp=1640995200000
        )
        assert sell_signal.side_multiplier == -1
    
    def test_signal_serialization(self):
        """Test signal serialization."""
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            timestamp=1640995200000,
            metadata={"strategy": "test"}
        )
        
        # Test to_dict
        signal_dict = signal.to_dict()
        assert signal_dict['symbol'] == "BTCUSDT"
        assert signal_dict['side'] == "buy"
        assert signal_dict['metadata']['strategy'] == "test"
        
        # Test to_json
        json_str = signal.to_json()
        data = json.loads(json_str)
        assert data['symbol'] == "BTCUSDT"
        
        # Test from_dict
        reconstructed = Signal.from_dict(signal_dict)
        assert reconstructed.symbol == signal.symbol
        assert reconstructed.side == signal.side
        assert reconstructed.quantity == signal.quantity


class TestFill:
    """Test cases for Fill model."""
    
    def test_fill_creation(self):
        """Test basic fill creation."""
        fill = Fill(
            order_id="order_123",
            fill_id="fill_456",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=47000.0,
            timestamp=1640995200000,
            fee=47.0
        )
        
        assert fill.order_id == "order_123"
        assert fill.fill_id == "fill_456"
        assert fill.symbol == "BTCUSDT"
        assert fill.side == OrderSide.BUY
        assert fill.quantity == 1.0
        assert fill.price == 47000.0
        assert fill.fee == 47.0
    
    def test_fill_validation(self):
        """Test fill validation."""
        # Invalid quantity
        with pytest.raises(ValueError):
            Fill(
                order_id="order_123",
                fill_id="fill_456",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                quantity=0.0,  # Invalid
                price=47000.0,
                timestamp=1640995200000
            )
        
        # Invalid price
        with pytest.raises(ValueError):
            Fill(
                order_id="order_123",
                fill_id="fill_456",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                quantity=1.0,
                price=0.0,  # Invalid
                timestamp=1640995200000
            )
    
    def test_fill_properties(self):
        """Test fill calculated properties."""
        fill = Fill(
            order_id="order_123",
            fill_id="fill_456",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=47000.0,
            timestamp=1640995200000,
            fee=47.0
        )
        
        # Test notional value
        assert fill.notional_value == 47000.0
        
        # Test net amount (buy)
        assert fill.net_amount == 47047.0  # 47000 + 47 fee
        
        # Test sell net amount
        sell_fill = Fill(
            order_id="order_123",
            fill_id="fill_456",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=1.0,
            price=47000.0,
            timestamp=1640995200000,
            fee=47.0
        )
        assert sell_fill.net_amount == 46953.0  # 47000 - 47 fee
    
    def test_fill_serialization(self):
        """Test fill serialization."""
        fill = Fill(
            order_id="order_123",
            fill_id="fill_456",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=47000.0,
            timestamp=1640995200000,
            fee=47.0
        )
        
        # Test to_dict
        fill_dict = fill.to_dict()
        assert fill_dict['order_id'] == "order_123"
        assert fill_dict['notional_value'] == 47000.0
        assert fill_dict['net_amount'] == 47047.0
        
        # Test from_dict
        reconstructed = Fill.from_dict(fill_dict)
        assert reconstructed.order_id == fill.order_id
        assert reconstructed.quantity == fill.quantity
        assert reconstructed.price == fill.price


class TestOrder:
    """Test cases for Order model."""
    
    @pytest.fixture
    def sample_signal(self):
        """Sample signal for testing."""
        return Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            timestamp=1640995200000,
            order_type=OrderType.MARKET
        )
    
    def test_order_creation(self, sample_signal):
        """Test basic order creation."""
        order = Order(
            order_id="order_123",
            signal=sample_signal
        )
        
        assert order.order_id == "order_123"
        assert order.signal == sample_signal
        assert order.status == OrderStatus.NEW
        assert order.filled_quantity == 0.0
        assert order.is_active == True
        assert order.is_complete == False
    
    def test_order_properties(self, sample_signal):
        """Test order calculated properties."""
        order = Order(
            order_id="order_123",
            signal=sample_signal
        )
        
        # Test properties from signal
        assert order.symbol == "BTCUSDT"
        assert order.side == OrderSide.BUY
        assert order.quantity == 1.0
        assert order.order_type == OrderType.MARKET
        
        # Test calculated properties
        assert order.remaining_quantity == 1.0
        assert order.fill_percentage == 0.0
    
    def test_order_fill_handling(self, sample_signal):
        """Test order fill handling."""
        order = Order(
            order_id="order_123",
            signal=sample_signal
        )
        
        # Create a fill
        fill = Fill(
            order_id="order_123",
            fill_id="fill_456",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.5,
            price=47000.0,
            timestamp=1640995200000,
            fee=23.5
        )
        
        # Add fill to order
        order.add_fill(fill)
        
        assert order.filled_quantity == 0.5
        assert order.remaining_quantity == 0.5
        assert order.fill_percentage == 50.0
        assert order.average_fill_price == 47000.0
        assert order.total_fee == 23.5
        assert order.status == OrderStatus.PARTIALLY_FILLED
        assert len(order.fills) == 1
        
        # Add second fill to complete order
        fill2 = Fill(
            order_id="order_123",
            fill_id="fill_789",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.5,
            price=47100.0,
            timestamp=1640995260000,
            fee=23.55
        )
        
        order.add_fill(fill2)
        
        assert order.filled_quantity == 1.0
        assert order.remaining_quantity == 0.0
        assert order.fill_percentage == 100.0
        assert order.average_fill_price == 47050.0  # Weighted average
        assert order.total_fee == 47.05
        assert order.status == OrderStatus.FILLED
        assert order.is_complete == True
        assert order.is_active == False
    
    def test_order_validation_errors(self, sample_signal):
        """Test order fill validation errors."""
        order = Order(
            order_id="order_123",
            signal=sample_signal
        )
        
        # Wrong order ID
        with pytest.raises(ValueError):
            fill = Fill(
                order_id="wrong_order",
                fill_id="fill_456",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                quantity=0.5,
                price=47000.0,
                timestamp=1640995200000
            )
            order.add_fill(fill)
        
        # Wrong symbol
        with pytest.raises(ValueError):
            fill = Fill(
                order_id="order_123",
                fill_id="fill_456",
                symbol="ETHUSDT",  # Wrong symbol
                side=OrderSide.BUY,
                quantity=0.5,
                price=47000.0,
                timestamp=1640995200000
            )
            order.add_fill(fill)
        
        # Wrong side
        with pytest.raises(ValueError):
            fill = Fill(
                order_id="order_123",
                fill_id="fill_456",
                symbol="BTCUSDT",
                side=OrderSide.SELL,  # Wrong side
                quantity=0.5,
                price=47000.0,
                timestamp=1640995200000
            )
            order.add_fill(fill)
    
    def test_order_cancellation(self, sample_signal):
        """Test order cancellation."""
        order = Order(
            order_id="order_123",
            signal=sample_signal
        )
        
        # Cancel order
        order.cancel("User request")
        
        assert order.status == OrderStatus.CANCELLED
        assert order.rejection_reason == "User request"
        assert order.is_active == False
        
        # Cannot cancel already cancelled order
        with pytest.raises(ValueError):
            order.cancel("Cannot cancel again")
    
    def test_order_rejection(self, sample_signal):
        """Test order rejection."""
        order = Order(
            order_id="order_123",
            signal=sample_signal
        )
        
        # Reject order
        order.reject("Insufficient balance")
        
        assert order.status == OrderStatus.REJECTED
        assert order.rejection_reason == "Insufficient balance"
        assert order.is_active == False
    
    def test_order_serialization(self, sample_signal):
        """Test order serialization."""
        order = Order(
            order_id="order_123",
            signal=sample_signal
        )
        
        # Add a fill
        fill = Fill(
            order_id="order_123",
            fill_id="fill_456",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.5,
            price=47000.0,
            timestamp=1640995200000,
            fee=23.5
        )
        order.add_fill(fill)
        
        # Test to_dict
        order_dict = order.to_dict()
        assert order_dict['order_id'] == "order_123"
        assert order_dict['filled_quantity'] == 0.5
        assert len(order_dict['fills']) == 1
        
        # Test to_json
        json_str = order.to_json()
        data = json.loads(json_str)
        assert data['order_id'] == "order_123"
        
        # Test from_dict
        reconstructed = Order.from_dict(order_dict)
        assert reconstructed.order_id == order.order_id
        assert reconstructed.filled_quantity == order.filled_quantity
        assert len(reconstructed.fills) == 1


class TestExecutionConfig:
    """Test cases for ExecutionConfig model."""
    
    def test_config_creation(self):
        """Test basic config creation."""
        config = ExecutionConfig(
            maker_fee_rate=0.0005,
            taker_fee_rate=0.001,
            market_slippage_bps=5.0
        )
        
        assert config.maker_fee_rate == 0.0005
        assert config.taker_fee_rate == 0.001
        assert config.market_slippage_bps == 5.0
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = ExecutionConfig()
        
        assert config.maker_fee_rate == 0.001
        assert config.taker_fee_rate == 0.001
        assert config.market_slippage_bps == 5.0
        assert config.min_order_size == 0.001
        assert config.enable_position_limits == True
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid fee rate
        with pytest.raises(ValueError):
            ExecutionConfig(maker_fee_rate=-0.001)
        
        with pytest.raises(ValueError):
            ExecutionConfig(taker_fee_rate=-0.001)
        
        # Invalid slippage
        with pytest.raises(ValueError):
            ExecutionConfig(market_slippage_bps=-1.0)
        
        # Invalid minimum order size
        with pytest.raises(ValueError):
            ExecutionConfig(min_order_size=0.0)
    
    def test_config_serialization(self):
        """Test config serialization."""
        config = ExecutionConfig(
            maker_fee_rate=0.0005,
            taker_fee_rate=0.001
        )
        
        config_dict = config.to_dict()
        assert config_dict['maker_fee_rate'] == 0.0005
        assert config_dict['taker_fee_rate'] == 0.001
        assert 'enable_position_limits' in config_dict


if __name__ == "__main__":
    pytest.main([__file__])