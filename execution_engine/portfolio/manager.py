"""
Portfolio Manager for Execution Engine

Manages portfolio state, positions, and P&L tracking for the execution engine.
Provides comprehensive portfolio analytics and risk management features.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
import logging
from decimal import Decimal

from ..models import Order, Fill, OrderSide


@dataclass
class Position:
    """
    Represents a position in a trading symbol.
    
    Tracks quantity, average entry price, realized and unrealized P&L,
    and provides position-level analytics.
    """
    symbol: str
    quantity: float = 0.0
    average_entry_price: float = 0.0
    total_cost: float = 0.0
    realized_pnl: float = 0.0
    total_fees: float = 0.0
    trade_count: int = 0
    last_update: Optional[int] = None
    
    def __post_init__(self):
        """Initialize last update timestamp."""
        if self.last_update is None:
            self.last_update = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is flat (no position)."""
        return abs(self.quantity) < 1e-8
    
    @property
    def notional_value(self) -> float:
        """Calculate notional value at average entry price."""
        return abs(self.quantity) * self.average_entry_price
    
    def unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized P&L at current price.
        
        Args:
            current_price: Current market price
            
        Returns:
            Unrealized P&L
        """
        if self.is_flat:
            return 0.0
        
        return self.quantity * (current_price - self.average_entry_price)
    
    def total_pnl(self, current_price: float) -> float:
        """
        Calculate total P&L (realized + unrealized).
        
        Args:
            current_price: Current market price
            
        Returns:
            Total P&L
        """
        return self.realized_pnl + self.unrealized_pnl(current_price)
    
    def update_position(self, fill: Fill) -> None:
        """
        Update position with a new fill.
        
        Args:
            fill: Fill to apply to position
        """
        if fill.symbol != self.symbol:
            raise ValueError(f"Fill symbol {fill.symbol} does not match position symbol {self.symbol}")
        
        old_quantity = self.quantity
        fill_quantity = fill.quantity if fill.side == OrderSide.BUY else -fill.quantity
        
        # Check if this is a closing trade
        if (old_quantity > 0 and fill_quantity < 0) or (old_quantity < 0 and fill_quantity > 0):
            # Partially or fully closing position
            closing_quantity = min(abs(old_quantity), abs(fill_quantity))
            
            if old_quantity > 0:  # Closing long position
                pnl_per_unit = fill.price - self.average_entry_price
                closing_pnl = closing_quantity * pnl_per_unit
            else:  # Closing short position
                pnl_per_unit = self.average_entry_price - fill.price
                closing_pnl = closing_quantity * pnl_per_unit
            
            self.realized_pnl += closing_pnl
            
            # Update position
            if abs(fill_quantity) >= abs(old_quantity):
                # Position reversed or closed
                remaining_quantity = abs(fill_quantity) - abs(old_quantity)
                if remaining_quantity > 0:
                    # Position reversed
                    self.quantity = remaining_quantity if fill.side == OrderSide.BUY else -remaining_quantity
                    self.average_entry_price = fill.price
                    self.total_cost = remaining_quantity * fill.price
                else:
                    # Position closed
                    self.quantity = 0.0
                    self.average_entry_price = 0.0
                    self.total_cost = 0.0
            else:
                # Partial close
                self.quantity += fill_quantity
                # Keep same average entry price and adjust total cost
                self.total_cost = abs(self.quantity) * self.average_entry_price
        
        else:
            # Adding to position or opening new position
            new_quantity = self.quantity + fill_quantity
            
            if self.is_flat:
                # Opening new position
                self.quantity = new_quantity
                self.average_entry_price = fill.price
                self.total_cost = abs(new_quantity) * fill.price
            else:
                # Adding to existing position
                new_total_cost = self.total_cost + (abs(fill_quantity) * fill.price)
                self.average_entry_price = new_total_cost / abs(new_quantity)
                self.total_cost = new_total_cost
                self.quantity = new_quantity
        
        # Update fees and trade count
        self.total_fees += fill.fee
        self.trade_count += 1
        self.last_update = fill.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary."""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_entry_price': self.average_entry_price,
            'total_cost': self.total_cost,
            'realized_pnl': self.realized_pnl,
            'total_fees': self.total_fees,
            'trade_count': self.trade_count,
            'last_update': self.last_update,
            'notional_value': self.notional_value,
            'is_long': self.is_long,
            'is_short': self.is_short,
            'is_flat': self.is_flat
        }


@dataclass
class PortfolioSnapshot:
    """
    Portfolio snapshot at a point in time.
    
    Captures complete portfolio state including cash, positions,
    and calculated metrics for historical tracking.
    """
    timestamp: int
    cash_balance: float
    positions: Dict[str, Position]
    market_prices: Dict[str, float]
    total_value: float = 0.0
    total_pnl: float = 0.0
    total_fees: float = 0.0
    
    def __post_init__(self):
        """Calculate derived values."""
        position_value = sum(
            pos.quantity * self.market_prices.get(pos.symbol, pos.average_entry_price)
            for pos in self.positions.values()
        )
        self.total_value = self.cash_balance + position_value
        
        self.total_pnl = sum(
            pos.total_pnl(self.market_prices.get(pos.symbol, pos.average_entry_price))
            for pos in self.positions.values()
        )
        
        self.total_fees = sum(pos.total_fees for pos in self.positions.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'timestamp': self.timestamp,
            'cash_balance': self.cash_balance,
            'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()},
            'market_prices': self.market_prices,
            'total_value': self.total_value,
            'total_pnl': self.total_pnl,
            'total_fees': self.total_fees
        }


class PortfolioManager:
    """
    Portfolio manager for tracking positions, cash, and P&L.
    
    Provides comprehensive portfolio management including position tracking,
    P&L calculation, risk metrics, and historical snapshots.
    """
    
    def __init__(self, initial_cash: float = 10000.0):
        """
        Initialize portfolio manager.
        
        Args:
            initial_cash: Starting cash balance
        """
        self.initial_cash = initial_cash
        self.cash_balance = initial_cash
        self.positions: Dict[str, Position] = {}
        self.market_prices: Dict[str, float] = {}
        
        # History tracking
        self.trade_history: List[Fill] = []
        self.snapshots: List[PortfolioSnapshot] = []
        
        # Statistics
        self.total_trades = 0
        self.total_volume = 0.0
        self.total_fees = 0.0
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def total_value(self) -> float:
        """Calculate total portfolio value."""
        position_value = sum(
            pos.quantity * self.market_prices.get(pos.symbol, pos.average_entry_price)
            for pos in self.positions.values()
        )
        return self.cash_balance + position_value
    
    @property
    def total_pnl(self) -> float:
        """Calculate total P&L."""
        return self.total_value - self.initial_cash
    
    @property
    def total_return_percent(self) -> float:
        """Calculate total return percentage."""
        return (self.total_pnl / self.initial_cash) * 100
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L."""
        return sum(
            pos.unrealized_pnl(self.market_prices.get(pos.symbol, pos.average_entry_price))
            for pos in self.positions.values()
        )
    
    @property
    def realized_pnl(self) -> float:
        """Calculate total realized P&L."""
        return sum(pos.realized_pnl for pos in self.positions.values())
    
    @property
    def active_positions(self) -> Dict[str, Position]:
        """Get all active (non-flat) positions."""
        return {symbol: pos for symbol, pos in self.positions.items() if not pos.is_flat}
    
    def get_position(self, symbol: str) -> Position:
        """
        Get position for symbol (creates if doesn't exist).
        
        Args:
            symbol: Symbol to get position for
            
        Returns:
            Position object
        """
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]
    
    def update_market_price(self, symbol: str, price: float) -> None:
        """
        Update market price for a symbol.
        
        Args:
            symbol: Symbol to update
            price: New market price
        """
        self.market_prices[symbol] = price
    
    def apply_fill(self, fill: Fill) -> None:
        """
        Apply a fill to the portfolio.
        
        Args:
            fill: Fill to apply
        """
        # Get or create position
        position = self.get_position(fill.symbol)
        
        # Update cash balance
        if fill.side == OrderSide.BUY:
            self.cash_balance -= fill.notional_value + fill.fee
        else:
            self.cash_balance += fill.notional_value - fill.fee
        
        # Update position
        position.update_position(fill)
        
        # Update statistics
        self.total_trades += 1
        self.total_volume += fill.notional_value
        self.total_fees += fill.fee
        
        # Add to trade history
        self.trade_history.append(fill)
        
        self.logger.info(
            f"Applied fill: {fill.symbol} {fill.side.value} {fill.quantity} @ {fill.price} "
            f"(fee: {fill.fee}) - Position: {position.quantity}, Cash: {self.cash_balance:.2f}"
        )
    
    def can_afford_order(self, symbol: str, side: OrderSide, quantity: float, price: float, fee_rate: float = 0.001) -> bool:
        """
        Check if portfolio can afford an order.
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            price: Order price
            fee_rate: Fee rate for calculation
            
        Returns:
            True if order is affordable
        """
        if side == OrderSide.BUY:
            # Check cash for buy order
            cost = quantity * price * (1 + fee_rate)
            return self.cash_balance >= cost
        else:
            # Check position for sell order
            position = self.get_position(symbol)
            return position.quantity >= quantity
    
    def get_buying_power(self, price: float, fee_rate: float = 0.001) -> float:
        """
        Calculate buying power at given price.
        
        Args:
            price: Price to calculate buying power at
            fee_rate: Fee rate to include
            
        Returns:
            Maximum quantity that can be bought
        """
        if price <= 0:
            return 0.0
        
        cost_per_unit = price * (1 + fee_rate)
        return self.cash_balance / cost_per_unit
    
    def create_snapshot(self) -> PortfolioSnapshot:
        """
        Create a portfolio snapshot.
        
        Returns:
            Portfolio snapshot
        """
        snapshot = PortfolioSnapshot(
            timestamp=int(datetime.now(timezone.utc).timestamp() * 1000),
            cash_balance=self.cash_balance,
            positions=self.positions.copy(),
            market_prices=self.market_prices.copy()
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate portfolio performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'total_volume': 0.0,
                'total_fees': 0.0,
                'total_pnl': 0.0,
                'return_percent': 0.0,
                'win_rate': 0.0,
                'average_trade_pnl': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Calculate trade-level P&L
        trade_pnls = []
        wins = 0
        
        for position in self.positions.values():
            if position.trade_count > 0:
                # Simplified: assume each position represents completed trades
                avg_pnl = position.realized_pnl / position.trade_count if position.trade_count > 0 else 0
                trade_pnls.extend([avg_pnl] * position.trade_count)
                if avg_pnl > 0:
                    wins += position.trade_count
        
        # Calculate metrics
        win_rate = (wins / len(trade_pnls)) * 100 if trade_pnls else 0
        avg_trade_pnl = sum(trade_pnls) / len(trade_pnls) if trade_pnls else 0
        
        # Simple drawdown calculation using snapshots
        max_drawdown = 0.0
        if len(self.snapshots) > 1:
            peak_value = self.initial_cash
            for snapshot in self.snapshots:
                if snapshot.total_value > peak_value:
                    peak_value = snapshot.total_value
                drawdown = (peak_value - snapshot.total_value) / peak_value
                max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_trades': self.total_trades,
            'total_volume': self.total_volume,
            'total_fees': self.total_fees,
            'total_pnl': self.total_pnl,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'return_percent': self.total_return_percent,
            'win_rate': win_rate,
            'average_trade_pnl': avg_trade_pnl,
            'max_drawdown': max_drawdown * 100,  # Convert to percentage
            'active_positions': len(self.active_positions),
            'cash_balance': self.cash_balance,
            'total_value': self.total_value
        }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate portfolio risk metrics.
        
        Returns:
            Dictionary of risk metrics
        """
        active_pos = self.active_positions
        
        if not active_pos:
            return {
                'position_count': 0,
                'total_exposure': 0.0,
                'largest_position_percent': 0.0,
                'concentration_risk': 0.0,
                'leverage_ratio': 0.0
            }
        
        # Calculate exposures
        exposures = {}
        total_exposure = 0.0
        
        for symbol, position in active_pos.items():
            market_price = self.market_prices.get(symbol, position.average_entry_price)
            exposure = abs(position.quantity * market_price)
            exposures[symbol] = exposure
            total_exposure += exposure
        
        # Find largest position
        largest_exposure = max(exposures.values()) if exposures else 0.0
        largest_position_percent = (largest_exposure / self.total_value) * 100 if self.total_value > 0 else 0.0
        
        # Calculate concentration (Herfindahl index)
        concentration = sum((exp / total_exposure) ** 2 for exp in exposures.values()) if total_exposure > 0 else 0.0
        
        # Simple leverage calculation
        leverage_ratio = total_exposure / self.total_value if self.total_value > 0 else 0.0
        
        return {
            'position_count': len(active_pos),
            'total_exposure': total_exposure,
            'largest_position_percent': largest_position_percent,
            'concentration_risk': concentration * 100,  # Convert to percentage
            'leverage_ratio': leverage_ratio
        }
    
    def reset(self, new_initial_cash: Optional[float] = None) -> None:
        """
        Reset portfolio to initial state.
        
        Args:
            new_initial_cash: New initial cash amount (optional)
        """
        if new_initial_cash is not None:
            self.initial_cash = new_initial_cash
        
        self.cash_balance = self.initial_cash
        self.positions.clear()
        self.market_prices.clear()
        self.trade_history.clear()
        self.snapshots.clear()
        
        self.total_trades = 0
        self.total_volume = 0.0
        self.total_fees = 0.0
        
        self.logger.info(f"Portfolio reset with initial cash: {self.initial_cash}")
    
    def export_state(self) -> Dict[str, Any]:
        """
        Export portfolio state to dictionary.
        
        Returns:
            Complete portfolio state
        """
        return {
            'initial_cash': self.initial_cash,
            'cash_balance': self.cash_balance,
            'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()},
            'market_prices': self.market_prices,
            'trade_history': [fill.to_dict() for fill in self.trade_history],
            'performance_metrics': self.get_performance_metrics(),
            'risk_metrics': self.get_risk_metrics(),
            'total_value': self.total_value,
            'total_pnl': self.total_pnl,
            'export_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def to_json(self) -> str:
        """Export portfolio state to JSON string."""
        return json.dumps(self.export_state(), indent=2)