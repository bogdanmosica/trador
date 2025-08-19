"""
Manages the state of a single strategy's portfolio.

This class is responsible for:
- Tracking account balances, equity, and PnL.
- Managing open positions.
- Recording trade history.
- Updating portfolio state based on fills from the Execution Engine.
"""

from datetime import datetime
from typing import Dict, List

from .models import Fill, Position, Trade, PortfolioState, OrderSide

class PortfolioManager:
    """Manages the portfolio for a single trading strategy."""

    def __init__(self, strategy_id: str, initial_equity: float):
        self.strategy_id = strategy_id
        self.state = PortfolioState(
            timestamp=datetime.utcnow(),
            equity=initial_equity,
            free_balance=initial_equity,
            open_positions={},
            trade_history=[]
        )
        self.state.equity_curve.append((self.state.timestamp, self.state.equity))

    @property
    def unrealized_pnl(self) -> float:
        """Calculates the total unrealized PnL across all open positions."""
        return sum(pos.unrealized_pnl for pos in self.state.open_positions.values())

    @property
    def total_equity(self) -> float:
        """Calculates the total current equity of the portfolio."""
        return self.state.free_balance + self.unrealized_pnl

    def update_market_price(self, symbol: str, mark_price: float):
        """
        Updates the unrealized PnL of an open position based on a new mark price.
        """
        if symbol in self.state.open_positions:
            self.state.open_positions[symbol].update_pnl(mark_price)
            self._update_equity()

    def apply_fill(self, fill: Fill):
        """
        Updates the portfolio state based on a new trade execution (fill).
        This is the primary method for interacting with the PortfolioManager.
        """
        # Note: This is a simplified implementation. A real implementation would
        # need to handle margin, collateral, and more complex fee structures.

        if fill.symbol in self.state.open_positions:
            self._handle_closing_or_modifying_position(fill)
        else:
            self._handle_opening_position(fill)

        self.state.free_balance -= fill.fee
        self._update_equity()

    def _handle_opening_position(self, fill: Fill):
        """Creates a new position based on an opening fill."""
        new_position = Position(
            symbol=fill.symbol,
            side=fill.side,
            entry_price=fill.price,
            quantity=fill.quantity
        )
        self.state.open_positions[fill.symbol] = new_position
        # In a real margin system, collateral would be locked here.

    def _handle_closing_or_modifying_position(self, fill: Fill):
        """Closes or modifies an existing position."""
        position = self.state.open_positions[fill.symbol]

        if fill.side == position.side:
            # Increase position size (e.g., averaging down)
            # This is a simplified calculation. A real implementation would use a VWAP.
            position.entry_price = (position.entry_price * position.quantity + fill.price * fill.quantity) / (position.quantity + fill.quantity)
            position.quantity += fill.quantity
        else:
            # Reduce or close position
            if fill.quantity >= position.quantity:
                # Position is fully closed
                self._close_position(fill, position)
            else:
                # Position is partially closed
                self._reduce_position(fill, position)

    def _close_position(self, fill: Fill, position: Position):
        """Handles the full closure of a position and records the trade."""
        realized_pnl = (fill.price - position.entry_price) * position.quantity
        if position.side == OrderSide.SELL:
            realized_pnl = -realized_pnl

        trade = Trade(
            symbol=position.symbol,
            side=position.side,
            entry_timestamp=position.last_update, # Simplified
            exit_timestamp=fill.timestamp,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=fill.price,
            realized_pnl=realized_pnl - fill.fee,
            fees=fill.fee
        )
        self.state.trade_history.append(trade)
        self.state.free_balance += realized_pnl
        del self.state.open_positions[position.symbol]

    def _reduce_position(self, fill: Fill, position: Position):
        """Handles a partial closure of a position."""
        realized_pnl = (fill.price - position.entry_price) * fill.quantity
        if position.side == OrderSide.SELL:
            realized_pnl = -realized_pnl
        
        # Create a trade for the closed portion
        trade = Trade(
            symbol=position.symbol,
            side=position.side,
            entry_timestamp=position.last_update, # Simplified
            exit_timestamp=fill.timestamp,
            quantity=fill.quantity,
            entry_price=position.entry_price,
            exit_price=fill.price,
            realized_pnl=realized_pnl - fill.fee,
            fees=fill.fee
        )
        self.state.trade_history.append(trade)
        self.state.free_balance += realized_pnl
        position.quantity -= fill.quantity

    def _update_equity(self):
        """Updates the equity curve with the latest portfolio value."""
        now = datetime.utcnow()
        self.state.equity = self.total_equity
        self.state.equity_curve.append((now, self.state.equity))
        self.state.timestamp = now
