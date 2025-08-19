"""
Test Portfolio Manager

Unit tests for portfolio management functionality including position tracking,
P&L calculation, and risk metrics computation.
"""

import pytest
from datetime import datetime, timezone

from ..portfolio.manager import PortfolioManager, Position, PortfolioSnapshot
from ..models import Fill, OrderSide


class TestPosition:
    """Test cases for Position model."""
    
    def test_position_creation(self):
        """Test basic position creation."""
        position = Position(symbol="BTCUSDT")
        
        assert position.symbol == "BTCUSDT"
        assert position.quantity == 0.0
        assert position.average_entry_price == 0.0
        assert position.realized_pnl == 0.0
        assert position.is_flat == True
        assert position.is_long == False
        assert position.is_short == False
    
    def test_position_opening(self):
        """Test opening a new position."""
        position = Position(symbol="BTCUSDT")
        
        # Create opening fill
        fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        
        position.update_position(fill)
        
        assert position.quantity == 1.0
        assert position.average_entry_price == 50000.0
        assert position.total_cost == 50000.0
        assert position.total_fees == 50.0
        assert position.trade_count == 1
        assert position.is_long == True
        assert position.is_flat == False
    
    def test_position_adding(self):
        """Test adding to existing position."""
        position = Position(symbol="BTCUSDT")
        
        # First fill
        fill1 = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        position.update_position(fill1)
        
        # Second fill at different price
        fill2 = Fill(
            order_id="order_2",
            fill_id="fill_2",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=52000.0,
            timestamp=1640995260000,
            fee=52.0
        )
        position.update_position(fill2)
        
        assert position.quantity == 2.0
        assert position.average_entry_price == 51000.0  # (50000 + 52000) / 2
        assert position.total_cost == 102000.0
        assert position.total_fees == 102.0
        assert position.trade_count == 2
    
    def test_position_closing(self):
        """Test closing a position."""
        position = Position(symbol="BTCUSDT")
        
        # Open position
        open_fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        position.update_position(open_fill)
        
        # Close position at profit
        close_fill = Fill(
            order_id="order_2",
            fill_id="fill_2",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=1.0,
            price=55000.0,
            timestamp=1640995260000,
            fee=55.0
        )
        position.update_position(close_fill)
        
        assert position.quantity == 0.0
        assert position.realized_pnl == 5000.0  # 55000 - 50000
        assert position.total_fees == 105.0
        assert position.is_flat == True
    
    def test_position_partial_close(self):
        """Test partial position closing."""
        position = Position(symbol="BTCUSDT")
        
        # Open position
        open_fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=2.0,
            price=50000.0,
            timestamp=1640995200000,
            fee=100.0
        )
        position.update_position(open_fill)
        
        # Partial close
        close_fill = Fill(
            order_id="order_2",
            fill_id="fill_2",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=1.0,
            price=55000.0,
            timestamp=1640995260000,
            fee=55.0
        )
        position.update_position(close_fill)
        
        assert position.quantity == 1.0  # 1 BTC remaining
        assert position.average_entry_price == 50000.0  # Same entry price
        assert position.realized_pnl == 5000.0  # Profit on 1 BTC sold
        assert position.total_fees == 155.0
        assert position.is_long == True
    
    def test_position_reversal(self):
        """Test position reversal."""
        position = Position(symbol="BTCUSDT")
        
        # Open long position
        long_fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        position.update_position(long_fill)
        
        # Reverse to short
        reverse_fill = Fill(
            order_id="order_2",
            fill_id="fill_2",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=2.0,  # Sell more than we have
            price=55000.0,
            timestamp=1640995260000,
            fee=110.0
        )
        position.update_position(reverse_fill)
        
        assert position.quantity == -1.0  # Now short 1 BTC
        assert position.average_entry_price == 55000.0  # New entry price
        assert position.realized_pnl == 5000.0  # Profit from closing long
        assert position.is_short == True
    
    def test_unrealized_pnl_calculation(self):
        """Test unrealized P&L calculation."""
        position = Position(symbol="BTCUSDT")
        
        # Open long position
        fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        position.update_position(fill)
        
        # Test unrealized P&L at different prices
        assert position.unrealized_pnl(55000.0) == 5000.0  # Profit
        assert position.unrealized_pnl(45000.0) == -5000.0  # Loss
        assert position.unrealized_pnl(50000.0) == 0.0  # Break-even
    
    def test_position_serialization(self):
        """Test position serialization."""
        position = Position(symbol="BTCUSDT", quantity=1.0, average_entry_price=50000.0)
        
        position_dict = position.to_dict()
        
        assert position_dict['symbol'] == "BTCUSDT"
        assert position_dict['quantity'] == 1.0
        assert position_dict['average_entry_price'] == 50000.0
        assert position_dict['is_long'] == True
        assert position_dict['notional_value'] == 50000.0


class TestPortfolioManager:
    """Test cases for PortfolioManager."""
    
    @pytest.fixture
    def portfolio(self):
        """Test portfolio manager instance."""
        return PortfolioManager(initial_cash=10000.0)
    
    def test_portfolio_initialization(self, portfolio):
        """Test portfolio initialization."""
        assert portfolio.initial_cash == 10000.0
        assert portfolio.cash_balance == 10000.0
        assert portfolio.total_value == 10000.0
        assert portfolio.total_pnl == 0.0
        assert len(portfolio.positions) == 0
        assert len(portfolio.active_positions) == 0
    
    def test_portfolio_fill_application(self, portfolio):
        """Test applying fills to portfolio."""
        # Buy order
        buy_fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        
        portfolio.apply_fill(buy_fill)
        
        # Check cash was deducted
        expected_cash = 10000.0 - (0.1 * 50000.0) - 50.0  # Initial - cost - fee
        assert portfolio.cash_balance == expected_cash
        
        # Check position was created
        position = portfolio.get_position("BTCUSDT")
        assert position.quantity == 0.1
        assert position.average_entry_price == 50000.0
        
        # Check statistics
        assert portfolio.total_trades == 1
        assert portfolio.total_volume == 5000.0
        assert portfolio.total_fees == 50.0
    
    def test_portfolio_sell_order(self, portfolio):
        """Test sell order processing."""
        # First buy some BTC
        buy_fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        portfolio.apply_fill(buy_fill)
        
        initial_cash = portfolio.cash_balance
        
        # Sell the BTC
        sell_fill = Fill(
            order_id="order_2",
            fill_id="fill_2",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=0.1,
            price=55000.0,
            timestamp=1640995260000,
            fee=55.0
        )
        portfolio.apply_fill(sell_fill)
        
        # Check cash was credited
        expected_cash = initial_cash + (0.1 * 55000.0) - 55.0
        assert portfolio.cash_balance == expected_cash
        
        # Check position was closed
        position = portfolio.get_position("BTCUSDT")
        assert position.quantity == 0.0
        assert position.realized_pnl == 500.0  # 55000 - 50000 for 0.1 BTC
    
    def test_portfolio_market_price_update(self, portfolio):
        """Test market price updates."""
        # Create a position
        fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        portfolio.apply_fill(fill)
        
        # Update market price
        portfolio.update_market_price("BTCUSDT", 55000.0)
        
        # Check total value includes unrealized gain
        expected_value = portfolio.cash_balance + (0.1 * 55000.0)
        assert abs(portfolio.total_value - expected_value) < 0.01
        
        # Check unrealized P&L
        assert portfolio.unrealized_pnl == 500.0  # 0.1 * (55000 - 50000)
    
    def test_portfolio_affordability_check(self, portfolio):
        """Test order affordability checking."""
        # Check buy affordability
        assert portfolio.can_afford_order("BTCUSDT", OrderSide.BUY, 0.1, 50000.0) == True
        assert portfolio.can_afford_order("BTCUSDT", OrderSide.BUY, 1.0, 50000.0) == False
        
        # Create a position for sell test
        fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        portfolio.apply_fill(fill)
        
        # Check sell affordability
        assert portfolio.can_afford_order("BTCUSDT", OrderSide.SELL, 0.05, 55000.0) == True
        assert portfolio.can_afford_order("BTCUSDT", OrderSide.SELL, 0.2, 55000.0) == False
    
    def test_buying_power_calculation(self, portfolio):
        """Test buying power calculation."""
        buying_power = portfolio.get_buying_power(50000.0, 0.001)
        
        # Should be able to buy cash / (price * (1 + fee_rate))
        expected_power = 10000.0 / (50000.0 * 1.001)
        assert abs(buying_power - expected_power) < 0.000001
    
    def test_portfolio_snapshot(self, portfolio):
        """Test portfolio snapshot creation."""
        # Create a position
        fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        portfolio.apply_fill(fill)
        portfolio.update_market_price("BTCUSDT", 55000.0)
        
        # Create snapshot
        snapshot = portfolio.create_snapshot()
        
        assert isinstance(snapshot, PortfolioSnapshot)
        assert snapshot.cash_balance == portfolio.cash_balance
        assert "BTCUSDT" in snapshot.positions
        assert snapshot.market_prices["BTCUSDT"] == 55000.0
        assert snapshot.total_value > 0
        assert snapshot.total_pnl != 0
    
    def test_performance_metrics(self, portfolio):
        """Test performance metrics calculation."""
        # Execute some trades
        fills = [
            Fill("order_1", "fill_1", "BTCUSDT", OrderSide.BUY, 0.1, 50000.0, 1640995200000, 50.0),
            Fill("order_2", "fill_2", "BTCUSDT", OrderSide.SELL, 0.1, 55000.0, 1640995260000, 55.0),
            Fill("order_3", "fill_3", "ETHUSDT", OrderSide.BUY, 1.0, 3000.0, 1640995320000, 30.0),
        ]
        
        for fill in fills:
            portfolio.apply_fill(fill)
        
        metrics = portfolio.get_performance_metrics()
        
        assert metrics['total_trades'] == 3
        assert metrics['total_volume'] == 13000.0  # 5000 + 5500 + 3000
        assert metrics['total_fees'] == 135.0  # 50 + 55 + 30
        assert metrics['realized_pnl'] > 0  # Should have profit from BTC trade
        assert 'return_percent' in metrics
        assert 'win_rate' in metrics
    
    def test_risk_metrics(self, portfolio):
        """Test risk metrics calculation."""
        # Create multiple positions
        fills = [
            Fill("order_1", "fill_1", "BTCUSDT", OrderSide.BUY, 0.1, 50000.0, 1640995200000, 50.0),
            Fill("order_2", "fill_2", "ETHUSDT", OrderSide.BUY, 1.0, 3000.0, 1640995260000, 30.0),
        ]
        
        for fill in fills:
            portfolio.apply_fill(fill)
        
        # Update market prices
        portfolio.update_market_price("BTCUSDT", 55000.0)
        portfolio.update_market_price("ETHUSDT", 3200.0)
        
        risk_metrics = portfolio.get_risk_metrics()
        
        assert risk_metrics['position_count'] == 2
        assert risk_metrics['total_exposure'] > 0
        assert risk_metrics['largest_position_percent'] > 0
        assert risk_metrics['concentration_risk'] > 0
        assert risk_metrics['leverage_ratio'] > 0
    
    def test_portfolio_reset(self, portfolio):
        """Test portfolio reset functionality."""
        # Create some activity
        fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        portfolio.apply_fill(fill)
        
        # Reset with new balance
        portfolio.reset(15000.0)
        
        assert portfolio.initial_cash == 15000.0
        assert portfolio.cash_balance == 15000.0
        assert len(portfolio.positions) == 0
        assert portfolio.total_trades == 0
        assert portfolio.total_volume == 0.0
        assert portfolio.total_fees == 0.0
    
    def test_portfolio_export(self, portfolio):
        """Test portfolio state export."""
        # Create some activity
        fill = Fill(
            order_id="order_1",
            fill_id="fill_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            timestamp=1640995200000,
            fee=50.0
        )
        portfolio.apply_fill(fill)
        portfolio.update_market_price("BTCUSDT", 55000.0)
        
        # Export state
        state = portfolio.export_state()
        
        assert state['initial_cash'] == 10000.0
        assert state['cash_balance'] == portfolio.cash_balance
        assert 'BTCUSDT' in state['positions']
        assert 'performance_metrics' in state
        assert 'risk_metrics' in state
        assert 'export_timestamp' in state
        
        # Test JSON export
        json_str = portfolio.to_json()
        assert isinstance(json_str, str)
        assert '"BTCUSDT"' in json_str


class TestPortfolioSnapshot:
    """Test cases for PortfolioSnapshot."""
    
    def test_snapshot_creation(self):
        """Test snapshot creation and calculations."""
        positions = {
            "BTCUSDT": Position("BTCUSDT", quantity=0.1, average_entry_price=50000.0),
            "ETHUSDT": Position("ETHUSDT", quantity=1.0, average_entry_price=3000.0)
        }
        
        market_prices = {
            "BTCUSDT": 55000.0,
            "ETHUSDT": 3200.0
        }
        
        snapshot = PortfolioSnapshot(
            timestamp=1640995200000,
            cash_balance=5000.0,
            positions=positions,
            market_prices=market_prices
        )
        
        # Check automatic calculations
        expected_total_value = 5000.0 + (0.1 * 55000.0) + (1.0 * 3200.0)
        assert abs(snapshot.total_value - expected_total_value) < 0.01
        
        # Check P&L calculation
        btc_pnl = 0.1 * (55000.0 - 50000.0)  # 500
        eth_pnl = 1.0 * (3200.0 - 3000.0)    # 200
        expected_pnl = btc_pnl + eth_pnl     # 700
        assert abs(snapshot.total_pnl - expected_pnl) < 0.01
    
    def test_snapshot_serialization(self):
        """Test snapshot serialization."""
        positions = {
            "BTCUSDT": Position("BTCUSDT", quantity=0.1, average_entry_price=50000.0)
        }
        
        snapshot = PortfolioSnapshot(
            timestamp=1640995200000,
            cash_balance=5000.0,
            positions=positions,
            market_prices={"BTCUSDT": 55000.0}
        )
        
        snapshot_dict = snapshot.to_dict()
        
        assert snapshot_dict['timestamp'] == 1640995200000
        assert snapshot_dict['cash_balance'] == 5000.0
        assert 'BTCUSDT' in snapshot_dict['positions']
        assert snapshot_dict['market_prices']['BTCUSDT'] == 55000.0
        assert 'total_value' in snapshot_dict
        assert 'total_pnl' in snapshot_dict


if __name__ == "__main__":
    pytest.main([__file__])