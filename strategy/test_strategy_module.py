"""
Test Script for Strategy Module

Demonstrates the usage of the strategy module and validates its functionality.
"""

from datetime import datetime, timedelta
from typing import List
import random

# Import from local module (relative imports for tests within the module)
from . import BaseStrategy, ConfigManager, SmaCrossoverStrategy
from .base_strategy import MarketData, Position, Signal


def generate_sample_market_data(symbol: str = "BTCUSDT", periods: int = 50) -> List[MarketData]:
    """
    Generate sample market data for testing purposes.
    
    Creates synthetic OHLCV data with realistic price movements.
    
    Args:
        symbol (str): Trading symbol
        periods (int): Number of data points to generate
        
    Returns:
        List[MarketData]: List of market data objects
    """
    data = []
    base_price = 50000.0  # Starting price
    current_time = datetime.now() - timedelta(hours=periods)
    
    for i in range(periods):
        # Simple random walk with some trend
        price_change = random.uniform(-0.03, 0.03)  # 3% max change
        base_price *= (1 + price_change)
        
        # Generate OHLC from base price
        high = base_price * random.uniform(1.001, 1.02)
        low = base_price * random.uniform(0.98, 0.999)
        open_price = random.uniform(low, high)
        close_price = base_price
        volume = random.uniform(100, 1000)
        
        data.append(MarketData(
            timestamp=current_time + timedelta(hours=i),
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=volume,
            symbol=symbol,
            timeframe="1h"
        ))
    
    return data


def test_config_manager():
    """Test the configuration manager functionality."""
    print("=== Testing Configuration Manager ===")
    
    config_manager = ConfigManager()
    
    # List available configs
    configs = config_manager.list_configs()
    print(f"Available configurations: {configs}")
    
    # Load and display a config
    if configs:
        config_name = configs[0]
        config = config_manager.load_config(config_name)
        if config:
            print(f"\nLoaded config '{config_name}':")
            print(f"  Base Strategy: {config.base_strategy}")
            print(f"  Status: {config.status}")
            print(f"  Parameters: {config.params}")
            print(f"  Notes: {config.notes}")
    
    # Test creating a new version
    if configs:
        base_config = configs[0]
        new_version = f"{base_config}_test_copy"
        success = config_manager.create_version(
            base_config, 
            new_version, 
            status="draft",
            notes="Test copy created by test script"
        )
        print(f"\nCreated test version '{new_version}': {success}")
        
        # Clean up test version
        if success:
            config_manager.delete_config(new_version)
            print(f"Cleaned up test version: {new_version}")


def test_sma_strategy():
    """Test the SMA crossover strategy."""
    print("\n=== Testing SMA Crossover Strategy ===")
    
    # Create strategy instance
    strategy = SmaCrossoverStrategy("test_sma")
    
    # Generate test market data
    market_data = generate_sample_market_data("BTCUSDT", 60)
    print(f"Generated {len(market_data)} market data points")
    
    # Test with default parameters
    test_params = {
        "fast_period": 9,
        "slow_period": 21,
        "min_confidence": 0.7,
        "position_size": 0.5
    }
    
    # Test parameter validation
    is_valid = strategy.validate_parameters(test_params)
    print(f"Parameter validation: {is_valid}")
    
    # Generate signals with no current position
    signals = strategy.generate_signals(market_data, None, test_params)
    print(f"Generated {len(signals)} signals with no position")
    
    for signal in signals:
        print(f"  Signal: {signal.action} {signal.symbol} at {signal.timestamp}")
        print(f"    Confidence: {signal.confidence:.2f}")
        print(f"    Reason: {signal.reason}")
    
    # Test with existing position
    if signals and signals[0].action == "BUY":
        # Simulate having a position after first buy signal
        test_position = Position(
            symbol="BTCUSDT",
            quantity=0.1,
            entry_price=market_data[-10].close,
            entry_time=market_data[-10].timestamp
        )
        
        # Generate more signals with position
        recent_data = market_data[-30:]  # Use recent data
        new_signals = strategy.generate_signals(recent_data, test_position, test_params)
        print(f"\nGenerated {len(new_signals)} signals with existing position")
        
        for signal in new_signals:
            print(f"  Signal: {signal.action} {signal.symbol}")
            print(f"    Confidence: {signal.confidence:.2f}")
            print(f"    Reason: {signal.reason}")


def test_strategy_with_config():
    """Test loading strategy parameters from configuration."""
    print("\n=== Testing Strategy with Configuration ===")
    
    config_manager = ConfigManager()
    strategy = SmaCrossoverStrategy("config_test")
    
    # Try to load parameters from configuration
    configs = config_manager.list_configs("sma_crossover")
    if configs:
        config_name = configs[0]
        print(f"Loading parameters from config: {config_name}")
        
        success = strategy.update_parameters(config_name)
        print(f"Parameter update successful: {success}")
        
        if success:
            print(f"Updated parameters: {strategy.parameters}")
            
            # Generate sample data and test with loaded config
            market_data = generate_sample_market_data("BTCUSDT", 50)
            signals = strategy.generate_signals(market_data, None, strategy.parameters)
            print(f"Generated {len(signals)} signals with config parameters")
    else:
        print("No SMA crossover configurations found")


def test_parameter_schema():
    """Test parameter schema functionality."""
    print("\n=== Testing Parameter Schema ===")
    
    strategy = SmaCrossoverStrategy("schema_test")
    schema = strategy.get_parameter_schema()
    
    print("Parameter Schema:")
    for param_name, param_info in schema.items():
        print(f"  {param_name}: {param_info}")
    
    required_indicators = strategy.get_required_indicators()
    print(f"\nRequired indicators: {required_indicators}")


def main():
    """Run all tests for the strategy module."""
    print("Strategy Module Test Suite")
    print("=" * 50)
    
    try:
        test_config_manager()
        test_sma_strategy()
        test_strategy_with_config()
        test_parameter_schema()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()