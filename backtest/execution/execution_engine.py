"""
Execution Engine

Manages order lifecycle, execution simulation, and trade generation.
Coordinates between order management and fill simulation for realistic
backtesting execution.
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..models import Order, Trade, OrderStatus, MarketSnapshot, BacktestConfig
from .fill_simulator import FillSimulator


logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Manages order execution and trade generation for backtesting.
    
    Coordinates order submission, fill simulation, and trade recording
    to provide realistic execution behavior in backtests.
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize execution engine with configuration.
        
        Args:
            config (BacktestConfig): Backtesting configuration parameters
        """
        self.config = config
        self.fill_simulator = FillSimulator(config)
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self.order_sequence = 0
    
    def submit_order(self, order: Order) -> str:
        """
        Submit an order for execution.
        
        Args:
            order (Order): Order to submit
            
        Returns:
            str: Order ID
        """
        # Validate order
        if not self._validate_order(order):
            order.status = OrderStatus.REJECTED
            logger.warning(f"Order rejected: {order}")
            return order.order_id
        
        # Store order
        self.orders[order.order_id] = order
        
        # Add to fill simulator's pending orders
        self.fill_simulator.pending_orders.append(order)
        
        logger.debug(f"Order submitted: {order.order_id} {order.side} {order.quantity} {order.symbol}")
        
        return order.order_id
    
    def process_market_update(self, market_data: MarketSnapshot) -> List[Trade]:
        """
        Process market update and execute pending orders.
        
        Args:
            market_data (MarketSnapshot): Current market state
            
        Returns:
            List[Trade]: List of trades generated from executions
        """
        new_trades = []
        
        # Process each pending order
        pending_orders = self.fill_simulator.get_pending_orders()
        
        for order in pending_orders:
            if order.symbol == market_data.symbol:
                trades = self.fill_simulator.process_order(order, market_data)
                new_trades.extend(trades)
                
                # Store trades
                self.trades.extend(trades)
        
        # Clean up filled orders
        self.fill_simulator.cleanup_filled_orders()
        
        return new_trades
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id (str): ID of order to cancel
            
        Returns:
            bool: True if order was cancelled, False if not found
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.is_active:
                success = self.fill_simulator.cancel_order(order_id)
                if success:
                    logger.debug(f"Order cancelled: {order_id}")
                return success
        
        logger.warning(f"Failed to cancel order: {order_id}")
        return False
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Cancel all pending orders, optionally filtered by symbol.
        
        Args:
            symbol (Optional[str]): If provided, only cancel orders for this symbol
            
        Returns:
            int: Number of orders cancelled
        """
        cancelled_count = 0
        
        for order in list(self.orders.values()):
            if order.is_active and (symbol is None or order.symbol == symbol):
                if self.cancel_order(order.order_id):
                    cancelled_count += 1
        
        return cancelled_count
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        Get order status by ID.
        
        Args:
            order_id (str): Order ID to query
            
        Returns:
            Optional[Order]: Order object if found, None otherwise
        """
        return self.orders.get(order_id)
    
    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get list of pending orders, optionally filtered by symbol.
        
        Args:
            symbol (Optional[str]): If provided, only return orders for this symbol
            
        Returns:
            List[Order]: List of pending orders
        """
        pending = []
        
        for order in self.orders.values():
            if order.is_active and (symbol is None or order.symbol == symbol):
                pending.append(order)
        
        return pending
    
    def get_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """
        Get list of executed trades, optionally filtered by symbol.
        
        Args:
            symbol (Optional[str]): If provided, only return trades for this symbol
            
        Returns:
            List[Trade]: List of executed trades
        """
        if symbol is None:
            return self.trades.copy()
        
        return [trade for trade in self.trades if trade.symbol == symbol]
    
    def get_trade_summary(self) -> Dict[str, any]:
        """
        Get summary statistics of executed trades.
        
        Returns:
            Dict[str, any]: Trade summary statistics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'total_volume': 0.0,
                'total_fees': 0.0,
                'symbols_traded': []
            }
        
        total_volume = sum(trade.notional_value for trade in self.trades)
        total_fees = sum(trade.fees for trade in self.trades)
        symbols_traded = list(set(trade.symbol for trade in self.trades))
        
        return {
            'total_trades': len(self.trades),
            'total_volume': total_volume,
            'total_fees': total_fees,
            'symbols_traded': symbols_traded,
            'avg_trade_size': total_volume / len(self.trades) if self.trades else 0
        }
    
    def _validate_order(self, order: Order) -> bool:
        """
        Validate order parameters before submission.
        
        Args:
            order (Order): Order to validate
            
        Returns:
            bool: True if order is valid, False otherwise
        """
        # Check minimum order size
        if order.limit_price:
            notional_value = order.quantity * order.limit_price
        else:
            # For market orders, we can't validate exact notional value
            # Use a reasonable estimate
            notional_value = order.quantity * 100  # Assume $100 per unit
        
        if notional_value < self.config.min_order_size:
            logger.warning(f"Order below minimum size: {notional_value} < {self.config.min_order_size}")
            return False
        
        # Check order quantity is positive
        if order.quantity <= 0:
            logger.warning(f"Invalid order quantity: {order.quantity}")
            return False
        
        # Check symbol format (basic validation)
        if not order.symbol or len(order.symbol) < 3:
            logger.warning(f"Invalid symbol: {order.symbol}")
            return False
        
        # Check limit price for limit orders
        if order.order_type.name.endswith('LIMIT') and order.limit_price is None:
            logger.warning(f"Limit order missing limit price: {order.order_id}")
            return False
        
        # Check stop price for stop orders
        if order.order_type.name.startswith('STOP') and order.stop_price is None:
            logger.warning(f"Stop order missing stop price: {order.order_id}")
            return False
        
        return True
    
    def reset(self) -> None:
        """Reset execution engine state for new backtest."""
        self.orders.clear()
        self.trades.clear()
        self.fill_simulator.pending_orders.clear()
        self.fill_simulator.fill_history.clear()
        self.order_sequence = 0
        
        logger.info("Execution engine reset")