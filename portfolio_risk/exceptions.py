"""
Custom exceptions for the Portfolio and Risk Engine.
"""

class PortfolioRiskError(Exception):
    """Base exception for all errors in the portfolio_risk module."""
    pass

class RiskViolationError(PortfolioRiskError):
    """Raised when a proposed action violates a risk rule."""
    def __init__(self, message: str, violations: list[str] | None = None):
        super().__init__(message)
        self.violations = violations or []
