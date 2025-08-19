"""
Base Strategy Interface

Defines the common interface that all trading strategies must implement.
Strategies are stateless and side-effect-free - they only generate signals.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketData:
    """
    Market data structure for strategy input.
    
    Contains OHLCV data and any additional indicators needed by strategies.
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str
    indicators: Optional[Dict[str, Any]] = None


@dataclass
class Position:
    """
    Current position information.
    
    Represents the current state of holdings for a specific symbol.
    """
    symbol: str
    quantity: float
    entry_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    unrealized_pnl: Optional[float] = None


@dataclass
class Signal:
    """
    Trading signal output from strategy.
    
    Contains the action to take and associated metadata.
    """
    action: str  # 'BUY', 'SELL', 'HOLD'
    symbol: str
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    quantity_ratio: float  # Fraction of available capital/position to use
    reason: str  # Human-readable explanation
    metadata: Optional[Dict[str, Any]] = None


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Defines the interface that all strategies must implement to ensure
    consistent behavior and pluggability.
    """
    
    def __init__(self, strategy_name: str):
        """
        Initialize the strategy with its name.
        
        Args:
            strategy_name (str): Unique identifier for this strategy
        """
        self.strategy_name = strategy_name
        self.parameters: Dict[str, Any] = {}
    
    @abstractmethod
    def generate_signals(
        self, 
        market_data: List[MarketData], 
        current_position: Optional[Position], 
        strategy_params: Dict[str, Any]
    ) -> List[Signal]:
        """
        Generate trading signals based on market data and current position.
        
        This method should be stateless and side-effect-free. It analyzes
        the provided market data and generates appropriate trading signals.
        
        Args:
            market_data (List[MarketData]): Historical market data for analysis
            current_position (Optional[Position]): Current position if any
            strategy_params (Dict[str, Any]): Strategy-specific parameters
            
        Returns:
            List[Signal]: List of trading signals (usually 0-1 signals)
        """
        pass
    
    @abstractmethod
    def update_parameters(self, preset_name: str) -> bool:
        """
        Update strategy parameters from a named preset.
        
        Loads parameter configuration from storage and updates the strategy's
        internal parameter state.
        
        Args:
            preset_name (str): Name of the parameter preset to load
            
        Returns:
            bool: True if parameters were successfully updated, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Validate that the provided parameters are valid for this strategy.
        
        Args:
            params (Dict[str, Any]): Parameters to validate
            
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        pass
    
    def get_required_indicators(self) -> List[str]:
        """
        Get list of indicators required by this strategy.
        
        Returns:
            List[str]: List of indicator names (e.g., ['SMA_20', 'RSI_14'])
        """
        return []
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get the parameter schema for this strategy.
        
        Returns a dictionary describing the expected parameters, their types,
        and valid ranges.
        
        Returns:
            Dict[str, Any]: Parameter schema definition
        """
        return {}
    
    def __str__(self) -> str:
        """String representation of the strategy."""
        return f"{self.__class__.__name__}(name='{self.strategy_name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the strategy."""
        return f"{self.__class__.__name__}(name='{self.strategy_name}', params={self.parameters})"