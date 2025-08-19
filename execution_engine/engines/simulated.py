"""
Simulated Execution Engine

Implements order execution simulation for backtesting and paper trading.
Provides realistic market simulation with slippage, fees, and latency modeling.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import random
import math

from .base import (
    ExecutionEngine, 
    ExecutionEngineError, 
    OrderValidationError,
    InsufficientBalanceError,
    PositionLimitError
)
from ..models import (
    Signal, Order, Fill, OrderStatus, OrderType, OrderSide, 
    ExecutionConfig, TimeInForce
)


class MarketData:
    """Simple market data container for execution simulation."""
    
    def __init__(
        self, 
        symbol: str, 
        timestamp: int, 
        open_price: float, 
        high_price: float, 
        low_price: float, 
        close_price: float, 
        volume: float
    ):
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price
        self.volume = volume
    
    @property
    def typical_price(self) -> float:
        """Calculate typical price (HLC/3)."""
        return (self.high + self.low + self.close) / 3
    
    @property
    def weighted_price(self) -> float:
        """Calculate weighted price (HLCC/4)."""
        return (self.high + self.low + self.close + self.close) / 4


from trador.portfolio_risk.exceptions import RiskViolationError
from trador.portfolio_risk.risk_engine import RiskEngine
from trador.portfolio_risk.portfolio_manager import PortfolioManager


class SimulatedExecutionEngine(ExecutionEngine):
    """
    Simulated execution engine for backtesting and paper trading.
    
    This engine is now integrated with the Portfolio & Risk Engine.
    """
    
    def __init__(self, config: ExecutionConfig, portfolio_manager: PortfolioManager, risk_rules: list):
        """
        Initialize simulated execution engine.
        
        Args:
            config: Execution configuration.
            portfolio_manager: An instance of the PortfolioManager for the strategy.
            risk_rules: A list of risk rule configurations.
        """
        super().__init__(config)
        
        # Portfolio and Risk Management
        self.portfolio_manager = portfolio_manager
        self.risk_engine = RiskEngine(self.portfolio_manager.state, risk_rules)
        
        # Market data
        self.current_market_data: Dict[str, MarketData] = {}
        
        # Execution state
        self._pending_orders: List[Order] = []
        self._execution_queue: asyncio.Queue = asyncio.Queue()

    def update_market_data(self, market_data: MarketData) -> None:
        """
        Update market data and portfolio PnL.
        """
        self.current_market_data[market_data.symbol] = market_data
        self.portfolio_manager.update_market_price(market_data.symbol, market_data.close)
        
        asyncio.create_task(self._process_pending_orders(market_data))
    
    async def start(self) -> None:
        self._is_running = True
        self.logger.info("Simulated execution engine started")
        asyncio.create_task(self._process_execution_queue())
    
    async def stop(self) -> None:
        self._is_running = False
        self.logger.info("Simulated execution engine stopped")
    
    async def submit_signal(self, signal: Signal) -> Order:
        if not self._is_running:
            raise ExecutionEngineError("Execution engine is not running")
        
        if not self._validate_signal(signal):
            raise OrderValidationError(f"Invalid signal: {signal}")

        # --- Integration with RiskEngine ---
        proposed_fill = self._create_proposed_fill(signal)
        is_safe, violations = self.risk_engine.check_pre_trade(proposed_fill)
        
        if not is_safe:
            raise RiskViolationError(f"Trade rejected due to risk violations: {violations}", violations)
        # --- End Integration ---

        order = Order(
            order_id=self.generate_order_id(),
            signal=signal,
            status=OrderStatus.NEW
        )
        
        self._add_order(order)
        
        if signal.order_type == OrderType.MARKET:
            await self._process_market_order(order)
        elif signal.order_type == OrderType.LIMIT:
            await self._process_limit_order(order)
        else:
            order.reject(f"Unsupported order type: {signal.order_type}")
            self._update_order_status(order, OrderStatus.REJECTED)
        
        return order

    def _create_proposed_fill(self, signal: Signal) -> Fill:
        """Creates a temporary Fill object from a Signal for risk checking."""
        price = signal.limit_price
        if signal.order_type == OrderType.MARKET:
            # For market orders, use the last known price for the check
            if signal.symbol in self.current_market_data:
                price = self.current_market_data[signal.symbol].close
            else:
                # Cannot check risk without a price
                raise OrderValidationError(f"Cannot determine price for risk check on market order for {signal.symbol}")
        
        return Fill(
            symbol=signal.symbol,
            side=OrderSide[signal.side.value],
            price=price,
            quantity=signal.quantity
        )

    async def cancel_order(self, order_id: str, reason: str = "User cancellation") -> bool:
        order = self.get_order(order_id)
        if not order or not order.is_active:
            return False
        
        self._pending_orders = [o for o in self._pending_orders if o.order_id != order_id]
        order.cancel(reason)
        self._update_order_status(order, OrderStatus.CANCELLED, reason)
        return True
    
    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        order = self.get_order(order_id)
        return order.status if order else None
    
    async def _process_market_order(self, order: Order) -> None:
        symbol = order.symbol
        if symbol not in self.current_market_data:
            order.reject("No market data available")
            self._update_order_status(order, OrderStatus.REJECTED)
            return
        
        if self.config.market_order_delay_ms > 0:
            await asyncio.sleep(self.config.market_order_delay_ms / 1000)
        
        self._update_order_status(order, OrderStatus.PENDING)
        
        market_data = self.current_market_data[symbol]
        execution_price = self._calculate_market_execution_price(order, market_data)
        
        fill = self._create_fill(order, execution_price, order.quantity, is_maker=False)
        
        self._add_fill(order, fill)
        self._apply_fill_to_portfolio(fill)
        
        self.logger.info(f"Market order filled: {order.order_id} @ {execution_price}")
    
    async def _process_limit_order(self, order: Order) -> None:
        self._update_order_status(order, OrderStatus.PENDING)
        self._pending_orders.append(order)
        self.logger.info(f"Limit order pending: {order.order_id} @ {order.signal.limit_price}")
    
    async def _process_pending_orders(self, market_data: MarketData) -> None:
        orders_to_remove = []
        for order in self._pending_orders:
            if order.symbol != market_data.symbol or not order.is_active:
                if not order.is_active:
                    orders_to_remove.append(order)
                continue
            
            if self._can_limit_order_fill(order, market_data):
                fill_price = self._calculate_limit_execution_price(order, market_data)
                fill = self._create_fill(order, fill_price, order.quantity, is_maker=True)
                self._add_fill(order, fill)
                self._apply_fill_to_portfolio(fill)
                orders_to_remove.append(order)
                self.logger.info(f"Limit order filled: {order.order_id} @ {fill_price}")
        
        for order in orders_to_remove:
            if order in self._pending_orders:
                self._pending_orders.remove(order)
    
    def _can_limit_order_fill(self, order: Order, market_data: MarketData) -> bool:
        limit_price = order.signal.limit_price
        if limit_price is None:
            return False
        
        if order.side == OrderSide.BUY:
            return market_data.low <= limit_price
        else:
            return market_data.high >= limit_price
    
    def _calculate_market_execution_price(self, order: Order, market_data: MarketData) -> float:
        base_price = market_data.typical_price
        slippage_noise = random.uniform(-0.25, 0.25)
        final_slippage = self.config.market_slippage_bps * (1 + slippage_noise)
        
        if order.side == OrderSide.BUY:
            slippage_multiplier = 1 + (final_slippage / 10000)
        else:
            slippage_multiplier = 1 - (final_slippage / 10000)
        
        return base_price * slippage_multiplier
    
    def _calculate_limit_execution_price(self, order: Order, market_data: MarketData) -> float:
        limit_price = order.signal.limit_price
        tolerance = self.config.limit_slippage_tolerance_bps / 10000
        
        if order.side == OrderSide.BUY:
            best_possible = min(limit_price, market_data.low)
            price_improvement = random.uniform(0, tolerance) * limit_price
            return max(best_possible, limit_price - price_improvement)
        else:
            best_possible = max(limit_price, market_data.high)
            price_improvement = random.uniform(0, tolerance) * limit_price
            return min(best_possible, limit_price + price_improvement)
    
    def _create_fill(self, order: Order, price: float, quantity: float, is_maker: bool = False) -> Fill:
        fee_rate = self.config.maker_fee_rate if is_maker else self.config.taker_fee_rate
        fee = quantity * price * fee_rate
        
        return Fill(
            symbol=order.symbol,
            side=order.side,
            price=price,
            quantity=quantity,
            fee=fee,
            fee_currency="USDT" # Simplified
        )
    
    def _apply_fill_to_portfolio(self, fill: Fill) -> None:
        """
        Apply fill to the PortfolioManager and check for critical risk violations.
        """
        self.portfolio_manager.apply_fill(fill)
        self.logger.debug(
            f"Portfolio updated via PortfolioManager. New equity: {self.portfolio_manager.total_equity:.2f}"
        )

        # --- Kill-Switch Logic ---
        is_critical, violations = self.risk_engine.check_for_critical_violations()
        if is_critical:
            self.logger.critical(f"CRITICAL RISK VIOLATION: {violations}. Triggering kill-switch.")
            asyncio.create_task(self.flatten_all_positions("Critical risk violation"))
        # --- End Kill-Switch Logic ---

    async def flatten_all_positions(self, reason: str):
        """
        Liquidates all open positions for the strategy.
        """
        self.logger.warning(f"Flattening all positions for strategy {self.portfolio_manager.strategy_id} due to: {reason}")
        
        # Stop accepting new signals
        self._is_running = False

        open_positions = list(self.portfolio_manager.state.open_positions.values())
        for position in open_positions:
            # Create a closing signal
            closing_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            signal = Signal(
                symbol=position.symbol,
                side=closing_side,
                quantity=position.quantity,
                order_type=OrderType.MARKET
            )
            
            try:
                # We need to temporarily re-enable the engine to submit the closing order
                self._is_running = True
                await self.submit_signal(signal)
                self._is_running = False
                self.logger.info(f"Submitted closing order for {position.symbol}.")
            except Exception as e:
                self.logger.error(f"Failed to submit closing order for {position.symbol}: {e}")
        
        self.logger.warning(f"All positions for strategy {self.portfolio_manager.strategy_id} have been flattened.")

    async def _process_execution_queue(self) -> None:
        while self._is_running:
            try:
                item = await asyncio.wait_for(self._execution_queue.get(), timeout=1.0)
                self.logger.debug(f"Processing execution queue item: {item}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing execution queue: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, any]:
        """
        Get portfolio summary from the PortfolioManager.
        """
        state = self.portfolio_manager.state
        return {
            'strategy_id': self.portfolio_manager.strategy_id,
            'equity': state.equity,
            'free_balance': state.free_balance,
            'unrealized_pnl': self.portfolio_manager.unrealized_pnl,
            'open_positions': {k: v.__dict__ for k, v in state.open_positions.items()},
            'trade_history_count': len(state.trade_history)
        }
