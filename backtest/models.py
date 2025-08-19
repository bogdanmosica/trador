"""
Core Data Models for Backtesting

Contains essential data structures for orders, trades, and portfolio tracking.
These models form the foundation of the backtesting engine's state management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class OrderType(Enum):
    """Order type enumeration for different execution styles."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    """Order status enumeration for tracking order lifecycle."""
    PENDING = "PENDING"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TimeInForce(Enum):
    """Time in force enumeration for order validity duration."""
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill
    DAY = "DAY"  # Good for Day


@dataclass
class Order:
    """
    Represents a trading order with all necessary execution parameters.
    
    Encapsulates order details including type, quantity, pricing, and timing
    constraints. Forms the basis for execution simulation and fill tracking.
    """
    symbol: str
    side: str  # 'BUY' or 'SELL'
    order_type: OrderType
    quantity: float
    timestamp: datetime
    time_in_force: TimeInForce = TimeInForce.GTC
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    remaining_quantity: Optional[float] = None
    average_fill_price: Optional[float] = None
    fees: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize remaining quantity if not provided."""
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side.upper() == 'BUY'
    
    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side.upper() == 'SELL'
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_partial_filled(self) -> bool:
        """Check if order is partially filled."""
        return self.status == OrderStatus.PARTIAL_FILLED
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active (pending or partial)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED]


@dataclass
class Trade:
    """
    Represents a completed trade (order fill) with execution details.
    
    Records the actual execution of an order or portion thereof, including
    price, quantity, fees, and timing information for portfolio tracking.
    """
    trade_id: str
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    timestamp: datetime
    fees: float = 0.0
    fee_currency: str = "USDT"
    is_maker: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def notional_value(self) -> float:
        """Calculate the notional value of the trade."""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Calculate the net value after fees."""
        if self.side.upper() == 'BUY':
            return -(self.notional_value + self.fees)
        else:
            return self.notional_value - self.fees


@dataclass
class PositionState:
    """
    Represents the current position state for a symbol.
    
    Tracks position size, entry details, unrealized PnL, and position
    history for comprehensive portfolio management.
    """
    symbol: str
    quantity: float
    average_entry_price: float
    entry_time: datetime
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_fees: float = 0.0
    trade_count: int = 0
    last_update: Optional[datetime] = None
    
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
        """Calculate notional value of position."""
        return abs(self.quantity) * self.average_entry_price


@dataclass
class MarketSnapshot:
    """
    Represents market data at a specific point in time.
    
    Extends the strategy module's MarketData with additional fields
    needed for realistic execution simulation including bid/ask spreads.
    """
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    
    def __post_init__(self):
        """Calculate bid/ask if not provided, using close price."""
        if self.bid is None or self.ask is None:
            # Estimate spread as 0.1% of close price for simulation
            estimated_spread = self.close * 0.001
            self.bid = self.close - (estimated_spread / 2)
            self.ask = self.close + (estimated_spread / 2)
            self.spread = estimated_spread
        elif self.spread is None:
            self.spread = self.ask - self.bid


@dataclass
class BacktestConfig:
    """
    Configuration parameters for backtest execution.
    
    Centralizes all configurable aspects of the backtesting process
    including fees, slippage, latency, and execution parameters.
    """
    # Fee structure
    maker_fee: float = 0.001  # 0.1%
    taker_fee: float = 0.001  # 0.1%
    
    # Slippage simulation
    market_order_slippage: float = 0.0005  # 0.05%
    limit_order_slippage: float = 0.0  # No slippage for limit orders
    
    # Execution simulation
    execution_latency_ms: int = 250  # Round-trip latency
    partial_fill_probability: float = 0.1  # 10% chance of partial fills
    
    # Portfolio management
    initial_balance: float = 10000.0
    base_currency: str = "USDT"
    max_leverage: float = 1.0  # Spot trading by default
    
    # Risk management
    max_position_size: float = 0.95  # Max 95% of portfolio
    min_order_size: float = 10.0  # Minimum order size in base currency
    
    # Data and caching
    cache_data: bool = True
    data_cache_path: str = "./data_cache"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            'maker_fee': self.maker_fee,
            'taker_fee': self.taker_fee,
            'market_order_slippage': self.market_order_slippage,
            'limit_order_slippage': self.limit_order_slippage,
            'execution_latency_ms': self.execution_latency_ms,
            'partial_fill_probability': self.partial_fill_probability,
            'initial_balance': self.initial_balance,
            'base_currency': self.base_currency,
            'max_leverage': self.max_leverage,
            'max_position_size': self.max_position_size,
            'min_order_size': self.min_order_size,
            'cache_data': self.cache_data,
            'data_cache_path': self.data_cache_path
        }