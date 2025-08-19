"""
Abstract Execution Engine Base Class

Defines the interface for all execution engines, providing a common
contract for signal processing, order management, and portfolio integration.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timezone
import logging
import uuid

from ..models import Signal, Order, Fill, OrderStatus, ExecutionConfig


class ExecutionEngine(ABC):
    """
    Abstract base class for execution engines.
    
    Defines the interface that all execution engines must implement,
    supporting both simulated and live trading environments.
    """
    
    def __init__(self, config: ExecutionConfig):
        """
        Initialize execution engine.
        
        Args:
            config: Execution configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Order tracking
        self._orders: Dict[str, Order] = {}
        self._active_orders: Dict[str, Order] = {}
        self._order_history: List[Order] = []
        self._fills: List[Fill] = []
        
        # Event callbacks
        self._on_order_update: Optional[Callable[[Order], None]] = None
        self._on_fill: Optional[Callable[[Fill], None]] = None
        self._on_order_rejected: Optional[Callable[[Order], None]] = None
        
        # Engine state
        self._is_running = False
        self._order_counter = 0
    
    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._is_running
    
    @property
    def orders(self) -> Dict[str, Order]:
        """Get all orders."""
        return self._orders.copy()
    
    @property
    def active_orders(self) -> Dict[str, Order]:
        """Get active orders."""
        return self._active_orders.copy()
    
    @property
    def order_history(self) -> List[Order]:
        """Get order history."""
        return self._order_history.copy()
    
    @property
    def fills(self) -> List[Fill]:
        """Get all fills."""
        return self._fills.copy()
    
    def set_order_update_callback(self, callback: Callable[[Order], None]) -> None:
        """Set callback for order updates."""
        self._on_order_update = callback
    
    def set_fill_callback(self, callback: Callable[[Fill], None]) -> None:
        """Set callback for fills."""
        self._on_fill = callback
    
    def set_order_rejected_callback(self, callback: Callable[[Order], None]) -> None:
        """Set callback for order rejections."""
        self._on_order_rejected = callback
    
    def generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_counter += 1
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        return f"order_{timestamp}_{self._order_counter}_{uuid.uuid4().hex[:8]}"
    
    def generate_fill_id(self) -> str:
        """Generate unique fill ID."""
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        return f"fill_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    def _validate_signal(self, signal: Signal) -> bool:
        """
        Validate signal before processing.
        
        Args:
            signal: Signal to validate
            
        Returns:
            True if signal is valid
        """
        # Basic validation
        if signal.quantity <= 0:
            self.logger.error(f"Invalid signal quantity: {signal.quantity}")
            return False
        
        if signal.quantity < self.config.min_order_size:
            self.logger.error(f"Signal quantity {signal.quantity} below minimum {self.config.min_order_size}")
            return False
        
        return True
    
    def _add_order(self, order: Order) -> None:
        """
        Add order to tracking.
        
        Args:
            order: Order to add
        """
        self._orders[order.order_id] = order
        if order.is_active:
            self._active_orders[order.order_id] = order
        
        self.logger.info(f"Added order {order.order_id}: {order.symbol} {order.side.value} {order.quantity}")
    
    def _update_order_status(self, order: Order, new_status: OrderStatus, reason: Optional[str] = None) -> None:
        """
        Update order status and handle state transitions.
        
        Args:
            order: Order to update
            new_status: New order status
            reason: Optional reason for status change
        """
        old_status = order.status
        order.status = new_status
        order.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        if reason and new_status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            order.rejection_reason = reason
        
        # Update active orders tracking
        if new_status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            if order.order_id in self._active_orders:
                del self._active_orders[order.order_id]
                self._order_history.append(order)
        
        self.logger.info(f"Order {order.order_id} status: {old_status.value} -> {new_status.value}")
        
        # Trigger callback
        if self._on_order_update:
            self._on_order_update(order)
        
        # Trigger rejection callback
        if new_status == OrderStatus.REJECTED and self._on_order_rejected:
            self._on_order_rejected(order)
    
    def _add_fill(self, order: Order, fill: Fill) -> None:
        """
        Add fill to order and update state.
        
        Args:
            order: Order that was filled
            fill: Fill details
        """
        # Add fill to order
        order.add_fill(fill)
        
        # Add to fills list
        self._fills.append(fill)
        
        self.logger.info(
            f"Fill added to order {order.order_id}: "
            f"{fill.quantity} @ {fill.price} (fee: {fill.fee})"
        )
        
        # Update order status based on fill
        if order.filled_quantity >= order.quantity:
            self._update_order_status(order, OrderStatus.FILLED)
        elif order.filled_quantity > 0:
            self._update_order_status(order, OrderStatus.PARTIALLY_FILLED)
        
        # Trigger callback
        if self._on_fill:
            self._on_fill(fill)
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the execution engine.
        
        Initialize any necessary connections or resources.
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the execution engine.
        
        Clean up connections and resources.
        """
        pass
    
    @abstractmethod
    async def submit_signal(self, signal: Signal) -> Order:
        """
        Submit a trading signal for execution.
        
        Args:
            signal: Trading signal to execute
            
        Returns:
            Order created from the signal
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, reason: str = "User cancellation") -> bool:
        """
        Cancel an active order.
        
        Args:
            order_id: ID of order to cancel
            reason: Reason for cancellation
            
        Returns:
            True if cancellation was successful
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        Get current status of an order.
        
        Args:
            order_id: ID of order to check
            
        Returns:
            Order status or None if order not found
        """
        pass
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID to retrieve
            
        Returns:
            Order object or None if not found
        """
        return self._orders.get(order_id)
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """
        Get all orders for a symbol.
        
        Args:
            symbol: Symbol to filter by
            
        Returns:
            List of orders for the symbol
        """
        return [order for order in self._orders.values() if order.symbol == symbol]
    
    def get_active_orders_by_symbol(self, symbol: str) -> List[Order]:
        """
        Get active orders for a symbol.
        
        Args:
            symbol: Symbol to filter by
            
        Returns:
            List of active orders for the symbol
        """
        return [order for order in self._active_orders.values() if order.symbol == symbol]
    
    def get_fills_by_symbol(self, symbol: str) -> List[Fill]:
        """
        Get all fills for a symbol.
        
        Args:
            symbol: Symbol to filter by
            
        Returns:
            List of fills for the symbol
        """
        return [fill for fill in self._fills if fill.symbol == symbol]
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get execution engine statistics.
        
        Returns:
            Dictionary of execution statistics
        """
        total_orders = len(self._orders)
        filled_orders = len([o for o in self._orders.values() if o.status == OrderStatus.FILLED])
        partial_orders = len([o for o in self._orders.values() if o.status == OrderStatus.PARTIALLY_FILLED])
        cancelled_orders = len([o for o in self._orders.values() if o.status == OrderStatus.CANCELLED])
        rejected_orders = len([o for o in self._orders.values() if o.status == OrderStatus.REJECTED])
        
        total_fills = len(self._fills)
        total_volume = sum(fill.notional_value for fill in self._fills)
        total_fees = sum(fill.fee for fill in self._fills)
        
        return {
            'total_orders': total_orders,
            'active_orders': len(self._active_orders),
            'filled_orders': filled_orders,
            'partially_filled_orders': partial_orders,
            'cancelled_orders': cancelled_orders,
            'rejected_orders': rejected_orders,
            'total_fills': total_fills,
            'total_volume': total_volume,
            'total_fees': total_fees,
            'fill_rate': filled_orders / total_orders if total_orders > 0 else 0,
            'average_fill_price': sum(fill.price for fill in self._fills) / total_fills if total_fills > 0 else 0
        }
    
    def clear_history(self) -> None:
        """Clear order and fill history."""
        self._order_history.clear()
        self._fills.clear()
        self.logger.info("Execution history cleared")
    
    def export_history(self) -> Dict[str, Any]:
        """
        Export execution history.
        
        Returns:
            Dictionary containing all orders and fills
        """
        return {
            'orders': [order.to_dict() for order in self._orders.values()],
            'fills': [fill.to_dict() for fill in self._fills],
            'statistics': self.get_execution_statistics(),
            'config': self.config.to_dict(),
            'export_timestamp': datetime.now(timezone.utc).isoformat()
        }


class ExecutionEngineError(Exception):
    """Base exception for execution engine errors."""
    pass


class OrderValidationError(ExecutionEngineError):
    """Raised when order validation fails."""
    pass


class InsufficientBalanceError(ExecutionEngineError):
    """Raised when there is insufficient balance for an order."""
    pass


class PositionLimitError(ExecutionEngineError):
    """Raised when position limits would be exceeded."""
    pass


class OrderNotFoundError(ExecutionEngineError):
    """Raised when an order is not found."""
    pass