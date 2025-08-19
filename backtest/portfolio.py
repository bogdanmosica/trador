"""
Portfolio Management

Tracks positions, calculates PnL, manages risk, and maintains portfolio state.
Provides comprehensive portfolio accounting for backtesting with realistic
position tracking and performance metrics.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

from .models import Trade, PositionState, MarketSnapshot, BacktestConfig


logger = logging.getLogger(__name__)


@dataclass
class PortfolioSnapshot:
    """
    Snapshot of portfolio state at a specific time.
    
    Contains all portfolio metrics including equity, positions,
    and performance statistics for historical tracking.
    """
    timestamp: datetime
    total_equity: float
    cash_balance: float
    total_position_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_fees: float
    positions: Dict[str, PositionState]
    trade_count: int
    
    @property
    def net_pnl(self) -> float:
        """Calculate net PnL (realized + unrealized - fees)."""
        return self.realized_pnl + self.unrealized_pnl - self.total_fees
    
    @property
    def total_return(self) -> float:
        """Calculate total return as percentage of initial equity."""
        initial_equity = self.total_equity - self.net_pnl
        if initial_equity <= 0:
            return 0.0
        return (self.net_pnl / initial_equity) * 100


class Portfolio:
    """
    Manages portfolio state, positions, and performance tracking.
    
    Provides comprehensive portfolio management including position tracking,
    PnL calculation, risk management, and performance metrics for backtesting.
    """
    
    def __init__(self, config: BacktestConfig, initial_balance: Optional[float] = None):
        """
        Initialize portfolio with configuration and starting balance.
        
        Args:
            config (BacktestConfig): Backtesting configuration
            initial_balance (Optional[float]): Starting cash balance
        """
        self.config = config
        self.initial_balance = initial_balance or config.initial_balance
        self.cash_balance = self.initial_balance
        
        # Position tracking
        self.positions: Dict[str, PositionState] = {}
        
        # Performance tracking
        self.realized_pnl = 0.0
        self.total_fees = 0.0
        self.trades: List[Trade] = []
        
        # Portfolio history
        self.snapshots: List[PortfolioSnapshot] = []
        
        # Risk tracking
        self.max_equity = self.initial_balance
        self.max_drawdown = 0.0
        
        logger.info(f"Portfolio initialized with {self.initial_balance} {config.base_currency}")
    
    def process_trade(self, trade: Trade, market_price: float) -> None:
        """
        Process a trade and update portfolio state.
        
        Args:
            trade (Trade): Executed trade to process
            market_price (float): Current market price for position valuation
        """
        symbol = trade.symbol
        
        # Initialize position if doesn't exist
        if symbol not in self.positions:
            self.positions[symbol] = PositionState(
                symbol=symbol,
                quantity=0.0,
                average_entry_price=0.0,
                entry_time=trade.timestamp,
                last_update=trade.timestamp
            )
        
        position = self.positions[symbol]
        
        # Process the trade
        if trade.side.upper() == 'BUY':
            self._process_buy_trade(trade, position)
        else:
            self._process_sell_trade(trade, position)
        
        # Update position market value
        position.last_update = trade.timestamp
        position.total_fees += trade.fees
        position.trade_count += 1
        
        # Update portfolio totals
        self.total_fees += trade.fees
        self.trades.append(trade)
        
        # Update unrealized PnL
        self._update_unrealized_pnl(symbol, market_price)
        
        logger.debug(f"Trade processed: {trade.side} {trade.quantity} {symbol} at {trade.price}")
    
    def _process_buy_trade(self, trade: Trade, position: PositionState) -> None:
        """
        Process a buy trade and update position.
        
        Args:
            trade (Trade): Buy trade to process
            position (PositionState): Position to update
        """
        old_quantity = position.quantity
        old_value = old_quantity * position.average_entry_price if old_quantity > 0 else 0
        
        # Add to position
        new_quantity = old_quantity + trade.quantity
        new_value = old_value + trade.notional_value
        
        if new_quantity > 0:
            position.average_entry_price = new_value / new_quantity
            position.quantity = new_quantity
            
            # Update entry time if opening new position
            if old_quantity <= 0:
                position.entry_time = trade.timestamp
        else:
            # Closing short position
            realized_pnl = old_value - trade.notional_value
            position.realized_pnl += realized_pnl
            self.realized_pnl += realized_pnl
            
            if new_quantity == 0:
                # Position closed
                position.average_entry_price = 0.0
                position.quantity = 0.0
            else:
                # Still short
                position.quantity = new_quantity
        
        # Update cash balance
        self.cash_balance -= (trade.notional_value + trade.fees)
    
    def _process_sell_trade(self, trade: Trade, position: PositionState) -> None:
        """
        Process a sell trade and update position.
        
        Args:
            trade (Trade): Sell trade to process
            position (PositionState): Position to update
        """
        old_quantity = position.quantity
        
        if old_quantity > 0:
            # Closing long position
            close_quantity = min(trade.quantity, old_quantity)
            realized_pnl = close_quantity * (trade.price - position.average_entry_price)
            position.realized_pnl += realized_pnl
            self.realized_pnl += realized_pnl
            
            position.quantity -= close_quantity
            
            # Check if opening short position
            remaining_sell = trade.quantity - close_quantity
            if remaining_sell > 0:
                position.quantity = -remaining_sell
                position.average_entry_price = trade.price
                position.entry_time = trade.timestamp
        else:
            # Adding to short position or opening new short
            old_value = abs(old_quantity) * position.average_entry_price if old_quantity < 0 else 0
            new_short_quantity = abs(old_quantity) + trade.quantity
            new_value = old_value + trade.notional_value
            
            position.quantity = -new_short_quantity
            position.average_entry_price = new_value / new_short_quantity
            
            if old_quantity >= 0:
                position.entry_time = trade.timestamp
        
        # Update cash balance
        self.cash_balance += (trade.notional_value - trade.fees)
    
    def _update_unrealized_pnl(self, symbol: str, market_price: float) -> None:
        """
        Update unrealized PnL for a position.
        
        Args:
            symbol (str): Symbol to update
            market_price (float): Current market price
        """
        if symbol in self.positions:
            position = self.positions[symbol]
            
            if position.quantity != 0:
                if position.quantity > 0:
                    # Long position
                    position.unrealized_pnl = position.quantity * (market_price - position.average_entry_price)
                else:
                    # Short position
                    position.unrealized_pnl = abs(position.quantity) * (position.average_entry_price - market_price)
            else:
                position.unrealized_pnl = 0.0
    
    def update_market_prices(self, market_data: Dict[str, float]) -> None:
        """
        Update unrealized PnL for all positions with current market prices.
        
        Args:
            market_data (Dict[str, float]): Current market prices by symbol
        """
        for symbol, price in market_data.items():
            self._update_unrealized_pnl(symbol, price)
    
    def get_position(self, symbol: str) -> Optional[PositionState]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol (str): Symbol to query
            
        Returns:
            Optional[PositionState]: Position if exists, None otherwise
        """
        return self.positions.get(symbol)
    
    def get_portfolio_value(self) -> float:
        """
        Calculate total portfolio value (cash + positions).
        
        Returns:
            float: Total portfolio value
        """
        position_value = sum(
            abs(pos.quantity) * pos.average_entry_price + pos.unrealized_pnl
            for pos in self.positions.values()
            if pos.quantity != 0
        )
        
        return self.cash_balance + position_value
    
    def get_total_unrealized_pnl(self) -> float:
        """
        Get total unrealized PnL across all positions.
        
        Returns:
            float: Total unrealized PnL
        """
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_exposure(self, symbol: str) -> float:
        """
        Get exposure percentage for a symbol.
        
        Args:
            symbol (str): Symbol to calculate exposure for
            
        Returns:
            float: Exposure as percentage of portfolio value
        """
        if symbol not in self.positions:
            return 0.0
        
        position = self.positions[symbol]
        if position.quantity == 0:
            return 0.0
        
        position_value = abs(position.quantity) * position.average_entry_price
        portfolio_value = self.get_portfolio_value()
        
        if portfolio_value <= 0:
            return 0.0
        
        return (position_value / portfolio_value) * 100
    
    def get_total_exposure(self) -> float:
        """
        Get total exposure across all positions.
        
        Returns:
            float: Total exposure as percentage
        """
        total_position_value = sum(
            abs(pos.quantity) * pos.average_entry_price
            for pos in self.positions.values()
            if pos.quantity != 0
        )
        
        portfolio_value = self.get_portfolio_value()
        
        if portfolio_value <= 0:
            return 0.0
        
        return (total_position_value / portfolio_value) * 100
    
    def can_open_position(self, symbol: str, quantity: float, price: float) -> bool:
        """
        Check if portfolio can open a new position within risk limits.
        
        Args:
            symbol (str): Symbol for new position
            quantity (float): Quantity to trade
            price (float): Price for position sizing
            
        Returns:
            bool: True if position can be opened within limits
        """
        notional_value = quantity * price
        portfolio_value = self.get_portfolio_value()
        
        # Check if we have enough cash
        if notional_value > self.cash_balance:
            return False
        
        # Check maximum position size
        if portfolio_value > 0:
            position_percentage = (notional_value / portfolio_value) * 100
            if position_percentage > self.config.max_position_size * 100:
                return False
        
        # Check minimum order size
        if notional_value < self.config.min_order_size:
            return False
        
        return True
    
    def take_snapshot(self, timestamp: datetime) -> PortfolioSnapshot:
        """
        Take a snapshot of current portfolio state.
        
        Args:
            timestamp (datetime): Timestamp for snapshot
            
        Returns:
            PortfolioSnapshot: Current portfolio state
        """
        total_unrealized_pnl = self.get_total_unrealized_pnl()
        total_position_value = sum(
            abs(pos.quantity) * pos.average_entry_price
            for pos in self.positions.values()
            if pos.quantity != 0
        )
        
        total_equity = self.cash_balance + total_position_value + total_unrealized_pnl
        
        # Update max equity and drawdown
        if total_equity > self.max_equity:
            self.max_equity = total_equity
        
        current_drawdown = (self.max_equity - total_equity) / self.max_equity * 100
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            total_equity=total_equity,
            cash_balance=self.cash_balance,
            total_position_value=total_position_value,
            unrealized_pnl=total_unrealized_pnl,
            realized_pnl=self.realized_pnl,
            total_fees=self.total_fees,
            positions=self.positions.copy(),
            trade_count=len(self.trades)
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.
        
        Returns:
            Dict[str, float]: Performance metrics including returns, drawdown, etc.
        """
        if not self.snapshots:
            return {}
        
        current_equity = self.get_portfolio_value()
        total_return = ((current_equity - self.initial_balance) / self.initial_balance) * 100
        
        # Calculate Sharpe ratio (simplified)
        if len(self.snapshots) > 1:
            returns = []
            for i in range(1, len(self.snapshots)):
                prev_equity = self.snapshots[i-1].total_equity
                curr_equity = self.snapshots[i].total_equity
                if prev_equity > 0:
                    daily_return = (curr_equity - prev_equity) / prev_equity
                    returns.append(daily_return)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                return_variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                return_std = return_variance ** 0.5
                sharpe_ratio = (avg_return / return_std) if return_std > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        # Win rate calculation
        winning_trades = sum(1 for trade in self.trades if trade.net_value > 0)
        win_rate = (winning_trades / len(self.trades) * 100) if self.trades else 0.0
        
        return {
            'total_return_pct': total_return,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.get_total_unrealized_pnl(),
            'total_fees': self.total_fees,
            'max_drawdown_pct': self.max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate_pct': win_rate,
            'total_trades': len(self.trades),
            'current_equity': current_equity
        }
    
    def reset(self) -> None:
        """Reset portfolio to initial state."""
        self.cash_balance = self.initial_balance
        self.positions.clear()
        self.realized_pnl = 0.0
        self.total_fees = 0.0
        self.trades.clear()
        self.snapshots.clear()
        self.max_equity = self.initial_balance
        self.max_drawdown = 0.0
        
        logger.info("Portfolio reset to initial state")