"""
Test Portfolio Management

Unit tests for portfolio tracking, position management, and PnL calculations.
Validates portfolio state management and performance metrics.
"""

import pytest
from datetime import datetime, timezone

from ..portfolio import Portfolio, PortfolioSnapshot
from ..models import Trade, BacktestConfig


class TestPortfolio:
    """Test cases for Portfolio class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = BacktestConfig(initial_balance=10000.0)
        self.portfolio = Portfolio(self.config)
    
    def test_portfolio_initialization(self):
        """Test portfolio initialization."""
        assert self.portfolio.initial_balance == 10000.0
        assert self.portfolio.cash_balance == 10000.0
        assert self.portfolio.realized_pnl == 0.0
        assert self.portfolio.total_fees == 0.0
        assert len(self.portfolio.positions) == 0
        assert len(self.portfolio.trades) == 0
    
    def test_process_buy_trade(self):
        """Test processing a buy trade."""
        trade = Trade(
            trade_id="trade1",
            order_id="order1",
            symbol="BTCUSDT",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            fees=50.0
        )
        
        self.portfolio.process_trade(trade, market_price=50000.0)
        
        # Check cash balance
        assert self.portfolio.cash_balance == 10000.0 - 50000.0 - 50.0  # Initial - cost - fees
        
        # Check position
        position = self.portfolio.get_position("BTCUSDT")
        assert position is not None
        assert position.quantity == 1.0
        assert position.average_entry_price == 50000.0
        assert position.is_long
        
        # Check trade tracking
        assert len(self.portfolio.trades) == 1
        assert self.portfolio.total_fees == 50.0
    
    def test_process_sell_trade(self):
        """Test processing a sell trade."""
        # First buy
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
        
        self.portfolio.process_trade(buy_trade, market_price=50000.0)
        
        # Then sell at higher price
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
        
        self.portfolio.process_trade(sell_trade, market_price=55000.0)
        
        # Check realized PnL (55000 - 50000 = 5000 profit)
        assert self.portfolio.realized_pnl == 5000.0
        
        # Check position is closed
        position = self.portfolio.get_position("BTCUSDT")
        assert position.quantity == 0.0
        assert position.is_flat
        
        # Check cash balance (initial - buy cost - buy fees + sell proceeds - sell fees)
        expected_cash = 10000.0 - 50000.0 - 50.0 + 55000.0 - 55.0
        assert self.portfolio.cash_balance == expected_cash
        
        # Check total fees
        assert self.portfolio.total_fees == 105.0
    
    def test_partial_position_close(self):
        """Test partial position closing."""
        # Buy 2 units
        buy_trade = Trade(
            trade_id="trade1",
            order_id="order1",
            symbol="BTCUSDT",
            side="BUY",
            quantity=2.0,
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            fees=100.0
        )
        
        self.portfolio.process_trade(buy_trade, market_price=50000.0)
        
        # Sell 1 unit
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
        
        self.portfolio.process_trade(sell_trade, market_price=55000.0)
        
        # Check position (should have 1 unit remaining)
        position = self.portfolio.get_position("BTCUSDT")
        assert position.quantity == 1.0
        assert position.average_entry_price == 50000.0
        
        # Check realized PnL (1 unit sold for 5000 profit)
        assert self.portfolio.realized_pnl == 5000.0
    
    def test_short_position(self):
        """Test short position handling."""
        # Sell without position (go short)
        sell_trade = Trade(
            trade_id="trade1",
            order_id="order1",
            symbol="BTCUSDT",
            side="SELL",
            quantity=1.0,
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            fees=50.0
        )
        
        self.portfolio.process_trade(sell_trade, market_price=50000.0)
        
        # Check position
        position = self.portfolio.get_position("BTCUSDT")
        assert position.quantity == -1.0
        assert position.average_entry_price == 50000.0
        assert position.is_short
        
        # Check cash balance (received cash from short sale)
        expected_cash = 10000.0 + 50000.0 - 50.0
        assert self.portfolio.cash_balance == expected_cash
    
    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation."""
        # Initial value should equal cash
        assert self.portfolio.get_portfolio_value() == 10000.0
        
        # Buy position
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
        
        self.portfolio.process_trade(buy_trade, market_price=50000.0)
        
        # Update unrealized PnL with new market price
        self.portfolio.update_market_prices({"BTCUSDT": 55000.0})
        
        # Portfolio value should be cash + position value + unrealized PnL
        expected_value = (10000.0 - 50000.0 - 50.0) + 50000.0 + 5000.0  # Cash + position cost + unrealized gain
        portfolio_value = self.portfolio.get_portfolio_value()
        assert abs(portfolio_value - expected_value) < 0.01  # Allow for small rounding errors
    
    def test_exposure_calculation(self):
        """Test position exposure calculations."""
        # Buy position
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
        
        self.portfolio.process_trade(buy_trade, market_price=50000.0)
        
        # Calculate exposure (position value / portfolio value)
        exposure = self.portfolio.get_exposure("BTCUSDT")
        
        # Position value = 50000, Portfolio value = 10000 (approximately, due to fees)
        # Exposure should be around 500%
        assert exposure > 400.0  # Should be high leverage
    
    def test_risk_limits(self):
        """Test risk limit checking."""
        # Should be able to open reasonable position
        can_open = self.portfolio.can_open_position("BTCUSDT", 0.1, 50000.0)
        assert can_open
        
        # Should not be able to open position larger than cash
        cannot_open = self.portfolio.can_open_position("BTCUSDT", 1.0, 20000.0)
        assert not cannot_open  # 20k > 10k cash
        
        # Test minimum order size
        cannot_open_small = self.portfolio.can_open_position("BTCUSDT", 0.001, 1000.0)
        assert not cannot_open_small  # Too small order
    
    def test_portfolio_snapshots(self):
        """Test portfolio snapshot functionality."""
        timestamp = datetime.now(timezone.utc)
        
        # Take initial snapshot
        snapshot = self.portfolio.take_snapshot(timestamp)
        
        assert isinstance(snapshot, PortfolioSnapshot)
        assert snapshot.timestamp == timestamp
        assert snapshot.total_equity == 10000.0
        assert snapshot.cash_balance == 10000.0
        assert snapshot.unrealized_pnl == 0.0
        assert snapshot.realized_pnl == 0.0
        assert snapshot.total_fees == 0.0
        assert snapshot.trade_count == 0
        
        # Process a trade
        trade = Trade(
            trade_id="trade1",
            order_id="order1",
            symbol="BTCUSDT",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            timestamp=timestamp,
            fees=50.0
        )
        
        self.portfolio.process_trade(trade, market_price=55000.0)
        
        # Take another snapshot
        snapshot2 = self.portfolio.take_snapshot(timestamp)
        
        assert snapshot2.trade_count == 1
        assert snapshot2.total_fees == 50.0
        assert snapshot2.unrealized_pnl == 5000.0  # 55000 - 50000
        assert len(self.portfolio.snapshots) == 2
    
    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        # Process some trades to generate performance data
        
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
        
        self.portfolio.process_trade(buy_trade, market_price=50000.0)
        
        # Sell trade (profitable)
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
        
        self.portfolio.process_trade(sell_trade, market_price=55000.0)
        
        # Get performance metrics
        metrics = self.portfolio.get_performance_metrics()
        
        assert 'total_return_pct' in metrics
        assert 'realized_pnl' in metrics
        assert 'total_fees' in metrics
        assert 'total_trades' in metrics
        assert 'win_rate_pct' in metrics
        
        assert metrics['realized_pnl'] == 5000.0
        assert metrics['total_fees'] == 105.0
        assert metrics['total_trades'] == 2
        assert metrics['win_rate_pct'] > 0  # Should have winning trades
    
    def test_portfolio_reset(self):
        """Test portfolio reset functionality."""
        # Process a trade
        trade = Trade(
            trade_id="trade1",
            order_id="order1",
            symbol="BTCUSDT",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            fees=50.0
        )
        
        self.portfolio.process_trade(trade, market_price=50000.0)
        self.portfolio.take_snapshot(datetime.now(timezone.utc))
        
        # Verify state is not empty
        assert len(self.portfolio.trades) > 0
        assert len(self.portfolio.positions) > 0
        assert len(self.portfolio.snapshots) > 0
        assert self.portfolio.total_fees > 0
        
        # Reset portfolio
        self.portfolio.reset()
        
        # Verify state is reset
        assert self.portfolio.cash_balance == 10000.0
        assert len(self.portfolio.positions) == 0
        assert self.portfolio.realized_pnl == 0.0
        assert self.portfolio.total_fees == 0.0
        assert len(self.portfolio.trades) == 0
        assert len(self.portfolio.snapshots) == 0
        assert self.portfolio.max_equity == 10000.0
        assert self.portfolio.max_drawdown == 0.0


if __name__ == "__main__":
    pytest.main([__file__])