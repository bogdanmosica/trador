"""
Integration Tests

End-to-end integration tests for the complete backtesting system.
Tests the interaction between all components in realistic scenarios.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add strategy module to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..backtester import Backtester, BacktestResult
from ..models import BacktestConfig, MarketSnapshot
from ..data_feeds.base_feed import BaseDataFeed
from strategy.base_strategy import BaseStrategy, MarketData, Position, Signal


class MockStrategy(BaseStrategy):
    """Mock strategy for testing."""
    
    def __init__(self):
        super().__init__("MockStrategy")
        self.call_count = 0
    
    def generate_signals(self, market_data, current_position, strategy_params):
        """Generate mock signals based on simple rules."""
        self.call_count += 1
        
        if not market_data or len(market_data) < 2:
            return []
        
        current_candle = market_data[-1]
        previous_candle = market_data[-2]
        
        signals = []
        
        # Simple momentum strategy: buy if price is rising, sell if falling
        if current_candle.close > previous_candle.close * 1.02:  # 2% rise
            if not current_position or current_position.quantity <= 0:
                signal = Signal(
                    action="BUY",
                    symbol=current_candle.symbol,
                    timestamp=current_candle.timestamp,
                    confidence=0.8,
                    quantity_ratio=0.5,  # Use 50% of available capital
                    reason="Price momentum upward",
                    metadata={"strategy_name": "MockStrategy"}
                )
                signals.append(signal)
        
        elif current_candle.close < previous_candle.close * 0.98:  # 2% fall
            if current_position and current_position.quantity > 0:
                signal = Signal(
                    action="SELL",
                    symbol=current_candle.symbol,
                    timestamp=current_candle.timestamp,
                    confidence=0.8,
                    quantity_ratio=1.0,  # Sell entire position
                    reason="Price momentum downward",
                    metadata={"strategy_name": "MockStrategy"}
                )
                signals.append(signal)
        
        return signals
    
    def update_parameters(self, preset_name):
        """Mock parameter update."""
        return True
    
    def validate_parameters(self, params):
        """Mock parameter validation."""
        return True


class MockDataFeed(BaseDataFeed):
    """Mock data feed for testing."""
    
    def __init__(self):
        super().__init__(cache_enabled=False)
        self.data_cache = []
    
    def fetch_historical_data(self, symbol, timeframe, start_time, end_time, limit=None):
        """Generate mock historical data."""
        if self.data_cache:
            return self.data_cache
        
        # Generate 100 candles with some price movement
        data = []
        base_price = 50000.0
        current_time = start_time
        
        for i in range(100):
            # Add some random price movement
            price_change = (i % 10 - 5) * 100  # -500 to +400 variation
            current_price = base_price + price_change + (i * 10)  # Overall uptrend
            
            # Create OHLC data
            open_price = current_price
            high_price = current_price + 200
            low_price = current_price - 200
            close_price = current_price + 50
            
            snapshot = MarketSnapshot(
                timestamp=current_time,
                symbol=symbol,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=1000.0,
                timeframe=timeframe
            )
            
            data.append(snapshot)
            current_time += timedelta(hours=1)  # 1-hour candles
        
        self.data_cache = data
        return data
    
    def get_symbol_info(self, symbol):
        """Mock symbol info."""
        return {
            'symbol': symbol,
            'status': 'TRADING',
            'baseAsset': 'BTC',
            'quoteAsset': 'USDT'
        }
    
    def get_available_symbols(self):
        """Mock available symbols."""
        return ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']


class TestBacktesterIntegration:
    """Integration tests for the complete backtesting system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = BacktestConfig(
            initial_balance=10000.0,
            maker_fee=0.001,
            taker_fee=0.001,
            market_order_slippage=0.001,
            min_order_size=100.0
        )
        
        self.mock_data_feed = MockDataFeed()
        self.backtester = Backtester(self.config, self.mock_data_feed)
        self.strategy = MockStrategy()
    
    def test_complete_backtest_flow(self):
        """Test complete backtest from start to finish."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 5, tzinfo=timezone.utc)
        
        strategy_params = {
            'lookback_period': 20
        }
        
        # Run backtest
        result = self.backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        # Verify result structure
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "MockStrategy"
        assert result.symbol == "BTCUSDT"
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert result.initial_balance == 10000.0
        
        # Verify strategy was called
        assert self.strategy.call_count > 0
        
        # Verify we have portfolio snapshots
        assert len(result.portfolio_snapshots) > 0
        
        # Verify performance metrics exist
        assert isinstance(result.performance_metrics, dict)
        assert 'total_return_pct' in result.performance_metrics
        assert 'total_trades' in result.performance_metrics
    
    def test_backtest_with_trades(self):
        """Test backtest that generates actual trades."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 5, tzinfo=timezone.utc)
        
        strategy_params = {
            'lookback_period': 5  # Short lookback to get signals quickly
        }
        
        result = self.backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        # Should have generated some trades due to price movements
        assert len(result.trades) > 0
        
        # Verify trade properties
        for trade in result.trades:
            assert trade.symbol == "BTCUSDT"
            assert trade.side in ["BUY", "SELL"]
            assert trade.quantity > 0
            assert trade.price > 0
            assert trade.fees >= 0
        
        # Verify final equity changed from initial
        assert result.final_equity != result.initial_balance
    
    def test_portfolio_state_tracking(self):
        """Test portfolio state tracking throughout backtest."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 3, tzinfo=timezone.utc)
        
        strategy_params = {'lookback_period': 5}
        
        result = self.backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        # Verify portfolio snapshots progression
        snapshots = result.portfolio_snapshots
        assert len(snapshots) > 1
        
        # First snapshot should be initial state
        first_snapshot = snapshots[0]
        assert first_snapshot.cash_balance == 10000.0
        assert first_snapshot.total_position_value == 0.0
        assert first_snapshot.trade_count == 0
        
        # Last snapshot should reflect final state
        last_snapshot = snapshots[-1]
        assert last_snapshot.trade_count >= 0
        
        # Verify timestamps are in order
        for i in range(1, len(snapshots)):
            assert snapshots[i].timestamp >= snapshots[i-1].timestamp
    
    def test_risk_management(self):
        """Test risk management functionality."""
        # Use smaller initial balance to test limits
        small_config = BacktestConfig(
            initial_balance=1000.0,
            min_order_size=50.0,
            max_position_size=0.5  # 50% max position
        )
        
        backtester = Backtester(small_config, self.mock_data_feed)
        
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 2, tzinfo=timezone.utc)
        
        strategy_params = {'lookback_period': 5}
        
        result = backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        # Verify risk limits were respected
        # Portfolio shouldn't be completely depleted due to risk limits
        assert result.final_equity > 0
        
        # Check that no individual trade was too large
        for trade in result.trades:
            trade_value = trade.quantity * trade.price
            # Should respect position sizing limits
            assert trade_value <= small_config.initial_balance * small_config.max_position_size * 2  # Allow some buffer
    
    def test_performance_metrics_calculation(self):
        """Test comprehensive performance metrics calculation."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 5, tzinfo=timezone.utc)
        
        strategy_params = {'lookback_period': 5}
        
        result = self.backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        metrics = result.performance_metrics
        
        # Verify key metrics exist
        required_metrics = [
            'total_return_pct',
            'realized_pnl',
            'unrealized_pnl', 
            'total_fees',
            'max_drawdown_pct',
            'sharpe_ratio',
            'total_trades',
            'current_equity'
        ]
        
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
        
        # Verify metric values are reasonable
        assert isinstance(metrics['total_return_pct'], (int, float))
        assert isinstance(metrics['total_trades'], int)
        assert metrics['total_trades'] >= 0
        assert metrics['total_fees'] >= 0
        assert metrics['current_equity'] > 0
    
    def test_backtester_reset_between_runs(self):
        """Test that backtester properly resets between runs."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 2, tzinfo=timezone.utc)
        
        strategy_params = {'lookback_period': 5}
        
        # First run
        result1 = self.backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        # Second run should start fresh
        result2 = self.backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        # Both runs should start with same initial balance
        assert result1.initial_balance == result2.initial_balance
        
        # Results should be identical (deterministic with same data)
        assert len(result1.trades) == len(result2.trades)
        assert abs(result1.final_equity - result2.final_equity) < 0.01
    
    def test_error_handling(self):
        """Test error handling in backtesting."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 2, tzinfo=timezone.utc)
        
        # Test with empty data feed
        empty_feed = MockDataFeed()
        empty_feed.data_cache = []  # No data
        empty_backtester = Backtester(self.config, empty_feed)
        
        strategy_params = {'lookback_period': 5}
        
        # Should raise an error for no data
        with pytest.raises(ValueError):
            empty_backtester.run_backtest(
                strategy=self.strategy,
                symbol="BTCUSDT",
                timeframe="1h",
                start_date=start_date,
                end_date=end_date,
                strategy_params=strategy_params
            )
    
    def test_summary_generation(self):
        """Test backtest result summary generation."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 1, 3, tzinfo=timezone.utc)
        
        strategy_params = {'lookback_period': 5}
        
        result = self.backtester.run_backtest(
            strategy=self.strategy,
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params
        )
        
        summary = result.get_summary()
        
        # Verify summary structure
        required_keys = [
            'strategy_name',
            'symbol',
            'period',
            'duration_days',
            'initial_balance',
            'final_equity',
            'total_return_pct',
            'max_drawdown_pct',
            'total_trades'
        ]
        
        for key in required_keys:
            assert key in summary, f"Missing summary key: {key}"
        
        # Verify summary values
        assert summary['strategy_name'] == "MockStrategy"
        assert summary['symbol'] == "BTCUSDT"
        assert summary['duration_days'] == 2
        assert summary['initial_balance'] == 10000.0
        assert isinstance(summary['total_trades'], int)


if __name__ == "__main__":
    pytest.main([__file__])