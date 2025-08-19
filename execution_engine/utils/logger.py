"""
Order Tracking and Logging System

Provides comprehensive logging, tracking, and export capabilities for
execution engine orders, fills, and portfolio events.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import asdict
import pandas as pd

from ..models import Order, Fill, Signal, OrderStatus, OrderSide


class ExecutionLogger:
    """
    Comprehensive logging system for execution engine events.
    
    Tracks all orders, fills, and execution events with multiple
    export formats and analytics capabilities.
    """
    
    def __init__(self, log_directory: str = "./logs", enable_file_logging: bool = True):
        """
        Initialize execution logger.
        
        Args:
            log_directory: Directory for log files
            enable_file_logging: Whether to enable file logging
        """
        self.log_directory = Path(log_directory)
        self.enable_file_logging = enable_file_logging
        
        # Create log directory
        if self.enable_file_logging:
            self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Event storage
        self.order_events: List[Dict[str, Any]] = []
        self.fill_events: List[Dict[str, Any]] = []
        self.execution_events: List[Dict[str, Any]] = []
        
        # Setup logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger."""
        logger = logging.getLogger('ExecutionEngine')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if logger.handlers:
            logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if self.enable_file_logging:
            log_file = self.log_directory / 'execution.log'
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def log_order_created(self, order: Order) -> None:
        """
        Log order creation event.
        
        Args:
            order: Created order
        """
        event = {
            'event_type': 'order_created',
            'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'order_type': order.order_type.value,
            'limit_price': order.signal.limit_price,
            'stop_price': order.signal.stop_price,
            'strategy_id': order.signal.strategy_id,
            'status': order.status.value
        }
        
        self.order_events.append(event)
        self.execution_events.append(event)
        
        self.logger.info(
            f"Order Created: {order.order_id} - {order.symbol} {order.side.value} "
            f"{order.quantity} @ {order.signal.limit_price or 'market'}"
        )
        
        if self.enable_file_logging:
            self._write_event_to_file(event, 'orders')
    
    def log_order_updated(self, order: Order, old_status: OrderStatus) -> None:
        """
        Log order status update event.
        
        Args:
            order: Updated order
            old_status: Previous order status
        """
        event = {
            'event_type': 'order_updated',
            'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'old_status': old_status.value,
            'new_status': order.status.value,
            'filled_quantity': order.filled_quantity,
            'average_fill_price': order.average_fill_price,
            'rejection_reason': order.rejection_reason
        }
        
        self.order_events.append(event)
        self.execution_events.append(event)
        
        self.logger.info(
            f"Order Updated: {order.order_id} - Status: {old_status.value} -> {order.status.value}"
        )
        
        if self.enable_file_logging:
            self._write_event_to_file(event, 'orders')
    
    def log_order_filled(self, order: Order, fill: Fill) -> None:
        """
        Log order fill event.
        
        Args:
            order: Filled order
            fill: Fill details
        """
        fill_event = {
            'event_type': 'order_filled',
            'timestamp': fill.timestamp,
            'order_id': order.order_id,
            'fill_id': fill.fill_id,
            'symbol': fill.symbol,
            'side': fill.side.value,
            'quantity': fill.quantity,
            'price': fill.price,
            'fee': fill.fee,
            'fee_asset': fill.fee_asset,
            'is_maker': fill.is_maker,
            'notional_value': fill.notional_value,
            'trade_id': fill.trade_id
        }
        
        self.fill_events.append(fill_event)
        self.execution_events.append(fill_event)
        
        self.logger.info(
            f"Order Filled: {order.order_id} - {fill.quantity} @ {fill.price} "
            f"(fee: {fill.fee}) {'[MAKER]' if fill.is_maker else '[TAKER]'}"
        )
        
        if self.enable_file_logging:
            self._write_event_to_file(fill_event, 'fills')
    
    def log_order_cancelled(self, order: Order, reason: str) -> None:
        """
        Log order cancellation event.
        
        Args:
            order: Cancelled order
            reason: Cancellation reason
        """
        event = {
            'event_type': 'order_cancelled',
            'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'reason': reason,
            'filled_quantity': order.filled_quantity,
            'remaining_quantity': order.remaining_quantity
        }
        
        self.order_events.append(event)
        self.execution_events.append(event)
        
        self.logger.info(f"Order Cancelled: {order.order_id} - Reason: {reason}")
        
        if self.enable_file_logging:
            self._write_event_to_file(event, 'orders')
    
    def log_order_rejected(self, order: Order, reason: str) -> None:
        """
        Log order rejection event.
        
        Args:
            order: Rejected order
            reason: Rejection reason
        """
        event = {
            'event_type': 'order_rejected',
            'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'reason': reason
        }
        
        self.order_events.append(event)
        self.execution_events.append(event)
        
        self.logger.warning(f"Order Rejected: {order.order_id} - Reason: {reason}")
        
        if self.enable_file_logging:
            self._write_event_to_file(event, 'orders')
    
    def log_execution_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log execution error event.
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        event = {
            'event_type': 'execution_error',
            'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        self.execution_events.append(event)
        
        self.logger.error(f"Execution Error: {type(error).__name__}: {error}")
        
        if self.enable_file_logging:
            self._write_event_to_file(event, 'errors')
    
    def _write_event_to_file(self, event: Dict[str, Any], event_type: str) -> None:
        """
        Write event to file.
        
        Args:
            event: Event data
            event_type: Type of event for file naming
        """
        try:
            timestamp_str = datetime.now().strftime('%Y%m%d')
            file_path = self.log_directory / f"{event_type}_{timestamp_str}.jsonl"
            
            with open(file_path, 'a') as f:
                f.write(json.dumps(event) + '\n')
        
        except Exception as e:
            self.logger.error(f"Failed to write event to file: {e}")
    
    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Get order execution statistics.
        
        Returns:
            Dictionary of order statistics
        """
        if not self.order_events:
            return {
                'total_orders': 0,
                'filled_orders': 0,
                'cancelled_orders': 0,
                'rejected_orders': 0,
                'fill_rate': 0.0,
                'cancellation_rate': 0.0,
                'rejection_rate': 0.0
            }
        
        # Count order events by type
        created_count = len([e for e in self.order_events if e['event_type'] == 'order_created'])
        filled_count = len([e for e in self.order_events if e['event_type'] == 'order_filled'])
        cancelled_count = len([e for e in self.order_events if e['event_type'] == 'order_cancelled'])
        rejected_count = len([e for e in self.order_events if e['event_type'] == 'order_rejected'])
        
        return {
            'total_orders': created_count,
            'filled_orders': filled_count,
            'cancelled_orders': cancelled_count,
            'rejected_orders': rejected_count,
            'fill_rate': (filled_count / created_count) * 100 if created_count > 0 else 0,
            'cancellation_rate': (cancelled_count / created_count) * 100 if created_count > 0 else 0,
            'rejection_rate': (rejected_count / created_count) * 100 if created_count > 0 else 0
        }
    
    def get_fill_statistics(self) -> Dict[str, Any]:
        """
        Get fill execution statistics.
        
        Returns:
            Dictionary of fill statistics
        """
        if not self.fill_events:
            return {
                'total_fills': 0,
                'total_volume': 0.0,
                'total_fees': 0.0,
                'average_fill_size': 0.0,
                'maker_fills': 0,
                'taker_fills': 0,
                'maker_rate': 0.0
            }
        
        total_fills = len(self.fill_events)
        total_volume = sum(e['notional_value'] for e in self.fill_events)
        total_fees = sum(e['fee'] for e in self.fill_events)
        average_fill_size = total_volume / total_fills if total_fills > 0 else 0
        
        maker_fills = len([e for e in self.fill_events if e['is_maker']])
        taker_fills = total_fills - maker_fills
        maker_rate = (maker_fills / total_fills) * 100 if total_fills > 0 else 0
        
        return {
            'total_fills': total_fills,
            'total_volume': total_volume,
            'total_fees': total_fees,
            'average_fill_size': average_fill_size,
            'maker_fills': maker_fills,
            'taker_fills': taker_fills,
            'maker_rate': maker_rate
        }
    
    def export_to_csv(self, file_path: str, event_type: str = 'all') -> None:
        """
        Export events to CSV file.
        
        Args:
            file_path: Output CSV file path
            event_type: Type of events to export ('all', 'orders', 'fills')
        """
        if event_type == 'orders':
            events = self.order_events
        elif event_type == 'fills':
            events = self.fill_events
        else:
            events = self.execution_events
        
        if not events:
            self.logger.warning(f"No {event_type} events to export")
            return
        
        # Convert to DataFrame for easier CSV export
        df = pd.DataFrame(events)
        df.to_csv(file_path, index=False)
        
        self.logger.info(f"Exported {len(events)} {event_type} events to {file_path}")
    
    def export_to_json(self, file_path: str) -> None:
        """
        Export all events to JSON file.
        
        Args:
            file_path: Output JSON file path
        """
        export_data = {
            'order_events': self.order_events,
            'fill_events': self.fill_events,
            'execution_events': self.execution_events,
            'statistics': {
                'orders': self.get_order_statistics(),
                'fills': self.get_fill_statistics()
            },
            'export_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported execution data to {file_path}")
    
    def clear_logs(self) -> None:
        """Clear all logged events."""
        self.order_events.clear()
        self.fill_events.clear()
        self.execution_events.clear()
        self.logger.info("Execution logs cleared")
    
    def get_events_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get all events for a specific symbol.
        
        Args:
            symbol: Symbol to filter by
            
        Returns:
            List of events for the symbol
        """
        return [
            event for event in self.execution_events 
            if event.get('symbol') == symbol
        ]
    
    def get_events_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get events within a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of events in time range
        """
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        return [
            event for event in self.execution_events
            if start_timestamp <= event['timestamp'] <= end_timestamp
        ]


class TradeJournal:
    """
    Trade journal for recording and analyzing completed trades.
    
    Provides trade-level analytics and performance tracking
    for completed position cycles.
    """
    
    def __init__(self):
        """Initialize trade journal."""
        self.trades: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    def record_trade(
        self, 
        symbol: str,
        entry_time: datetime,
        exit_time: datetime,
        entry_price: float,
        exit_price: float,
        quantity: float,
        side: OrderSide,
        pnl: float,
        fees: float,
        strategy_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a completed trade.
        
        Args:
            symbol: Trading symbol
            entry_time: Trade entry time
            exit_time: Trade exit time
            entry_price: Entry price
            exit_price: Exit price
            quantity: Trade quantity
            side: Trade side (initial direction)
            pnl: Realized P&L
            fees: Total fees
            strategy_id: Strategy that generated the trade
            metadata: Additional trade metadata
        """
        trade = {
            'trade_id': f"trade_{int(entry_time.timestamp() * 1000)}_{symbol}",
            'symbol': symbol,
            'entry_time': entry_time.isoformat(),
            'exit_time': exit_time.isoformat(),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'side': side.value,
            'pnl': pnl,
            'fees': fees,
            'net_pnl': pnl - fees,
            'return_percent': ((exit_price - entry_price) / entry_price) * 100 * (1 if side == OrderSide.BUY else -1),
            'holding_period_hours': (exit_time - entry_time).total_seconds() / 3600,
            'strategy_id': strategy_id,
            'metadata': metadata or {}
        }
        
        self.trades.append(trade)
        
        self.logger.info(
            f"Trade Recorded: {symbol} {side.value} {quantity} @ {entry_price} -> {exit_price} "
            f"P&L: {pnl:.2f} (fees: {fees:.2f})"
        )
    
    def get_trade_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive trade analytics.
        
        Returns:
            Dictionary of trade analytics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0,
                'total_pnl': 0.0,
                'average_holding_period': 0.0
            }
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['net_pnl'] > 0])
        losing_trades = len([t for t in self.trades if t['net_pnl'] < 0])
        
        wins = [t['net_pnl'] for t in self.trades if t['net_pnl'] > 0]
        losses = [t['net_pnl'] for t in self.trades if t['net_pnl'] < 0]
        
        average_win = sum(wins) / len(wins) if wins else 0
        average_loss = sum(losses) / len(losses) if losses else 0
        
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        total_pnl = sum(t['net_pnl'] for t in self.trades)
        average_holding_period = sum(t['holding_period_hours'] for t in self.trades) / total_trades
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades) * 100,
            'average_win': average_win,
            'average_loss': average_loss,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'average_holding_period': average_holding_period,
            'best_trade': max(t['net_pnl'] for t in self.trades),
            'worst_trade': min(t['net_pnl'] for t in self.trades)
        }
    
    def export_trades(self, file_path: str, format: str = 'csv') -> None:
        """
        Export trades to file.
        
        Args:
            file_path: Output file path
            format: Export format ('csv' or 'json')
        """
        if format.lower() == 'csv':
            df = pd.DataFrame(self.trades)
            df.to_csv(file_path, index=False)
        elif format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump({
                    'trades': self.trades,
                    'analytics': self.get_trade_analytics(),
                    'export_timestamp': datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        
        self.logger.info(f"Exported {len(self.trades)} trades to {file_path}")
    
    def clear_trades(self) -> None:
        """Clear all recorded trades."""
        self.trades.clear()
        self.logger.info("Trade journal cleared")