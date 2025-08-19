"""
Risk rule to enforce a maximum drawdown limit.
"""

from typing import Any, Dict

from ..models import PortfolioState, Fill
from .base_rule import RiskRule

class MaxDrawdown(RiskRule):
    """Prevents trading if the portfolio's drawdown exceeds a set limit."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_drawdown_pct = self.config.get("max_drawdown_pct", 10.0)
        self.peak_equity = -float('inf')
        self.current_drawdown = 0.0

    def check(self, portfolio_state: PortfolioState, proposed_fill: Fill | None = None) -> tuple[bool, str]:
        """
        Checks if the current drawdown exceeds the maximum allowed percentage.
        This is a post-trade check, so it ignores the proposed_fill.
        """
        if proposed_fill is not None:
            return True, "Pre-trade check not applicable for MaxDrawdown."

        # Update peak equity
        if portfolio_state.equity > self.peak_equity:
            self.peak_equity = portfolio_state.equity

        # Calculate current drawdown
        if self.peak_equity > 0:
            drawdown = (self.peak_equity - portfolio_state.equity) / self.peak_equity
            self.current_drawdown = drawdown * 100
        else:
            self.current_drawdown = 0.0

        if self.current_drawdown > self.max_drawdown_pct:
            return False, f"Drawdown of {self.current_drawdown:.2f}% exceeds limit of {self.max_drawdown_pct:.2f}%."

        return True, f"Current drawdown is {self.current_drawdown:.2f}%, which is within the {self.max_drawdown_pct:.2f}% limit."
