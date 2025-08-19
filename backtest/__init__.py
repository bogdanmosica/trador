"""
Backtest Module

Event-driven backtesting engine for crypto trading strategies.
Provides realistic simulation of order execution, portfolio management,
and performance metrics for trading strategy evaluation.
"""

from .models import Order, Trade, OrderType, OrderStatus, TimeInForce
from .portfolio import Portfolio
from .backtester import Backtester

__all__ = [
    'Order',
    'Trade', 
    'OrderType',
    'OrderStatus',
    'TimeInForce',
    'Portfolio',
    'Backtester'
]