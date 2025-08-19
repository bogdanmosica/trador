"""
Core Data Models for Execution Engine

Defines the fundamental data structures for order execution including
signals, orders, fills, and related metadata for trade execution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import json
from decimal import Decimal


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status enumeration."""
    NEW = "new"
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(Enum):
    """Time in force enumeration."""
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    DAY = "day"  # Good for Day


@dataclass
class Signal:
    """
    Trading signal from strategy module.
    
    Represents the intent to enter or exit a position based on
    strategy analysis. Contains all necessary information for
    order generation.
    """
    symbol: str
    side: OrderSide
    quantity: float
    timestamp: int  # Unix timestamp in milliseconds
    strategy_id: str = "default"
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate signal data after initialization."""
        if self.quantity <= 0:
            raise ValueError("Signal quantity must be positive")
        
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("Limit orders require limit_price")
        
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and self.stop_price is None:
            raise ValueError("Stop orders require stop_price")
        
        if self.order_type == OrderType.STOP_LIMIT and self.limit_price is None:
            raise ValueError("Stop limit orders require both stop_price and limit_price")
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000, timezone.utc)
    
    @property
    def side_multiplier(self) -> int:
        """Return side multiplier for position calculations."""
        return 1 if self.side == OrderSide.BUY else -1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'timestamp': self.timestamp,
            'strategy_id': self.strategy_id,
            'order_type': self.order_type.value,
            'limit_price': self.limit_price,
            'stop_price': self.stop_price,
            'time_in_force': self.time_in_force.value,
            'metadata': self.metadata,
            'datetime': self.datetime.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """Create signal from dictionary."""
        return cls(
            symbol=data['symbol'],
            side=OrderSide(data['side']),
            quantity=data['quantity'],
            timestamp=data['timestamp'],
            strategy_id=data.get('strategy_id', 'default'),
            order_type=OrderType(data.get('order_type', 'market')),
            limit_price=data.get('limit_price'),
            stop_price=data.get('stop_price'),
            time_in_force=TimeInForce(data.get('time_in_force', 'gtc')),
            metadata=data.get('metadata', {})
        )
    
    def to_json(self) -> str:
        """Convert signal to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class Fill:
    """
    Order fill information.
    
    Represents a complete or partial execution of an order,
    including execution price, quantity, fees, and timing.
    """
    order_id: str
    fill_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: int  # Unix timestamp in milliseconds
    fee: float = 0.0
    fee_asset: str = "USDT"
    is_maker: bool = False
    trade_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate fill data after initialization."""
        if self.quantity <= 0:
            raise ValueError("Fill quantity must be positive")
        
        if self.price <= 0:
            raise ValueError("Fill price must be positive")
        
        if self.fee < 0:
            raise ValueError("Fill fee cannot be negative")
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000, timezone.utc)
    
    @property
    def notional_value(self) -> float:
        """Calculate notional value of the fill."""
        return self.quantity * self.price
    
    @property
    def net_amount(self) -> float:
        """Calculate net amount after fees."""
        if self.side == OrderSide.BUY:
            return self.notional_value + self.fee
        else:
            return self.notional_value - self.fee
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert fill to dictionary."""
        return {
            'order_id': self.order_id,
            'fill_id': self.fill_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'price': self.price,
            'timestamp': self.timestamp,
            'fee': self.fee,
            'fee_asset': self.fee_asset,
            'is_maker': self.is_maker,
            'trade_id': self.trade_id,
            'datetime': self.datetime.isoformat(),
            'notional_value': self.notional_value,
            'net_amount': self.net_amount
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fill':
        """Create fill from dictionary."""
        return cls(
            order_id=data['order_id'],
            fill_id=data['fill_id'],
            symbol=data['symbol'],
            side=OrderSide(data['side']),
            quantity=data['quantity'],
            price=data['price'],
            timestamp=data['timestamp'],
            fee=data.get('fee', 0.0),
            fee_asset=data.get('fee_asset', 'USDT'),
            is_maker=data.get('is_maker', False),
            trade_id=data.get('trade_id')
        )


@dataclass
class Order:
    """
    Order object representing a trading order.
    
    Tracks the complete lifecycle of an order from creation
    through execution, including partial fills and status changes.
    """
    order_id: str
    signal: Signal
    status: OrderStatus = OrderStatus.NEW
    created_at: Optional[int] = None  # Unix timestamp in milliseconds
    updated_at: Optional[int] = None  # Unix timestamp in milliseconds
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    fills: List[Fill] = field(default_factory=list)
    total_fee: float = 0.0
    rejection_reason: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = int(datetime.now(timezone.utc).timestamp() * 1000)
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    @property
    def symbol(self) -> str:
        """Get symbol from signal."""
        return self.signal.symbol
    
    @property
    def side(self) -> OrderSide:
        """Get side from signal."""
        return self.signal.side
    
    @property
    def quantity(self) -> float:
        """Get quantity from signal."""
        return self.signal.quantity
    
    @property
    def order_type(self) -> OrderType:
        """Get order type from signal."""
        return self.signal.order_type
    
    @property
    def remaining_quantity(self) -> float:
        """Calculate remaining quantity to be filled."""
        return max(0.0, self.quantity - self.filled_quantity)
    
    @property
    def fill_percentage(self) -> float:
        """Calculate fill percentage."""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in [OrderStatus.NEW, OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def created_datetime(self) -> datetime:
        """Convert created timestamp to datetime."""
        return datetime.fromtimestamp(self.created_at / 1000, timezone.utc)
    
    @property
    def updated_datetime(self) -> datetime:
        """Convert updated timestamp to datetime."""
        return datetime.fromtimestamp(self.updated_at / 1000, timezone.utc)
    
    def add_fill(self, fill: Fill) -> None:
        """
        Add a fill to the order and update order state.
        
        Args:
            fill: Fill object to add to the order
        """
        if fill.order_id != self.order_id:
            raise ValueError("Fill order_id does not match order")
        
        if fill.symbol != self.symbol:
            raise ValueError("Fill symbol does not match order")
        
        if fill.side != self.side:
            raise ValueError("Fill side does not match order")
        
        # Add the fill
        self.fills.append(fill)
        
        # Update filled quantity
        self.filled_quantity += fill.quantity
        
        # Update average fill price
        total_notional = sum(f.quantity * f.price for f in self.fills)
        self.average_fill_price = total_notional / self.filled_quantity
        
        # Update total fees
        self.total_fee += fill.fee
        
        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIALLY_FILLED
        
        # Update timestamp
        self.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    def cancel(self, reason: str = "User cancellation") -> None:
        """
        Cancel the order.
        
        Args:
            reason: Reason for cancellation
        """
        if not self.is_active:
            raise ValueError(f"Cannot cancel order with status {self.status}")
        
        self.status = OrderStatus.CANCELLED
        self.rejection_reason = reason
        self.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    def reject(self, reason: str) -> None:
        """
        Reject the order.
        
        Args:
            reason: Reason for rejection
        """
        self.status = OrderStatus.REJECTED
        self.rejection_reason = reason
        self.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary."""
        return {
            'order_id': self.order_id,
            'signal': self.signal.to_dict(),
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'average_fill_price': self.average_fill_price,
            'fill_percentage': self.fill_percentage,
            'total_fee': self.total_fee,
            'fills': [fill.to_dict() for fill in self.fills],
            'rejection_reason': self.rejection_reason,
            'created_datetime': self.created_datetime.isoformat(),
            'updated_datetime': self.updated_datetime.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Create order from dictionary."""
        order = cls(
            order_id=data['order_id'],
            signal=Signal.from_dict(data['signal']),
            status=OrderStatus(data['status']),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            filled_quantity=data.get('filled_quantity', 0.0),
            average_fill_price=data.get('average_fill_price', 0.0),
            total_fee=data.get('total_fee', 0.0),
            rejection_reason=data.get('rejection_reason')
        )
        
        # Add fills
        for fill_data in data.get('fills', []):
            fill = Fill.from_dict(fill_data)
            order.fills.append(fill)
        
        return order
    
    def to_json(self) -> str:
        """Convert order to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ExecutionConfig:
    """
    Configuration for execution engine behavior.
    
    Controls various aspects of order execution simulation
    including fees, slippage, and market impact modeling.
    """
    # Fee configuration
    maker_fee_rate: float = 0.001  # 0.1% maker fee
    taker_fee_rate: float = 0.001  # 0.1% taker fee
    
    # Slippage configuration
    market_slippage_bps: float = 5.0  # 5 basis points market order slippage
    limit_slippage_tolerance_bps: float = 1.0  # 1 bp tolerance for limit fills
    
    # Execution delays
    market_order_delay_ms: int = 100  # 100ms market order execution delay
    limit_order_delay_ms: int = 0    # No delay for limit orders
    
    # Position sizing
    max_position_size: Optional[float] = None  # Maximum position size
    min_order_size: float = 0.001  # Minimum order size
    
    # Risk controls
    enable_position_limits: bool = True
    enable_order_size_checks: bool = True
    enable_balance_checks: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.maker_fee_rate < 0 or self.taker_fee_rate < 0:
            raise ValueError("Fee rates cannot be negative")
        
        if self.market_slippage_bps < 0:
            raise ValueError("Slippage cannot be negative")
        
        if self.min_order_size <= 0:
            raise ValueError("Minimum order size must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'maker_fee_rate': self.maker_fee_rate,
            'taker_fee_rate': self.taker_fee_rate,
            'market_slippage_bps': self.market_slippage_bps,
            'limit_slippage_tolerance_bps': self.limit_slippage_tolerance_bps,
            'market_order_delay_ms': self.market_order_delay_ms,
            'limit_order_delay_ms': self.limit_order_delay_ms,
            'max_position_size': self.max_position_size,
            'min_order_size': self.min_order_size,
            'enable_position_limits': self.enable_position_limits,
            'enable_order_size_checks': self.enable_order_size_checks,
            'enable_balance_checks': self.enable_balance_checks
        }


def validate_signal(signal: Signal) -> bool:
    """
    Validate signal data integrity.
    
    Args:
        signal: Signal to validate
        
    Returns:
        True if signal is valid
    """
    try:
        # Check required fields
        if not signal.symbol or not isinstance(signal.symbol, str):
            return False
        
        if signal.quantity <= 0:
            return False
        
        if signal.timestamp <= 0:
            return False
        
        # Check order type specific requirements
        if signal.order_type == OrderType.LIMIT and signal.limit_price is None:
            return False
        
        if signal.order_type == OrderType.LIMIT and signal.limit_price <= 0:
            return False
        
        return True
    
    except Exception:
        return False


def validate_order(order: Order) -> bool:
    """
    Validate order data integrity.
    
    Args:
        order: Order to validate
        
    Returns:
        True if order is valid
    """
    try:
        # Validate signal
        if not validate_signal(order.signal):
            return False
        
        # Check filled quantity
        if order.filled_quantity < 0 or order.filled_quantity > order.quantity:
            return False
        
        # Check average fill price
        if order.filled_quantity > 0 and order.average_fill_price <= 0:
            return False
        
        # Validate fills
        total_fill_qty = sum(fill.quantity for fill in order.fills)
        if abs(total_fill_qty - order.filled_quantity) > 1e-8:
            return False
        
        return True
    
    except Exception:
        return False