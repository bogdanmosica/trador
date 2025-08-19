"""
Base class for all risk rules.

This module defines the abstract base class (ABC) that all risk rule
implementations must inherit from. This ensures that the RiskEngine can
interact with any rule in a consistent way.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models import PortfolioState, Fill

class RiskRule(ABC):
    """Abstract base class for a risk management rule."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def check(self, portfolio_state: PortfolioState, proposed_fill: Fill | None = None) -> tuple[bool, str]:
        """
        Evaluates the risk rule.

        Args:
            portfolio_state: The current state of the portfolio.
            proposed_fill: The proposed trade to be executed. This is None for post-trade checks.

        Returns:
            A tuple containing:
            - bool: True if the rule passes, False otherwise.
            - str: A message describing the result or violation.
        """
        pass
