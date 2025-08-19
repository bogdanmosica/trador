"""
Unit Tests for Statistical Arbitrage Strategy

Comprehensive test suite covering all aspects of the StatisticalArbitrageStrategy
including signal generation, regime detection, indicator calculations, and
parameter validation.
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List
import warnings

from strategies.statistical_arbitrage import StatisticalArbitrageStrategy, RegimeState
from base_strategy import MarketData, Position, Signal


class TestStatisticalArbitrageStrategy(unittest.TestCase):
    """Test cases for Statistical Arbitrage Strategy."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.strategy = StatisticalArbitrageStrategy("test_stat_arb")
        
        # Create sample market data for testing
        self.sample_data = self._generate_sample_market_data()
        
        # Suppress warnings during tests
        warnings.filterwarnings('ignore')
    
    def tearDown(self):
        """Clean up after each test method."""
        warnings.resetwarnings()
    
    def _generate_sample_market_data(self, days: int = 100) -> List[MarketData]:
        """
        Generate realistic sample market data for testing.
        
        Creates data with trend, mean reversion, and noise patterns.
        """
        np.random.seed(42)  # For reproducible tests
        
        # Generate base price series with trend and mean reversion
        base_price = 100.0
        prices = [base_price]
        
        for i in range(days * 24):  # Hourly data
            # Add trend component
            trend = 0.0001 * i
            
            # Add mean reversion component  
            mean_reversion = -0.01 * (prices[-1] - base_price) / base_price
            
            # Add random noise
            noise = np.random.normal(0, 0.002)
            
            # Calculate next price
            price_change = trend + mean_reversion + noise
            new_price = prices[-1] * (1 + price_change)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        # Create MarketData objects
        market_data = []
        base_time = datetime.now() - timedelta(hours=len(prices))
        
        for i, price in enumerate(prices[1:]):  # Skip first price
            timestamp = base_time + timedelta(hours=i)
            
            # Generate OHLCV data around the close price
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            open_price = prices[i] + np.random.normal(0, price * 0.001)
            volume = max(1000 + np.random.normal(0, 500), 100)
            
            market_data.append(MarketData(
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=price,
                volume=volume,
                symbol="TEST",
                timeframe="1h"
            ))
        
        return market_data
    
    def test_strategy_initialization(self):
        """Test strategy initialization with default parameters."""
        strategy = StatisticalArbitrageStrategy("test_init")
        
        self.assertEqual(strategy.strategy_name, "test_init")
        self.assertIsInstance(strategy.parameters, dict)
        self.assertIn('lookback_window', strategy.parameters)
        self.assertIn('zscore_entry_threshold', strategy.parameters)
        self.assertIn('min_confidence', strategy.parameters)
        
        # Test default parameter values
        self.assertEqual(strategy.parameters['lookback_window'], 50)
        self.assertEqual(strategy.parameters['zscore_entry_threshold'], 2.0)
        self.assertEqual(strategy.parameters['min_confidence'], 0.6)
    
    def test_convert_to_dataframe(self):
        """Test conversion of MarketData list to pandas DataFrame."""
        df = self.strategy._convert_to_dataframe(self.sample_data[:10])
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 10)
        self.assertTrue(df.index.name == 'timestamp')
        self.assertIn('close', df.columns)
        self.assertIn('volume', df.columns)
        self.assertTrue(df.index.is_monotonic_increasing)
    
    def test_regime_detection(self):
        """Test market regime detection functionality."""
        df = self.strategy._convert_to_dataframe(self.sample_data)
        self.strategy._update_regime_state(df)
        
        self.assertIsNotNone(self.strategy._regime_state)
        self.assertIsInstance(self.strategy._regime_state, RegimeState)
        
        regime = self.strategy._regime_state.regime
        self.assertIn(regime, ['trending', 'mean_reverting', 'volatile'])
        
        self.assertGreaterEqual(self.strategy._regime_state.volatility_percentile, 0)
        self.assertLessEqual(self.strategy._regime_state.volatility_percentile, 1)
        self.assertGreaterEqual(self.strategy._regime_state.trend_strength, 0)
    
    def test_calculate_indicators(self):
        """Test calculation of technical indicators."""
        df = self.strategy._convert_to_dataframe(self.sample_data)
        indicators = self.strategy._calculate_indicators(df)
        
        # Check that all expected indicators are present
        expected_indicators = ['zscore', 'volatility', 'rsi', 'bollinger_position']
        for indicator in expected_indicators:
            self.assertIn(indicator, indicators)
            self.assertEqual(len(indicators[indicator]), len(df))
        
        # Test Z-score properties
        zscore = indicators['zscore']
        self.assertFalse(np.all(np.isnan(zscore[-10:])))  # Should have valid values
        
        # Test RSI bounds
        rsi = indicators['rsi']
        valid_rsi = rsi[~np.isnan(rsi)]
        if len(valid_rsi) > 0:
            self.assertGreaterEqual(np.min(valid_rsi), 0)
            self.assertLessEqual(np.max(valid_rsi), 100)
        
        # Test Bollinger position bounds
        bollinger_pos = indicators['bollinger_position']
        valid_bollinger = bollinger_pos[~np.isnan(bollinger_pos)]
        if len(valid_bollinger) > 0:
            self.assertGreaterEqual(np.min(valid_bollinger), 0)
            self.assertLessEqual(np.max(valid_bollinger), 1)
    
    def test_rolling_zscore_calculation(self):
        """Test rolling Z-score calculation."""
        # Create test series with known properties
        test_series = np.array([1, 2, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1])
        window = 5
        
        zscore = self.strategy._calculate_rolling_zscore(test_series, window)
        
        # Should have same length as input
        self.assertEqual(len(zscore), len(test_series))
        
        # Check for reasonable values (not all NaN or inf)
        valid_values = zscore[~np.isnan(zscore)]
        self.assertGreater(len(valid_values), 0)
        self.assertFalse(np.any(np.isinf(valid_values)))
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        # Create trending up series
        up_trend = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109] * 3)
        rsi_up = self.strategy._calculate_rsi(up_trend, 14)
        
        # RSI should be high for uptrending data
        valid_rsi = rsi_up[~np.isnan(rsi_up)]
        if len(valid_rsi) > 0:
            self.assertGreater(np.mean(valid_rsi[-5:]), 60)  # Should be overbought
        
        # Test bounds
        self.assertGreaterEqual(np.min(valid_rsi), 0)
        self.assertLessEqual(np.max(valid_rsi), 100)
    
    def test_bollinger_position_calculation(self):
        """Test Bollinger Band position calculation."""
        # Create series with known volatility
        prices = np.array([100] * 10 + [110] * 10 + [100] * 10)
        bollinger_pos = self.strategy._calculate_bollinger_position(prices, 10)
        
        # Should return values between 0 and 1
        valid_pos = bollinger_pos[~np.isnan(bollinger_pos)]
        if len(valid_pos) > 0:
            self.assertGreaterEqual(np.min(valid_pos), 0)
            self.assertLessEqual(np.max(valid_pos), 1)
    
    def test_signal_generation_no_position(self):
        """Test signal generation when no current position exists."""
        signals = self.strategy.generate_signals(self.sample_data, None, {})
        
        # Should return a list
        self.assertIsInstance(signals, list)
        
        # If signals generated, check properties
        if signals:
            signal = signals[0]
            self.assertIsInstance(signal, Signal)
            self.assertIn(signal.action, ['BUY', 'SELL', 'HOLD'])
            self.assertGreaterEqual(signal.confidence, 0)
            self.assertLessEqual(signal.confidence, 1)
            self.assertGreater(signal.quantity_ratio, 0)
    
    def test_signal_generation_with_long_position(self):
        """Test signal generation when holding a long position."""
        # Create a long position
        long_position = Position(
            symbol="TEST",
            quantity=100,
            entry_price=100.0,
            entry_time=datetime.now() - timedelta(hours=1)
        )
        
        signals = self.strategy.generate_signals(self.sample_data, long_position, {})
        
        # Should return a list
        self.assertIsInstance(signals, list)
        
        # If exit signal generated, should be SELL
        if signals:
            signal = signals[0]
            self.assertEqual(signal.action, 'SELL')
    
    def test_signal_generation_with_short_position(self):
        """Test signal generation when holding a short position."""
        # Create a short position
        short_position = Position(
            symbol="TEST",
            quantity=-100,
            entry_price=100.0,
            entry_time=datetime.now() - timedelta(hours=1)
        )
        
        signals = self.strategy.generate_signals(self.sample_data, short_position, {})
        
        # Should return a list
        self.assertIsInstance(signals, list)
        
        # If exit signal generated, should be BUY
        if signals:
            signal = signals[0]
            self.assertEqual(signal.action, 'BUY')
    
    def test_signal_generation_insufficient_data(self):
        """Test signal generation with insufficient data."""
        # Use only a few data points
        short_data = self.sample_data[:10]
        signals = self.strategy.generate_signals(short_data, None, {})
        
        # Should return empty list due to insufficient data
        self.assertEqual(signals, [])
    
    def test_regime_adjusted_thresholds(self):
        """Test regime-based threshold adjustments."""
        # Test with different regime states
        base_threshold = 2.0
        self.strategy.parameters['zscore_entry_threshold'] = base_threshold
        
        # Test volatile regime
        self.strategy._regime_state = RegimeState(
            regime='volatile',
            volatility_percentile=0.9,
            trend_strength=0.2,
            last_updated=datetime.now()
        )
        volatile_threshold = self.strategy._get_regime_adjusted_threshold('entry')
        self.assertGreater(volatile_threshold, base_threshold)
        
        # Test mean-reverting regime
        self.strategy._regime_state = RegimeState(
            regime='mean_reverting',
            volatility_percentile=0.3,
            trend_strength=0.1,
            last_updated=datetime.now()
        )
        mr_threshold = self.strategy._get_regime_adjusted_threshold('entry')
        self.assertLess(mr_threshold, base_threshold)
    
    def test_confidence_calculation(self):
        """Test signal confidence calculation."""
        # Test with extreme Z-score (should have high confidence)
        confidence_high = self.strategy._calculate_confidence(
            zscore=-3.0,
            volatility=0.01,
            rsi=20,
            bollinger_pos=0.1,
            signal_strength=2.0
        )
        
        # Test with weak Z-score (should have low confidence)
        confidence_low = self.strategy._calculate_confidence(
            zscore=-1.0,
            volatility=0.05,
            rsi=45,
            bollinger_pos=0.5,
            signal_strength=0.5
        )
        
        self.assertGreater(confidence_high, confidence_low)
        self.assertGreaterEqual(confidence_high, 0)
        self.assertLessEqual(confidence_high, 1)
        self.assertGreaterEqual(confidence_low, 0)
        self.assertLessEqual(confidence_low, 1)
    
    def test_parameter_presets(self):
        """Test parameter preset updates."""
        original_threshold = self.strategy.parameters['zscore_entry_threshold']
        
        # Test conservative preset
        success = self.strategy.update_parameters('conservative')
        self.assertTrue(success)
        self.assertNotEqual(
            self.strategy.parameters['zscore_entry_threshold'],
            original_threshold
        )
        
        # Test aggressive preset
        success = self.strategy.update_parameters('aggressive')
        self.assertTrue(success)
        
        # Test invalid preset
        success = self.strategy.update_parameters('invalid_preset')
        self.assertFalse(success)
    
    def test_parameter_validation(self):
        """Test parameter validation logic."""
        # Test valid parameters
        valid_params = {
            'lookback_window': 50,
            'zscore_entry_threshold': 2.0,
            'zscore_exit_threshold': 0.5,
            'min_confidence': 0.6
        }
        self.assertTrue(self.strategy.validate_parameters(valid_params))
        
        # Test invalid parameters
        invalid_params = {
            'lookback_window': 5,  # Too small
            'zscore_entry_threshold': -1.0,  # Negative
            'zscore_exit_threshold': 3.0,  # Greater than entry
            'min_confidence': 1.5  # Greater than 1
        }
        self.assertFalse(self.strategy.validate_parameters(invalid_params))
        
        # Test missing required parameters
        incomplete_params = {'lookback_window': 50}
        self.assertFalse(self.strategy.validate_parameters(incomplete_params))
    
    def test_required_indicators(self):
        """Test required indicators list."""
        indicators = self.strategy.get_required_indicators()
        
        self.assertIsInstance(indicators, list)
        self.assertGreater(len(indicators), 0)
        
        # Check for expected indicators
        expected = ['EWMA_10', 'RSI_14', 'BOLLINGER_20_2']
        for indicator in expected:
            self.assertIn(indicator, indicators)
    
    def test_parameter_schema(self):
        """Test parameter schema structure."""
        schema = self.strategy.get_parameter_schema()
        
        self.assertIsInstance(schema, dict)
        self.assertGreater(len(schema), 0)
        
        # Check schema structure for key parameters
        key_params = ['lookback_window', 'zscore_entry_threshold', 'min_confidence']
        for param in key_params:
            self.assertIn(param, schema)
            self.assertIn('type', schema[param])
            self.assertIn('default', schema[param])
            self.assertIn('description', schema[param])
    
    def test_signal_metadata(self):
        """Test that generated signals contain proper metadata."""
        # Force signal generation with custom parameters
        custom_params = {
            'zscore_entry_threshold': 0.5,  # Very low threshold
            'min_confidence': 0.1  # Very low confidence requirement
        }
        
        signals = self.strategy.generate_signals(self.sample_data, None, custom_params)
        
        if signals:
            signal = signals[0]
            self.assertIsNotNone(signal.metadata)
            
            # Check for expected metadata fields
            expected_fields = [
                'zscore', 'volatility', 'rsi', 'bollinger_position',
                'signal_strength', 'regime', 'strategy_type'
            ]
            
            for field in expected_fields:
                self.assertIn(field, signal.metadata)
            
            # Check metadata types
            self.assertIsInstance(signal.metadata['zscore'], float)
            self.assertIsInstance(signal.metadata['strategy_type'], str)
            self.assertEqual(signal.metadata['strategy_type'], 'statistical_arbitrage')
    
    def test_volume_trend_calculation(self):
        """Test volume trend correlation calculation."""
        # Create test data with correlated volume and price changes
        volume = np.array([1000, 1100, 1200, 1100, 1000, 900, 1000, 1100] * 5)
        prices = np.array([100, 101, 102, 101, 100, 99, 100, 101] * 5)
        
        volume_trend = self.strategy._calculate_volume_trend(volume, prices)
        
        # Should return array same length as input
        self.assertEqual(len(volume_trend), len(volume))
        
        # Should contain finite values
        self.assertTrue(np.all(np.isfinite(volume_trend)))
    
    def test_error_handling(self):
        """Test error handling in signal generation."""
        # Test with invalid market data
        invalid_data = []
        signals = self.strategy.generate_signals(invalid_data, None, {})
        self.assertEqual(signals, [])
        
        # Test with None market data
        signals = self.strategy.generate_signals(None, None, {})
        self.assertEqual(signals, [])


class TestRegimeState(unittest.TestCase):
    """Test cases for RegimeState dataclass."""
    
    def test_regime_state_creation(self):
        """Test RegimeState creation and properties."""
        regime = RegimeState(
            regime='mean_reverting',
            volatility_percentile=0.3,
            trend_strength=0.1,
            last_updated=datetime.now()
        )
        
        self.assertEqual(regime.regime, 'mean_reverting')
        self.assertEqual(regime.volatility_percentile, 0.3)
        self.assertEqual(regime.trend_strength, 0.1)
        self.assertIsInstance(regime.last_updated, datetime)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestStatisticalArbitrageStrategy)
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRegimeState))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} tests passed successfully!")
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors")
        
    exit(0 if result.wasSuccessful() else 1)