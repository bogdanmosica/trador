"""
Test Simulated Execution Engine

Unit tests for the simulated execution engine including order processing,
portfolio management, and market simulation functionality.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from ..engines.simulated import SimulatedExecutionEngine, MarketData
from ..models import (
    Signal, OrderSide, OrderType, OrderStatus, ExecutionConfig
)


class TestSimulatedExecutionEngine:
    """Test cases for SimulatedExecutionEngine."""
    
    @pytest.fixture
    def config(self):
        """Test execution configuration."""
        return ExecutionConfig(
            maker_fee_rate=0.001,
            taker_fee_rate=0.001,
            market_slippage_bps=5.0,
            initial_balance=10000.0
        )
    
    @pytest.fixture
    def engine(self, config):
        """Test engine instance."""
        return SimulatedExecutionEngine(config, initial_balance=10000.0)
    
    @pytest.fixture
    def market_data(self):
        """Sample market data."""
        return MarketData(
            symbol="BTCUSDT",
            timestamp=1640995200000,
            open_price=47000.0,
            high_price=47500.0,
            low_price=46500.0,
            close_price=47200.0,
            volume=1000.0
        )
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, engine):
        """Test engine start and stop."""
        assert not engine.is_running
        
        await engine.start()
        assert engine.is_running
        
        await engine.stop()
        assert not engine.is_running
    
    @pytest.mark.asyncio
    async def test_market_order_execution(self, engine, market_data):
        """Test market order execution."""
        await engine.start()
        
        # Update market data
        engine.update_market_data(market_data)
        
        # Create market order signal
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            timestamp=1640995200000,
            order_type=OrderType.MARKET
        )
        
        # Submit signal
        order = await engine.submit_signal(signal)
        
        # Wait for execution
        await asyncio.sleep(0.2)
        
        # Check order was filled
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 0.1
        assert order.average_fill_price > 0
        assert len(order.fills) == 1
        
        # Check portfolio was updated
        position = engine.get_position("BTCUSDT")
        assert position == 0.1
        assert engine.cash_balance < 10000.0  # Cash reduced
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_limit_order_execution(self, engine, market_data):
        """Test limit order execution."""
        await engine.start()
        
        # Update market data
        engine.update_market_data(market_data)
        
        # Create limit order signal (at low price, should fill)
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            timestamp=1640995200000,
            order_type=OrderType.LIMIT,
            limit_price=46600.0  # Below low of 46500, should fill
        )
        
        # Submit signal
        order = await engine.submit_signal(signal)
        
        # Order should be pending initially
        assert order.status == OrderStatus.PENDING
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check order was filled
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 0.1
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_limit_order_no_fill(self, engine, market_data):
        """Test limit order that doesn't fill."""
        await engine.start()
        
        # Update market data
        engine.update_market_data(market_data)
        
        # Create limit order signal (at high price, should not fill)
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            timestamp=1640995200000,
            order_type=OrderType.LIMIT,
            limit_price=46000.0  # Below low of 46500, should not fill
        )
        
        # Submit signal
        order = await engine.submit_signal(signal)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Order should remain pending
        assert order.status == OrderStatus.PENDING
        assert order.filled_quantity == 0.0
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_sell_order_execution(self, engine, market_data):
        """Test sell order execution."""
        await engine.start()
        
        # Update market data
        engine.update_market_data(market_data)
        
        # First buy some BTC
        buy_signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            timestamp=1640995200000,
            order_type=OrderType.MARKET
        )
        
        buy_order = await engine.submit_signal(buy_signal)
        await asyncio.sleep(0.2)
        
        assert buy_order.status == OrderStatus.FILLED
        assert engine.get_position("BTCUSDT") == 0.1
        
        # Now sell the BTC
        sell_signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=0.1,
            timestamp=1640995260000,
            order_type=OrderType.MARKET
        )
        
        sell_order = await engine.submit_signal(sell_signal)
        await asyncio.sleep(0.2)
        
        assert sell_order.status == OrderStatus.FILLED
        assert engine.get_position("BTCUSDT") == 0.0
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_insufficient_balance_check(self, engine, market_data):
        """Test insufficient balance checking."""
        await engine.start()
        
        # Update market data
        engine.update_market_data(market_data)
        
        # Try to buy more than we can afford
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1000.0,  # Way more than we can afford
            timestamp=1640995200000,
            order_type=OrderType.MARKET
        )
        
        # Should raise insufficient balance error
        with pytest.raises(Exception):  # InsufficientBalanceError
            await engine.submit_signal(signal)
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_insufficient_position_check(self, engine, market_data):
        """Test insufficient position checking."""
        await engine.start()
        
        # Update market data
        engine.update_market_data(market_data)
        
        # Try to sell without having a position
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=1.0,
            timestamp=1640995200000,
            order_type=OrderType.MARKET
        )
        
        # Should raise insufficient balance error
        with pytest.raises(Exception):  # InsufficientBalanceError
            await engine.submit_signal(signal)
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_order_cancellation(self, engine, market_data):
        """Test order cancellation."""
        await engine.start()
        
        # Update market data
        engine.update_market_data(market_data)
        
        # Create limit order that won't fill immediately
        signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            timestamp=1640995200000,
            order_type=OrderType.LIMIT,
            limit_price=40000.0  # Very low price
        )
        
        order = await engine.submit_signal(signal)
        assert order.status == OrderStatus.PENDING
        
        # Cancel the order
        success = await engine.cancel_order(order.order_id, "Test cancellation")
        assert success == True
        assert order.status == OrderStatus.CANCELLED
        assert order.rejection_reason == "Test cancellation"
        
        await engine.stop()
    
    def test_portfolio_tracking(self, engine, market_data):
        """Test portfolio tracking."""
        # Initial state
        assert engine.cash_balance == 10000.0
        assert engine.portfolio_value == 10000.0
        assert engine.unrealized_pnl == 0.0
        assert len(engine.positions) == 0
        
        # Update market data
        engine.update_market_data(market_data)
        
        # Simulate a position
        engine.positions["BTCUSDT"] = 0.1
        engine.cash_balance = 5280.0  # Remaining after buying 0.1 BTC at 47200
        
        # Check portfolio value calculation
        expected_value = 5280.0 + (0.1 * 47200.0)  # Cash + position value
        assert abs(engine.portfolio_value - expected_value) < 0.01
        
        # Check unrealized PnL
        expected_pnl = engine.portfolio_value - 10000.0
        assert abs(engine.unrealized_pnl - expected_pnl) < 0.01
    
    def test_slippage_calculation(self, engine, market_data):
        """Test slippage calculation."""
        # Test buy order slippage
        buy_signal = Signal(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            timestamp=1640995200000,
            order_type=OrderType.MARKET
        )
        
        order = type('Order', (), {'side': OrderSide.BUY})()
        execution_price = engine._calculate_market_execution_price(order, market_data)
        
        # Price should be higher than typical price due to slippage
        typical_price = market_data.typical_price
        assert execution_price > typical_price
        
        # Test sell order slippage
        sell_order = type('Order', (), {'side': OrderSide.SELL})()
        sell_execution_price = engine._calculate_market_execution_price(sell_order, market_data)
        
        # Price should be lower than typical price due to slippage
        assert sell_execution_price < typical_price
    
    def test_fee_calculation(self, engine):
        """Test fee calculation."""
        order = type('Order', (), {
            'order_id': 'test_order',
            'symbol': 'BTCUSDT',
            'side': OrderSide.BUY
        })()
        
        # Test taker fee
        fill = engine._create_fill(order, 47000.0, 0.1, is_maker=False)
        expected_taker_fee = 0.1 * 47000.0 * engine.config.taker_fee_rate
        assert abs(fill.fee - expected_taker_fee) < 0.01
        
        # Test maker fee
        maker_fill = engine._create_fill(order, 47000.0, 0.1, is_maker=True)
        expected_maker_fee = 0.1 * 47000.0 * engine.config.maker_fee_rate
        assert abs(maker_fill.fee - expected_maker_fee) < 0.01
    
    def test_portfolio_reset(self, engine):
        """Test portfolio reset functionality."""
        # Modify portfolio state
        engine.cash_balance = 5000.0
        engine.positions["BTCUSDT"] = 0.1
        engine.total_trades = 10
        engine.total_volume = 50000.0
        engine.total_fees = 100.0
        
        # Reset portfolio
        engine.reset_portfolio(15000.0)
        
        # Check reset state
        assert engine.cash_balance == 15000.0
        assert engine.initial_balance == 15000.0
        assert len(engine.positions) == 0
        assert engine.total_trades == 0
        assert engine.total_volume == 0.0
        assert engine.total_fees == 0.0
    
    def test_portfolio_summary(self, engine, market_data):
        """Test portfolio summary."""
        # Update market data
        engine.update_market_data(market_data)
        
        # Simulate trades
        engine.positions["BTCUSDT"] = 0.1
        engine.cash_balance = 5280.0
        engine.total_trades = 2
        engine.total_volume = 9440.0
        engine.total_fees = 9.44
        
        summary = engine.get_portfolio_summary()
        
        assert summary['cash_balance'] == 5280.0
        assert summary['positions']['BTCUSDT'] == 0.1
        assert summary['total_trades'] == 2
        assert summary['total_volume'] == 9440.0
        assert summary['total_fees'] == 9.44
        assert 'portfolio_value' in summary
        assert 'unrealized_pnl' in summary
        assert 'return_percent' in summary
    
    @pytest.mark.asyncio
    async def test_execution_statistics(self, engine, market_data):
        """Test execution statistics."""
        await engine.start()
        engine.update_market_data(market_data)
        
        # Execute some orders
        for i in range(3):
            signal = Signal(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                quantity=0.01,
                timestamp=1640995200000 + i * 1000,
                order_type=OrderType.MARKET
            )
            await engine.submit_signal(signal)
            await asyncio.sleep(0.1)
        
        stats = engine.get_execution_statistics()
        
        assert stats['total_orders'] == 3
        assert stats['filled_orders'] == 3
        assert stats['total_fills'] == 3
        assert stats['fill_rate'] == 1.0
        assert stats['total_volume'] > 0
        assert stats['total_fees'] > 0
        
        await engine.stop()


class TestMarketData:
    """Test cases for MarketData helper class."""
    
    def test_market_data_creation(self):
        """Test market data creation."""
        market_data = MarketData(
            symbol="BTCUSDT",
            timestamp=1640995200000,
            open_price=47000.0,
            high_price=47500.0,
            low_price=46500.0,
            close_price=47200.0,
            volume=1000.0
        )
        
        assert market_data.symbol == "BTCUSDT"
        assert market_data.open == 47000.0
        assert market_data.high == 47500.0
        assert market_data.low == 46500.0
        assert market_data.close == 47200.0
        assert market_data.volume == 1000.0
    
    def test_market_data_properties(self):
        """Test market data calculated properties."""
        market_data = MarketData(
            symbol="BTCUSDT",
            timestamp=1640995200000,
            open_price=47000.0,
            high_price=47500.0,
            low_price=46500.0,
            close_price=47200.0,
            volume=1000.0
        )
        
        # Test typical price (HLC/3)
        expected_typical = (47500.0 + 46500.0 + 47200.0) / 3
        assert abs(market_data.typical_price - expected_typical) < 0.01
        
        # Test weighted price (HLCC/4)
        expected_weighted = (47500.0 + 46500.0 + 47200.0 + 47200.0) / 4
        assert abs(market_data.weighted_price - expected_weighted) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])