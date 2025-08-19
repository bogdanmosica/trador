"""
Main Backtester Class

Event-driven backtesting engine that coordinates strategy execution,
market data processing, order execution, and performance tracking.
Provides the main interface for running realistic trading simulations.
"""

from typing import List, Dict, Any, Optional, Type
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sys

# Add strategy module to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from strategy.base_strategy import BaseStrategy, MarketData, Position, Signal
from .models import (
    BacktestConfig, Order, OrderType, TimeInForce, MarketSnapshot
)
from .portfolio import Portfolio
from .execution.execution_engine import ExecutionEngine
from .data_feeds.base_feed import BaseDataFeed
from .data_feeds.binance_feed import BinanceDataFeed


logger = logging.getLogger(__name__)


class BacktestResult:
    """
    Contains results and analytics from a completed backtest.
    
    Provides comprehensive access to backtest outcomes including
    performance metrics, trade history, and portfolio snapshots.
    """
    
    def __init__(
        self,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_balance: float,
        final_equity: float,
        portfolio_snapshots: List,
        trades: List,
        performance_metrics: Dict[str, float],
        config: BacktestConfig
    ):
        """
        Initialize backtest result.
        
        Args:
            strategy_name (str): Name of tested strategy
            symbol (str): Trading symbol used
            start_date (datetime): Backtest start date
            end_date (datetime): Backtest end date
            initial_balance (float): Starting portfolio value
            final_equity (float): Final portfolio value
            portfolio_snapshots (List): Historical portfolio states
            trades (List): Executed trades
            performance_metrics (Dict[str, float]): Performance statistics
            config (BacktestConfig): Backtest configuration used
        """
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.final_equity = final_equity
        self.portfolio_snapshots = portfolio_snapshots
        self.trades = trades
        self.performance_metrics = performance_metrics
        self.config = config
        
        # Calculate duration
        self.duration = end_date - start_date
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of backtest results.
        
        Returns:
            Dict[str, Any]: Summary statistics and key metrics
        """
        return {
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'period': f"{self.start_date.date()} to {self.end_date.date()}",
            'duration_days': self.duration.days,
            'initial_balance': self.initial_balance,
            'final_equity': self.final_equity,
            'total_return_pct': self.performance_metrics.get('total_return_pct', 0),
            'max_drawdown_pct': self.performance_metrics.get('max_drawdown_pct', 0),
            'sharpe_ratio': self.performance_metrics.get('sharpe_ratio', 0),
            'total_trades': len(self.trades),
            'win_rate_pct': self.performance_metrics.get('win_rate_pct', 0),
            'total_fees': self.performance_metrics.get('total_fees', 0)
        }


class Backtester:
    """
    Event-driven backtesting engine for trading strategies.
    
    Coordinates strategy execution, market data processing, order execution,
    and performance tracking to provide realistic trading simulation.
    """
    
    def __init__(self, config: BacktestConfig, data_feed: Optional[BaseDataFeed] = None):
        """
        Initialize backtester with configuration and data feed.
        
        Args:
            config (BacktestConfig): Backtesting configuration
            data_feed (Optional[BaseDataFeed]): Data feed implementation
        """
        self.config = config
        self.data_feed = data_feed or BinanceDataFeed(
            cache_enabled=config.cache_data,
            cache_path=config.data_cache_path
        )
        
        # Initialize components
        self.portfolio = Portfolio(config)
        self.execution_engine = ExecutionEngine(config)
        
        # State tracking
        self.current_time: Optional[datetime] = None
        self.market_data_history: List[MarketSnapshot] = []
        
        logger.info(f"Backtester initialized with {config.initial_balance} {config.base_currency}")
    
    def run_backtest(
        self,
        strategy: BaseStrategy,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        strategy_params: Dict[str, Any]
    ) -> BacktestResult:
        """
        Run a complete backtest for a strategy.
        
        Args:
            strategy (BaseStrategy): Strategy to test
            symbol (str): Trading symbol
            timeframe (str): Data timeframe (e.g., '1h', '4h', '1d')
            start_date (datetime): Backtest start date
            end_date (datetime): Backtest end date
            strategy_params (Dict[str, Any]): Strategy parameters
            
        Returns:
            BacktestResult: Complete backtest results
        """
        logger.info(f"Starting backtest: {strategy.strategy_name} on {symbol} from {start_date} to {end_date}")
        
        try:
            # Reset state
            self._reset_state()
            
            # Fetch historical data
            market_data = self._fetch_market_data(symbol, timeframe, start_date, end_date)
            
            if not market_data:
                raise ValueError("No market data available for the specified period")
            
            # Run simulation
            self._run_simulation(strategy, market_data, strategy_params)
            
            # Generate results
            result = self._generate_results(
                strategy.strategy_name,
                symbol,
                start_date,
                end_date
            )
            
            logger.info(f"Backtest completed: {len(self.portfolio.trades)} trades, "
                       f"{result.performance_metrics.get('total_return_pct', 0):.2f}% return")
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise
    
    def _fetch_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[MarketSnapshot]:
        """
        Fetch historical market data for backtesting.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Data timeframe
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            List[MarketSnapshot]: Historical market data
        """
        logger.info(f"Fetching market data for {symbol} {timeframe}")
        
        market_data = self.data_feed.fetch_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_date,
            end_time=end_date
        )
        
        # Sort by timestamp to ensure chronological order
        market_data.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Loaded {len(market_data)} candles")
        return market_data
    
    def _run_simulation(
        self,
        strategy: BaseStrategy,
        market_data: List[MarketSnapshot],
        strategy_params: Dict[str, Any]
    ) -> None:
        """
        Run the main simulation loop.
        
        Args:
            strategy (BaseStrategy): Strategy to execute
            market_data (List[MarketSnapshot]): Historical market data
            strategy_params (Dict[str, Any]): Strategy parameters
        """
        logger.info("Running simulation...")
        
        # Get required lookback period
        lookback_period = strategy_params.get('lookback_period', 50)
        
        for i, current_candle in enumerate(market_data):
            self.current_time = current_candle.timestamp
            
            # Build market data window for strategy
            start_idx = max(0, i - lookback_period + 1)
            market_window = market_data[start_idx:i + 1]
            
            # Convert to strategy format
            strategy_data = self._convert_to_strategy_format(market_window)
            
            # Get current position
            current_position = self._get_current_position(current_candle.symbol)
            
            # Process any pending orders first
            new_trades = self.execution_engine.process_market_update(current_candle)
            
            # Process trades in portfolio
            for trade in new_trades:
                self.portfolio.process_trade(trade, current_candle.close)
            
            # Skip strategy execution if insufficient data
            if len(strategy_data) < lookback_period:
                continue
            
            # Generate strategy signals
            try:
                signals = strategy.generate_signals(
                    market_data=strategy_data,
                    current_position=current_position,
                    strategy_params=strategy_params
                )
            except Exception as e:
                logger.warning(f"Strategy signal generation failed at {current_candle.timestamp}: {e}")
                signals = []
            
            # Process signals and create orders
            for signal in signals:
                order = self._convert_signal_to_order(signal, current_candle)
                if order:
                    self.execution_engine.submit_order(order)
            
            # Update portfolio with current prices
            self.portfolio.update_market_prices({current_candle.symbol: current_candle.close})
            
            # Take portfolio snapshot (every 24 hours or at significant intervals)
            if i % max(1, len(market_data) // 100) == 0:  # Take ~100 snapshots
                self.portfolio.take_snapshot(current_candle.timestamp)
            
            self.market_data_history.append(current_candle)
        
        # Final portfolio snapshot
        if market_data:
            self.portfolio.take_snapshot(market_data[-1].timestamp)
    
    def _convert_to_strategy_format(self, market_snapshots: List[MarketSnapshot]) -> List[MarketData]:
        """
        Convert market snapshots to strategy MarketData format.
        
        Args:
            market_snapshots (List[MarketSnapshot]): Market data snapshots
            
        Returns:
            List[MarketData]: Strategy-compatible market data
        """
        strategy_data = []
        
        for snapshot in market_snapshots:
            market_data = MarketData(
                timestamp=snapshot.timestamp,
                open=snapshot.open,
                high=snapshot.high,
                low=snapshot.low,
                close=snapshot.close,
                volume=snapshot.volume,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe
            )
            strategy_data.append(market_data)
        
        return strategy_data
    
    def _get_current_position(self, symbol: str) -> Optional[Position]:
        """
        Get current position in strategy format.
        
        Args:
            symbol (str): Symbol to get position for
            
        Returns:
            Optional[Position]: Current position or None
        """
        portfolio_position = self.portfolio.get_position(symbol)
        
        if not portfolio_position or portfolio_position.quantity == 0:
            return None
        
        return Position(
            symbol=symbol,
            quantity=portfolio_position.quantity,
            entry_price=portfolio_position.average_entry_price,
            entry_time=portfolio_position.entry_time,
            unrealized_pnl=portfolio_position.unrealized_pnl
        )
    
    def _convert_signal_to_order(self, signal: Signal, market_data: MarketSnapshot) -> Optional[Order]:
        """
        Convert strategy signal to executable order.
        
        Args:
            signal (Signal): Strategy signal
            market_data (MarketSnapshot): Current market data
            
        Returns:
            Optional[Order]: Order to execute or None
        """
        if signal.action.upper() == 'HOLD':
            return None
        
        # Calculate position size
        portfolio_value = self.portfolio.get_portfolio_value()
        max_position_value = portfolio_value * signal.quantity_ratio
        
        # Use current price for sizing
        current_price = market_data.close
        max_quantity = max_position_value / current_price
        
        # Check minimum order size
        if max_position_value < self.config.min_order_size:
            logger.debug(f"Signal ignored: order size too small ({max_position_value:.2f})")
            return None
        
        # Check if we can open this position
        if not self.portfolio.can_open_position(signal.symbol, max_quantity, current_price):
            logger.debug(f"Signal ignored: position limits exceeded")
            return None
        
        # Determine order type and side
        side = 'BUY' if signal.action.upper() == 'BUY' else 'SELL'
        
        # Create market order (can be extended to support limit orders)
        order = Order(
            symbol=signal.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=max_quantity,
            timestamp=signal.timestamp,
            time_in_force=TimeInForce.GTC,
            metadata={
                'signal_confidence': signal.confidence,
                'signal_reason': signal.reason,
                'strategy_name': signal.metadata.get('strategy_name', 'unknown') if signal.metadata else 'unknown'
            }
        )
        
        return order
    
    def _generate_results(
        self,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        Generate comprehensive backtest results.
        
        Args:
            strategy_name (str): Name of tested strategy
            symbol (str): Trading symbol
            start_date (datetime): Backtest start date
            end_date (datetime): Backtest end date
            
        Returns:
            BacktestResult: Complete backtest results
        """
        final_equity = self.portfolio.get_portfolio_value()
        performance_metrics = self.portfolio.get_performance_metrics()
        
        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.config.initial_balance,
            final_equity=final_equity,
            portfolio_snapshots=self.portfolio.snapshots,
            trades=self.portfolio.trades,
            performance_metrics=performance_metrics,
            config=self.config
        )
    
    def _reset_state(self) -> None:
        """Reset backtester state for new run."""
        self.portfolio.reset()
        self.execution_engine.reset()
        self.current_time = None
        self.market_data_history.clear()
        
        logger.debug("Backtester state reset")
    
    def get_data_feed_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the data feed.
        
        Returns:
            Dict[str, Any]: Data feed statistics
        """
        return self.data_feed.get_cache_stats()
    
    def clear_data_cache(self) -> None:
        """Clear data feed cache."""
        self.data_feed.clear_cache()
        logger.info("Data cache cleared")