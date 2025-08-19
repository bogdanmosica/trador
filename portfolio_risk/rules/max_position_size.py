"""
Risk rule to enforce a maximum position size.
"""

from typing import Any, Dict

from ..models import PortfolioState, Fill, OrderSide
from .base_rule import RiskRule

class MaxPositionSize(RiskRule):
    """Prevents trades that would result in a position larger than a set limit."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_size_usd = self.config.get("max_size_usd", float('inf'))

    def check(self, portfolio_state: PortfolioState, proposed_fill: Fill | None = None) -> tuple[bool, str]:
        """
        Checks if a proposed trade would exceed the maximum allowed position size.
        This check is only performed pre-trade.
        """
        if proposed_fill is None:
            return True, "Post-trade check not applicable for MaxPositionSize."

        symbol = proposed_fill.symbol
        current_position = portfolio_state.open_positions.get(symbol)
        
        proposed_value = proposed_fill.price * proposed_fill.quantity

        if current_position is None:
            # This is a new position
            if proposed_value > self.max_size_usd:
                return False, f"Proposed position value ({proposed_value:.2f} USD) exceeds max size ({self.max_size_usd:.2f} USD)."
        else:
            # This modifies an existing position
            current_value = current_position.entry_price * current_position.quantity
            if proposed_fill.side == current_position.side:
                # Increasing position
                new_total_value = current_value + proposed_value
                if new_total_value > self.max_size_usd:
                    return False, f"Increasing position would exceed max size. New value: {new_total_value:.2f} USD, Limit: {self.max_size_usd:.2f} USD."
            # If sides are opposite, it's a reduction, which is always allowed by this rule.

        return True, "Position size is within limits."
