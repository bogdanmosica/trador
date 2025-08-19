"""
Simple Moving Average (SMA) Crossover Strategy

A classic trend-following strategy that generates buy signals when a fast SMA
crosses above a slow SMA, and sell signals when the fast SMA crosses below
the slow SMA.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

# Try relative import first, fall back to absolute import for dynamic loading
try:
    from ..base_strategy import BaseStrategy, MarketData, Position, Signal
    from ..config_manager import ConfigManager
except (ImportError, SystemError):
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from base_strategy import BaseStrategy, MarketData, Position, Signal
    from config_manager import ConfigManager


class SmaCrossoverStrategy(BaseStrategy):
    """
    SMA Crossover Strategy Implementation.
    
    Generates trading signals based on the crossover of two Simple Moving Averages:
    - Fast SMA (shorter period)
    - Slow SMA (longer period)
    
    Buy Signal: Fast SMA crosses above Slow SMA
    Sell Signal: Fast SMA crosses below Slow SMA
    """
    
    def __init__(self, strategy_name: str = "sma_crossover"):
        """
        Initialize the SMA Crossover strategy.
        
        Args:
            strategy_name (str): Name identifier for this strategy instance
        """
        super().__init__(strategy_name)
        self.config_manager = ConfigManager()
        
        # Default parameters
        self.parameters = {
            "fast_period": 9,
            "slow_period": 21,
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "min_confidence": 0.7,
            "position_size": 0.5  # Fraction of available capital to use
        }
    
    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average for given prices and period.
        
        Args:
            prices (List[float]): List of price values
            period (int): Number of periods for SMA calculation
            
        Returns:
            Optional[float]: SMA value or None if insufficient data
        """
        if len(prices) < period:
            return None
        
        return statistics.mean(prices[-period:])
    
    def generate_signals(
        self, 
        market_data: List[MarketData], 
        current_position: Optional[Position], 
        strategy_params: Dict[str, Any]
    ) -> List[Signal]:
        """
        Generate trading signals based on SMA crossover logic.
        
        Args:
            market_data (List[MarketData]): Historical market data
            current_position (Optional[Position]): Current position if any
            strategy_params (Dict[str, Any]): Strategy parameters
            
        Returns:
            List[Signal]: Generated trading signals
        """
        # Update parameters with provided params
        params = {**self.parameters, **strategy_params}
        
        fast_period = params["fast_period"]
        slow_period = params["slow_period"]
        min_confidence = params["min_confidence"]
        position_size = params["position_size"]
        
        # Validate we have enough data
        if len(market_data) < slow_period + 1:
            return []
        
        # Extract closing prices
        close_prices = [candle.close for candle in market_data]
        
        # Calculate current and previous SMAs
        current_fast_sma = self.calculate_sma(close_prices, fast_period)
        current_slow_sma = self.calculate_sma(close_prices, slow_period)
        
        previous_fast_sma = self.calculate_sma(close_prices[:-1], fast_period)
        previous_slow_sma = self.calculate_sma(close_prices[:-1], slow_period)
        
        # Check if we have all required SMA values
        if None in [current_fast_sma, current_slow_sma, previous_fast_sma, previous_slow_sma]:
            return []
        
        # Get latest market data for signal metadata
        latest_data = market_data[-1]
        
        # Determine crossover conditions
        signals = []
        
        # Bullish crossover: Fast SMA crosses above Slow SMA
        if (previous_fast_sma <= previous_slow_sma and 
            current_fast_sma > current_slow_sma):
            
            # Calculate confidence based on separation between SMAs
            sma_separation = abs(current_fast_sma - current_slow_sma) / current_slow_sma
            confidence = min(0.9, max(0.5, sma_separation * 10))
            
            if confidence >= min_confidence and (not current_position or current_position.quantity <= 0):
                signals.append(Signal(
                    action="BUY",
                    symbol=latest_data.symbol,
                    timestamp=latest_data.timestamp,
                    confidence=confidence,
                    quantity_ratio=position_size,
                    reason=f"Fast SMA ({current_fast_sma:.2f}) crossed above Slow SMA ({current_slow_sma:.2f})",
                    metadata={
                        "fast_sma": current_fast_sma,
                        "slow_sma": current_slow_sma,
                        "sma_separation": sma_separation,
                        "strategy": self.strategy_name
                    }
                ))
        
        # Bearish crossover: Fast SMA crosses below Slow SMA
        elif (previous_fast_sma >= previous_slow_sma and 
              current_fast_sma < current_slow_sma):
            
            # Calculate confidence based on separation between SMAs
            sma_separation = abs(current_fast_sma - current_slow_sma) / current_slow_sma
            confidence = min(0.9, max(0.5, sma_separation * 10))
            
            if confidence >= min_confidence and current_position and current_position.quantity > 0:
                signals.append(Signal(
                    action="SELL",
                    symbol=latest_data.symbol,
                    timestamp=latest_data.timestamp,
                    confidence=confidence,
                    quantity_ratio=1.0,  # Sell full position
                    reason=f"Fast SMA ({current_fast_sma:.2f}) crossed below Slow SMA ({current_slow_sma:.2f})",
                    metadata={
                        "fast_sma": current_fast_sma,
                        "slow_sma": current_slow_sma,
                        "sma_separation": sma_separation,
                        "strategy": self.strategy_name
                    }
                ))
        
        return signals
    
    def update_parameters(self, preset_name: str) -> bool:
        """
        Update strategy parameters from a named preset configuration.
        
        Args:
            preset_name (str): Name of the configuration preset to load
            
        Returns:
            bool: True if parameters updated successfully, False otherwise
        """
        config = self.config_manager.load_config(preset_name)
        if config and config.base_strategy == "sma_crossover":
            if self.validate_parameters(config.params):
                self.parameters.update(config.params)
                return True
        return False
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Validate SMA crossover strategy parameters.
        
        Args:
            params (Dict[str, Any]): Parameters to validate
            
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        required_params = ["fast_period", "slow_period"]
        
        # Check required parameters exist
        for param in required_params:
            if param not in params:
                return False
        
        # Validate parameter values
        fast_period = params["fast_period"]
        slow_period = params["slow_period"]
        
        # Basic validation
        if not isinstance(fast_period, int) or not isinstance(slow_period, int):
            return False
        
        if fast_period <= 0 or slow_period <= 0:
            return False
        
        if fast_period >= slow_period:
            return False
        
        # Validate optional parameters if present
        if "min_confidence" in params:
            confidence = params["min_confidence"]
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                return False
        
        if "position_size" in params:
            size = params["position_size"]
            if not isinstance(size, (int, float)) or not (0.0 < size <= 1.0):
                return False
        
        return True
    
    def get_required_indicators(self) -> List[str]:
        """
        Get list of indicators required by this strategy.
        
        Returns:
            List[str]: List of required indicators
        """
        fast_period = self.parameters.get("fast_period", 9)
        slow_period = self.parameters.get("slow_period", 21)
        
        return [f"SMA_{fast_period}", f"SMA_{slow_period}"]
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get the parameter schema for SMA crossover strategy.
        
        Returns:
            Dict[str, Any]: Parameter schema definition
        """
        return {
            "fast_period": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": self.parameters.get("fast_period", 9),
                "description": "Period for fast moving average"
            },
            "slow_period": {
                "type": "integer", 
                "minimum": 2,
                "maximum": 200,
                "default": self.parameters.get("slow_period", 21),
                "description": "Period for slow moving average"
            },
            "symbol": {
                "type": "string",
                "default": self.parameters.get("symbol", "BTCUSDT"),
                "description": "Trading symbol (e.g., BTCUSDT)"
            },
            "timeframe": {
                "type": "string",
                "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                "default": self.parameters.get("timeframe", "1h"),
                "description": "Timeframe for analysis"
            },
            "min_confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": self.parameters.get("min_confidence", 0.7),
                "description": "Minimum confidence threshold for signals"
            },
            "position_size": {
                "type": "number",
                "minimum": 0.01,
                "maximum": 1.0,
                "default": self.parameters.get("position_size", 0.5),
                "description": "Fraction of capital to use for positions"
            }
        }
