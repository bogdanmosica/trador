"""
Strategy Module for Trador - Modular Crypto Trading Bot

This module provides a pluggable, configurable strategy system that outputs
trade signals based on defined logic and market data.
"""

from .base_strategy import BaseStrategy
from .config_manager import ConfigManager
from .strategies.sma_crossover import SmaCrossoverStrategy

__all__ = ['BaseStrategy', 'ConfigManager', 'SmaCrossoverStrategy']