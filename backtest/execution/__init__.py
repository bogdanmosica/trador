"""
Execution Engine Module

Simulates realistic order execution including partial fills, slippage,
latency, and market impact. Provides the core execution logic for
the backtesting engine.
"""

from .execution_engine import ExecutionEngine
from .fill_simulator import FillSimulator

__all__ = [
    'ExecutionEngine',
    'FillSimulator'
]