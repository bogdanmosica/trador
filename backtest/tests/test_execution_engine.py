"""
Test Execution Engine

Unit tests for order execution simulation, fill logic, and trade generation.
Validates realistic execution behavior and order lifecycle management.
"""

import pytest
from datetime import datetime, timezone, timedelta

from ..execution.execution_engine import ExecutionEngine
from ..execution.fill_simulator import FillSimulator
from ..models import (
    Order, OrderType, OrderStatus, TimeInForce, MarketSnapshot, BacktestConfig
)


class TestFillSimulator:
    """Test cases for FillSimulator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = BacktestConfig(
            market_order_slippage=0.001,
            execution_latency_ms=100,
            maker_fee=0.001,
            taker_fee=0.001
        )
        self.simulator = FillSimulator(self.config)
        
        self.market_data = MarketSnapshot(
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
    
    def test_market_order_buy_execution(self):
        """Test market buy order execution."""
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        fills = self.simulator.process_order(order, self.market_data)
        
        assert len(fills) == 1
        fill = fills[0]
        
        # Market buy should execute at ask + slippage
        expected_price = self.market_data.ask * (1 + self.config.market_order_slippage)
        assert abs(fill.price - expected_price) < 0.01
        
        assert fill.symbol == "BTCUSDT"
        assert fill.side == "BUY"
        assert fill.quantity == 1.0
        assert not fill.is_maker  # Market orders are taker
        assert fill.fees > 0
        
        # Order should be filled
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 1.0
        assert order.remaining_quantity == 0.0
    
    def test_market_order_sell_execution(self):
        """Test market sell order execution."""
        order = Order(
            symbol="BTCUSDT",
            side="SELL",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        fills = self.simulator.process_order(order, self.market_data)
        
        assert len(fills) == 1
        fill = fills[0]
        
        # Market sell should execute at bid - slippage
        expected_price = self.market_data.bid * (1 - self.config.market_order_slippage)
        assert abs(fill.price - expected_price) < 0.01
        
        assert fill.side == "SELL"
        assert not fill.is_maker
        assert order.status == OrderStatus.FILLED
    
    def test_limit_order_execution(self):
        """Test limit order execution."""
        # Buy limit order that can be filled
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=1.0,
            limit_price=50100.0,  # Above current ask
            timestamp=datetime.now(timezone.utc)
        )
        
        fills = self.simulator.process_order(order, self.market_data)
        
        assert len(fills) == 1
        fill = fills[0]
        
        # Should get price improvement (better than limit price)
        assert fill.price <= order.limit_price
        assert fill.is_maker  # Limit orders are typically maker
        assert order.status == OrderStatus.FILLED
    
    def test_limit_order_no_fill(self):
        """Test limit order that cannot be filled."""
        # Buy limit order below market
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=1.0,
            limit_price=48000.0,  # Below current bid
            timestamp=datetime.now(timezone.utc)
        )
        
        fills = self.simulator.process_order(order, self.market_data)
        
        assert len(fills) == 0
        assert order.status == OrderStatus.PENDING  # Still pending
        assert order.filled_quantity == 0.0
        assert order.remaining_quantity == 1.0
    
    def test_stop_order_trigger(self):
        """Test stop order triggering."""
        # Stop-market order
        order = Order(
            symbol="BTCUSDT",
            side="SELL",
            order_type=OrderType.STOP_MARKET,
            quantity=1.0,
            stop_price=49000.0,  # Below current price
            timestamp=datetime.now(timezone.utc)
        )
        
        # Create market data that triggers the stop
        trigger_data = MarketSnapshot(
            timestamp=datetime.now(timezone.utc),
            symbol="BTCUSDT",
            open=49000.0,
            high=49000.0,
            low=48000.0,
            close=48500.0,  # Price fell below stop
            volume=1000.0,
            timeframe="1h",
            bid=48450.0,
            ask=48550.0
        )
        
        fills = self.simulator.process_order(order, trigger_data)
        
        assert len(fills) == 1
        assert order.status == OrderStatus.FILLED
        assert order.order_type == OrderType.MARKET  # Converted to market order
    
    def test_ioc_order_behavior(self):
        """Test Immediate-Or-Cancel order behavior."""
        # Set up partial fill simulation
        self.config.partial_fill_probability = 1.0  # Force partial fill
        
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            time_in_force=TimeInForce.IOC,
            timestamp=datetime.now(timezone.utc)
        )
        
        fills = self.simulator.process_order(order, self.market_data)
        
        # IOC order should either fill completely or have remaining quantity cancelled
        if order.filled_quantity < order.quantity:
            assert order.status == OrderStatus.PARTIAL_FILLED
            assert order.remaining_quantity == 0  # Cancelled remainder
    
    def test_fok_order_behavior(self):
        """Test Fill-Or-Kill order behavior."""
        # Force partial fill scenario
        self.config.partial_fill_probability = 1.0
        
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            time_in_force=TimeInForce.FOK,
            timestamp=datetime.now(timezone.utc)
        )
        
        fills = self.simulator.process_order(order, self.market_data)
        
        # FOK order should either fill completely or be cancelled entirely
        if order.filled_quantity < order.quantity:
            assert order.status == OrderStatus.CANCELLED
            assert order.filled_quantity == 0
    
    def test_execution_latency(self):
        """Test execution latency simulation."""
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        fills = self.simulator.process_order(order, self.market_data)
        
        if fills:
            fill = fills[0]
            # Execution time should be after order time + latency
            expected_min_time = order.timestamp + timedelta(milliseconds=self.config.execution_latency_ms)
            assert fill.timestamp >= expected_min_time


class TestExecutionEngine:
    """Test cases for ExecutionEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = BacktestConfig()
        self.engine = ExecutionEngine(self.config)
        
        self.market_data = MarketSnapshot(
            timestamp=datetime.now(timezone.utc),
            symbol="BTCUSDT",
            open=49000.0,
            high=51000.0,
            low=48000.0,
            close=50000.0,
            volume=1000.0,
            timeframe="1h"
        )
    
    def test_order_submission(self):
        """Test order submission."""
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        order_id = self.engine.submit_order(order)
        
        assert order_id == order.order_id
        assert order_id in self.engine.orders
        assert len(self.engine.get_pending_orders()) == 1
    
    def test_order_validation(self):
        """Test order validation."""
        # Valid order
        valid_order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        order_id = self.engine.submit_order(valid_order)
        assert valid_order.status != OrderStatus.REJECTED
        
        # Invalid order (zero quantity)
        invalid_order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=0.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.engine.submit_order(invalid_order)
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_market_update_processing(self):
        """Test market update processing."""
        # Submit an order
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.engine.submit_order(order)
        
        # Process market update
        trades = self.engine.process_market_update(self.market_data)
        
        assert len(trades) > 0
        assert len(self.engine.trades) > 0
        assert order.status == OrderStatus.FILLED
    
    def test_order_cancellation(self):
        """Test order cancellation."""
        # Submit limit order that won't fill immediately
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=1.0,
            limit_price=40000.0,  # Well below market
            timestamp=datetime.now(timezone.utc)
        )
        
        order_id = self.engine.submit_order(order)
        
        # Verify order is pending
        assert order.status == OrderStatus.PENDING
        assert len(self.engine.get_pending_orders()) == 1
        
        # Cancel the order
        success = self.engine.cancel_order(order_id)
        
        assert success
        assert order.status == OrderStatus.CANCELLED
        assert len(self.engine.get_pending_orders()) == 0
    
    def test_cancel_all_orders(self):
        """Test cancelling all orders."""
        # Submit multiple orders
        for i in range(3):
            order = Order(
                symbol="BTCUSDT",
                side="BUY",
                order_type=OrderType.LIMIT,
                quantity=1.0,
                limit_price=40000.0 + i * 1000,
                timestamp=datetime.now(timezone.utc)
            )
            self.engine.submit_order(order)
        
        assert len(self.engine.get_pending_orders()) == 3
        
        # Cancel all orders
        cancelled_count = self.engine.cancel_all_orders()
        
        assert cancelled_count == 3
        assert len(self.engine.get_pending_orders()) == 0
    
    def test_symbol_specific_operations(self):
        """Test symbol-specific order operations."""
        # Submit orders for different symbols
        btc_order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=1.0,
            limit_price=40000.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        eth_order = Order(
            symbol="ETHUSDT",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=10.0,
            limit_price=2000.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.engine.submit_order(btc_order)
        self.engine.submit_order(eth_order)
        
        # Test symbol-specific pending orders
        btc_pending = self.engine.get_pending_orders("BTCUSDT")
        eth_pending = self.engine.get_pending_orders("ETHUSDT")
        
        assert len(btc_pending) == 1
        assert len(eth_pending) == 1
        assert btc_pending[0].symbol == "BTCUSDT"
        assert eth_pending[0].symbol == "ETHUSDT"
        
        # Test symbol-specific cancellation
        cancelled = self.engine.cancel_all_orders("BTCUSDT")
        assert cancelled == 1
        assert len(self.engine.get_pending_orders("BTCUSDT")) == 0
        assert len(self.engine.get_pending_orders("ETHUSDT")) == 1
    
    def test_trade_summary(self):
        """Test trade summary generation."""
        # Process some orders to generate trades
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.engine.submit_order(order)
        self.engine.process_market_update(self.market_data)
        
        summary = self.engine.get_trade_summary()
        
        assert 'total_trades' in summary
        assert 'total_volume' in summary
        assert 'total_fees' in summary
        assert 'symbols_traded' in summary
        assert 'avg_trade_size' in summary
        
        assert summary['total_trades'] > 0
        assert summary['total_volume'] > 0
        assert 'BTCUSDT' in summary['symbols_traded']
    
    def test_engine_reset(self):
        """Test execution engine reset."""
        # Submit and process orders
        order = Order(
            symbol="BTCUSDT",
            side="BUY",
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.engine.submit_order(order)
        self.engine.process_market_update(self.market_data)
        
        # Verify state is not empty
        assert len(self.engine.orders) > 0
        assert len(self.engine.trades) > 0
        
        # Reset engine
        self.engine.reset()
        
        # Verify state is reset
        assert len(self.engine.orders) == 0
        assert len(self.engine.trades) == 0
        assert len(self.engine.get_pending_orders()) == 0


if __name__ == "__main__":
    pytest.main([__file__])