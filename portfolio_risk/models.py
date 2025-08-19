"""
Core data models for the Portfolio and Risk Engine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict

class OrderSide(Enum):
    """Defines the side of an order."""
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Fill:
    """
    Represents a single trade execution (a fill).

    This object is created by the Execution Engine and passed to the
    PortfolioManager to update the portfolio state.
    """
    symbol: str
    side: OrderSide
    price: float
    quantity: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    fee: float = 0.0
    fee_currency: str | None = None

@dataclass
class Position:
    """
    Represents an open position for a single symbol.
    """
    symbol: str
    side: OrderSide
    entry_price: float
    quantity: float
    leverage: float = 1.0
    unrealized_pnl: float = 0.0
    last_update: datetime = field(default_factory=datetime.utcnow)

    def update_pnl(self, mark_price: float):
        """Updates the unrealized PnL based on the current mark price."""
        price_diff = mark_price - self.entry_price
        if self.side == OrderSide.SELL:
            price_diff = -price_diff
        
        self.unrealized_pnl = price_diff * self.quantity
        self.last_update = datetime.utcnow()

@dataclass
class Trade:
    """
    Represents a completed trade with an entry and an exit.
    """
    symbol: str
    entry_timestamp: datetime
    exit_timestamp: datetime
    side: OrderSide
    quantity: float
    entry_price: float
    exit_price: float
    realized_pnl: float
    fees: float = 0.0

@dataclass
class PortfolioState:
    """
    A snapshot of the entire portfolio's state at a moment in time.
    """
    timestamp: datetime
    equity: float
    free_balance: float
    open_positions: Dict[str, Position]
    trade_history: List[Trade]
    equity_curve: List[tuple[datetime, float]] = field(default_factory=list)

