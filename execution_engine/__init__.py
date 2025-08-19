"""
Execution Engine Module

Comprehensive order execution system for crypto trading bots supporting
both simulated (backtest/paper) and live trading environments.
"""

from .models import (
    Signal, Order, Fill, OrderStatus, OrderSide, OrderType, 
    TimeInForce, ExecutionConfig, validate_signal, validate_order
)

from .engines.base import (
    ExecutionEngine, ExecutionEngineError, OrderValidationError,
    InsufficientBalanceError, PositionLimitError, OrderNotFoundError
)

from .engines.simulated import SimulatedExecutionEngine, MarketData
from .engines.live import (
    LiveExecutionEngine, ExchangeConfig, BinanceLiveExecutionEngine,
    CoinbaseLiveExecutionEngine
)

from .portfolio.manager import PortfolioManager, Position, PortfolioSnapshot
from .utils.logger import ExecutionLogger, TradeJournal

__version__ = "1.0.0"
__author__ = "Trading Bot Development Team"

__all__ = [
    # Core models
    "Signal", "Order", "Fill", "OrderStatus", "OrderSide", "OrderType", 
    "TimeInForce", "ExecutionConfig", "validate_signal", "validate_order",
    
    # Engine interfaces
    "ExecutionEngine", "ExecutionEngineError", "OrderValidationError",
    "InsufficientBalanceError", "PositionLimitError", "OrderNotFoundError",
    
    # Simulated execution
    "SimulatedExecutionEngine", "MarketData",
    
    # Live execution
    "LiveExecutionEngine", "ExchangeConfig", "BinanceLiveExecutionEngine",
    "CoinbaseLiveExecutionEngine",
    
    # Portfolio management
    "PortfolioManager", "Position", "PortfolioSnapshot",
    
    # Logging and tracking
    "ExecutionLogger", "TradeJournal"
]