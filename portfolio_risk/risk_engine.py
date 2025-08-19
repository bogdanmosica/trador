"""
Evaluates pre-trade and post-trade risk rules.

This module contains the RiskEngine, which is responsible for loading and
evaluating a set of modular risk rules for a given strategy.
"""

from typing import List, Dict, Any, Type

from .models import PortfolioState, Fill
from .rules.base_rule import RiskRule

# A simple rule registry for demonstration purposes.
# In a real application, this might use dynamic imports or a plugin system.
from .rules.max_position_size import MaxPositionSize
from .rules.max_drawdown import MaxDrawdown

RULE_REGISTRY: Dict[str, Type[RiskRule]] = {
    "max_position_size": MaxPositionSize,
    "max_drawdown": MaxDrawdown,
    # Add other rules here as they are created
}

class RiskEngine:
    """Manages and evaluates a set of risk rules for a strategy."""

    def __init__(self, portfolio_state: PortfolioState, rule_configs: List[Dict[str, Any]]):
        self.portfolio_state = portfolio_state
        self.rules: List[RiskRule] = self._load_rules(rule_configs)
        self.violations: List[str] = []

    def _load_rules(self, rule_configs: List[Dict[str, Any]]) -> List[RiskRule]:
        """Instantiates risk rules based on the provided configurations."""
        loaded_rules = []
        for config in rule_configs:
            rule_name = config.get("name")
            if not rule_name or rule_name not in RULE_REGISTRY:
                # In a real app, you'd want more robust error handling/logging
                print(f"Warning: Rule '{rule_name}' not found or name is missing. Skipping.")
                continue
            
            rule_class = RULE_REGISTRY[rule_name]
            loaded_rules.append(rule_class(config))
        return loaded_rules

    def check_pre_trade(self, proposed_fill: Fill) -> tuple[bool, List[str]]:
        """
        Checks all pre-trade rules against a proposed trade.

        Args:
            proposed_fill: The trade being considered.

        Returns:
            A tuple containing:
            - bool: True if all rules pass, False otherwise.
            - list[str]: A list of violation messages.
        """
        self.violations.clear()
        all_pass = True

        for rule in self.rules:
            is_pass, message = rule.check(self.portfolio_state, proposed_fill)
            if not is_pass:
                all_pass = False
                self.violations.append(f"[{rule.__class__.__name__}] {message}")
        
        return all_pass, self.violations

    def check_post_trade(self) -> tuple[bool, List[str]]:
        """
        Checks all post-trade rules (e.g., max drawdown).

        Returns:
            A tuple containing:
            - bool: True if all rules pass, False otherwise.
            - list[str]: A list of violation messages.
        """
        self.violations.clear()
        all_pass = True

        for rule in self.rules:
            # Pass None for proposed_fill to indicate a post-trade check
            is_pass, message = rule.check(self.portfolio_state, None)
            if not is_pass:
                all_pass = False
                self.violations.append(f"[{rule.__class__.__name__}] {message}")
        
        return all_pass, self.violations

    def check_for_critical_violations(self) -> tuple[bool, List[str]]:
        """
        Checks for critical, post-trade violations that might trigger a kill-switch.

        Returns:
            A tuple containing:
            - bool: True if a critical violation is found, False otherwise.
            - list[str]: A list of critical violation messages.
        """
        critical_violations = []
        for rule in self.rules:
            # For now, we'll consider MaxDrawdown a critical rule.
            # A more robust implementation might have a 'critical' flag in the rule config.
            if isinstance(rule, MaxDrawdown):
                is_pass, message = rule.check(self.portfolio_state, None)
                if not is_pass:
                    critical_violations.append(f"[{rule.__class__.__name__}] {message}")
        
        return len(critical_violations) > 0, critical_violations
