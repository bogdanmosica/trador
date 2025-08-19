"""
Fill Simulator

Simulates realistic order fills with slippage, partial fills, and latency.
Models market microstructure effects for accurate execution simulation.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging

from ..models import Order, Trade, OrderType, OrderStatus, TimeInForce, MarketSnapshot, BacktestConfig


logger = logging.getLogger(__name__)


class FillSimulator:
    """
    Simulates realistic order execution with market microstructure effects.
    
    Models slippage, partial fills, latency, and order book dynamics
    to provide realistic execution simulation for backtesting.
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize fill simulator with configuration.
        
        Args:
            config (BacktestConfig): Backtesting configuration parameters
        """
        self.config = config
        self.pending_orders: List[Order] = []
        self.fill_history: List[Trade] = []
    
    def process_order(self, order: Order, market_data: MarketSnapshot) -> List[Trade]:
        """
        Process an order against current market conditions.
        
        Args:
            order (Order): Order to process
            market_data (MarketSnapshot): Current market state
            
        Returns:
            List[Trade]: List of trades generated from order execution
        """
        fills = []
        
        # Simulate execution latency
        execution_time = market_data.timestamp + timedelta(
            milliseconds=self.config.execution_latency_ms
        )
        
        if order.order_type == OrderType.MARKET:
            fills = self._process_market_order(order, market_data, execution_time)
        elif order.order_type == OrderType.LIMIT:
            fills = self._process_limit_order(order, market_data, execution_time)
        elif order.order_type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT]:
            fills = self._process_stop_order(order, market_data, execution_time)
        
        # Update order status
        self._update_order_status(order)
        
        return fills
    
    def _process_market_order(self, order: Order, market_data: MarketSnapshot, execution_time: datetime) -> List[Trade]:
        """
        Process market order with slippage simulation.
        
        Args:
            order (Order): Market order to process
            market_data (MarketSnapshot): Current market data
            execution_time (datetime): Simulated execution timestamp
            
        Returns:
            List[Trade]: Generated trades
        """
        fills = []
        
        # Determine execution price with slippage
        if order.is_buy:
            # Buy at ask price + slippage
            base_price = market_data.ask
            slippage_factor = 1 + self.config.market_order_slippage
            execution_price = base_price * slippage_factor
        else:
            # Sell at bid price - slippage
            base_price = market_data.bid
            slippage_factor = 1 - self.config.market_order_slippage
            execution_price = base_price * slippage_factor
        
        # Simulate partial fills
        remaining_quantity = order.remaining_quantity
        
        # Check if we should simulate a partial fill
        if (remaining_quantity > 0 and 
            random.random() < self.config.partial_fill_probability and
            order.time_in_force != TimeInForce.FOK):
            
            # Fill 50-90% of remaining quantity
            fill_ratio = random.uniform(0.5, 0.9)
            fill_quantity = remaining_quantity * fill_ratio
        else:
            # Full fill
            fill_quantity = remaining_quantity
        
        if fill_quantity > 0:
            # Calculate fees
            notional_value = fill_quantity * execution_price
            fee = notional_value * self.config.taker_fee  # Market orders are always taker
            
            # Create trade
            trade = Trade(
                trade_id=f"trade_{order.order_id}_{len(fills)}",
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=fill_quantity,
                price=execution_price,
                timestamp=execution_time,
                fees=fee,
                fee_currency=self.config.base_currency,
                is_maker=False,  # Market orders are always taker
                metadata={'slippage_applied': self.config.market_order_slippage}
            )
            
            fills.append(trade)
            
            # Update order
            order.filled_quantity += fill_quantity
            order.remaining_quantity -= fill_quantity
            
            # Update average fill price
            if order.average_fill_price is None:
                order.average_fill_price = execution_price
            else:
                total_filled = order.filled_quantity
                order.average_fill_price = (
                    (order.average_fill_price * (total_filled - fill_quantity) + 
                     execution_price * fill_quantity) / total_filled
                )
            
            order.fees += fee
            
            logger.debug(f"Market order fill: {fill_quantity} {order.symbol} at {execution_price}")
        
        return fills
    
    def _process_limit_order(self, order: Order, market_data: MarketSnapshot, execution_time: datetime) -> List[Trade]:
        """
        Process limit order based on market price conditions.
        
        Args:
            order (Order): Limit order to process
            market_data (MarketSnapshot): Current market data
            execution_time (datetime): Simulated execution timestamp
            
        Returns:
            List[Trade]: Generated trades
        """
        fills = []
        
        if order.limit_price is None:
            logger.error(f"Limit order {order.order_id} missing limit price")
            return fills
        
        # Check if limit order can be filled
        can_fill = False
        execution_price = order.limit_price
        
        if order.is_buy:
            # Buy limit can fill if market ask <= limit price
            if market_data.ask <= order.limit_price:
                can_fill = True
                # Get better price if possible (price improvement)
                execution_price = min(order.limit_price, market_data.ask)
        else:
            # Sell limit can fill if market bid >= limit price
            if market_data.bid >= order.limit_price:
                can_fill = True
                # Get better price if possible (price improvement)
                execution_price = max(order.limit_price, market_data.bid)
        
        if not can_fill:
            # Order remains in order book
            return fills
        
        # Simulate partial fills for limit orders
        remaining_quantity = order.remaining_quantity
        
        # Limit orders have lower probability of partial fills
        partial_fill_prob = self.config.partial_fill_probability * 0.5
        
        if (remaining_quantity > 0 and 
            random.random() < partial_fill_prob and
            order.time_in_force != TimeInForce.FOK):
            
            # Fill 60-95% of remaining quantity
            fill_ratio = random.uniform(0.6, 0.95)
            fill_quantity = remaining_quantity * fill_ratio
        else:
            # Full fill
            fill_quantity = remaining_quantity
        
        if fill_quantity > 0:
            # Calculate fees (assume maker fee for limit orders)
            notional_value = fill_quantity * execution_price
            fee = notional_value * self.config.maker_fee
            
            # Create trade
            trade = Trade(
                trade_id=f"trade_{order.order_id}_{len(fills)}",
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=fill_quantity,
                price=execution_price,
                timestamp=execution_time,
                fees=fee,
                fee_currency=self.config.base_currency,
                is_maker=True,  # Limit orders are typically maker
                metadata={'limit_price': order.limit_price}
            )
            
            fills.append(trade)
            
            # Update order
            order.filled_quantity += fill_quantity
            order.remaining_quantity -= fill_quantity
            
            # Update average fill price
            if order.average_fill_price is None:
                order.average_fill_price = execution_price
            else:
                total_filled = order.filled_quantity
                order.average_fill_price = (
                    (order.average_fill_price * (total_filled - fill_quantity) + 
                     execution_price * fill_quantity) / total_filled
                )
            
            order.fees += fee
            
            logger.debug(f"Limit order fill: {fill_quantity} {order.symbol} at {execution_price}")
        
        return fills
    
    def _process_stop_order(self, order: Order, market_data: MarketSnapshot, execution_time: datetime) -> List[Trade]:
        """
        Process stop orders (stop-market and stop-limit).
        
        Args:
            order (Order): Stop order to process
            market_data (MarketSnapshot): Current market data
            execution_time (datetime): Simulated execution timestamp
            
        Returns:
            List[Trade]: Generated trades
        """
        fills = []
        
        if order.stop_price is None:
            logger.error(f"Stop order {order.order_id} missing stop price")
            return fills
        
        # Check if stop is triggered
        stop_triggered = False
        
        if order.is_buy:
            # Buy stop: trigger when price rises above stop price
            if market_data.close >= order.stop_price:
                stop_triggered = True
        else:
            # Sell stop: trigger when price falls below stop price
            if market_data.close <= order.stop_price:
                stop_triggered = True
        
        if not stop_triggered:
            return fills
        
        # Stop is triggered - convert to market or limit order
        if order.order_type == OrderType.STOP_MARKET:
            # Convert to market order
            order.order_type = OrderType.MARKET
            fills = self._process_market_order(order, market_data, execution_time)
        elif order.order_type == OrderType.STOP_LIMIT:
            # Convert to limit order
            order.order_type = OrderType.LIMIT
            fills = self._process_limit_order(order, market_data, execution_time)
        
        return fills
    
    def _update_order_status(self, order: Order) -> None:
        """
        Update order status based on fill quantity.
        
        Args:
            order (Order): Order to update
        """
        if order.remaining_quantity <= 0:
            order.status = OrderStatus.FILLED
        elif order.filled_quantity > 0:
            order.status = OrderStatus.PARTIAL_FILLED
        
        # Handle IOC and FOK orders
        if order.time_in_force == TimeInForce.IOC and order.status == OrderStatus.PARTIAL_FILLED:
            # Cancel remaining quantity for IOC orders
            order.status = OrderStatus.PARTIAL_FILLED
            order.remaining_quantity = 0
        elif order.time_in_force == TimeInForce.FOK and order.filled_quantity < order.quantity:
            # Cancel entire order if not fully filled for FOK orders
            order.status = OrderStatus.CANCELLED
            order.filled_quantity = 0
            order.remaining_quantity = order.quantity
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id (str): ID of order to cancel
            
        Returns:
            bool: True if order was cancelled, False if not found
        """
        for order in self.pending_orders:
            if order.order_id == order_id and order.is_active:
                order.status = OrderStatus.CANCELLED
                return True
        return False
    
    def get_pending_orders(self) -> List[Order]:
        """
        Get list of pending orders.
        
        Returns:
            List[Order]: List of active orders
        """
        return [order for order in self.pending_orders if order.is_active]
    
    def cleanup_filled_orders(self) -> None:
        """Remove filled and cancelled orders from pending list."""
        self.pending_orders = [order for order in self.pending_orders if order.is_active]