"""
Statistical Arbitrage Strategy - Renaissance Technologies Inspired

A sophisticated mean reversion strategy that identifies statistical anomalies
in price relationships and captures profits from reversion to the mean.
This implementation focuses on pure signal generation, delegating risk
management to the portfolio_risk module.

Key Features:
- Z-score based entry/exit signals with dynamic thresholds
- Market regime detection for parameter adaptation
- Multi-timeframe confirmation
- Advanced statistical indicators
- Clean separation from risk management
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import warnings
from scipy import stats
import logging

# Try relative import first, fall back to absolute import for dynamic loading
try:
    from ..base_strategy import BaseStrategy, MarketData, Position, Signal
except (ImportError, SystemError):
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from base_strategy import BaseStrategy, MarketData, Position, Signal


@dataclass
class RegimeState:
    """Market regime classification for adaptive parameter adjustment."""
    regime: str  # 'trending', 'mean_reverting', 'volatile', 'stable'
    volatility_percentile: float
    trend_strength: float
    last_updated: datetime


class StatisticalArbitrageStrategy(BaseStrategy):
    """
    Statistical arbitrage strategy targeting mean reversion opportunities.
    
    This strategy implements sophisticated signal generation based on statistical
    anomalies and mean reversion patterns. Risk management is handled by the
    separate portfolio_risk module, keeping concerns properly separated.
    
    Core Algorithm:
    1. Calculate rolling Z-scores with exponential decay
    2. Detect market regime (trending/mean-reverting/volatile)
    3. Apply regime-adjusted entry/exit thresholds
    4. Generate signals with confidence scores
    5. Delegate position sizing and risk controls to portfolio_risk module
    """
    
    def __init__(self, strategy_name: str = "StatArb_RenTech_v1"):
        """
        Initialize the statistical arbitrage strategy.
        
        Args:
            strategy_name (str): Unique identifier for this strategy instance
        """
        super().__init__(strategy_name)
        
        # Core strategy parameters focused on signal generation
        self.parameters = {
            # Statistical parameters
            'lookback_window': 50,          # Primary lookback for Z-score calculation
            'zscore_entry_threshold': 2.0,   # Entry threshold for Z-score
            'zscore_exit_threshold': 0.5,    # Exit threshold for Z-score
            'volatility_lookback': 20,       # Volatility calculation window
            'half_life_periods': 10,         # Half-life for exponential decay
            
            # Regime detection
            'regime_lookback': 100,          # Lookback for regime analysis
            'volatility_threshold': 0.75,    # High volatility percentile
            'trend_threshold': 0.3,          # Trend strength threshold
            
            # Signal filtering
            'min_confidence': 0.6,           # Minimum signal confidence
            'volume_filter': True,           # Enable volume-based filtering
            'rsi_oversold': 30,              # RSI oversold threshold
            'rsi_overbought': 70,            # RSI overbought threshold
        }
        
        # Internal state tracking
        self._regime_state: Optional[RegimeState] = None
        self._signal_history: List[Dict] = []
        
        # Logging setup
        self.logger = logging.getLogger(f"{__name__}.{strategy_name}")
        
    def generate_signals(
        self, 
        market_data: List[MarketData], 
        current_position: Optional[Position], 
        strategy_params: Dict[str, Any]
    ) -> List[Signal]:
        """
        Generate statistical arbitrage signals based on mean reversion analysis.
        
        This method implements the core signal generation logic using:
        1. Z-score calculation with exponential decay
        2. Market regime detection and adaptation
        3. Multi-indicator confirmation
        4. Confidence scoring
        
        Args:
            market_data (List[MarketData]): Historical market data
            current_position (Optional[Position]): Current position if any
            strategy_params (Dict[str, Any]): Strategy parameters
            
        Returns:
            List[Signal]: Generated trading signals
        """
        try:
            # Update parameters if provided
            if strategy_params:
                self.parameters.update(strategy_params)
            
            # Ensure sufficient data
            if len(market_data) < self.parameters['lookback_window']:
                self.logger.warning(f"Insufficient data: {len(market_data)} < {self.parameters['lookback_window']}")
                return []
            
            # Convert to pandas DataFrame for analysis
            df = self._convert_to_dataframe(market_data)
            
            # Update market regime state
            self._update_regime_state(df)
            
            # Calculate core statistical indicators
            indicators = self._calculate_indicators(df)
            
            # Generate primary signal
            signal = self._generate_primary_signal(df, indicators, current_position)
            
            if signal:
                return [signal]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            return []
    
    def _convert_to_dataframe(self, market_data: List[MarketData]) -> pd.DataFrame:
        """Convert market data to pandas DataFrame with proper indexing."""
        data = []
        for md in market_data:
            data.append({
                'timestamp': md.timestamp,
                'open': md.open,
                'high': md.high,
                'low': md.low,
                'close': md.close,
                'volume': md.volume,
                'symbol': md.symbol
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    def _update_regime_state(self, df: pd.DataFrame) -> None:
        """
        Update market regime state based on volatility and trend analysis.
        
        This method implements regime detection for adaptive parameter adjustment,
        allowing the strategy to adapt to different market conditions.
        """
        lookback = min(self.parameters['regime_lookback'], len(df))
        recent_data = df.tail(lookback)
        
        # Calculate rolling volatility
        returns = recent_data['close'].pct_change().dropna()
        volatility = returns.rolling(window=self.parameters['volatility_lookback']).std()
        current_vol = volatility.iloc[-1]
        vol_percentile = stats.percentileofscore(volatility.dropna(), current_vol) / 100
        
        # Calculate trend strength using linear regression
        prices = recent_data['close'].values
        x = np.arange(len(prices))
        slope, _, r_value, _, _ = stats.linregress(x, prices)
        trend_strength = abs(r_value)
        
        # Determine regime
        if vol_percentile > self.parameters['volatility_threshold']:
            regime = 'volatile' if trend_strength <= self.parameters['trend_threshold'] else 'trending'
        else:
            regime = 'mean_reverting' if trend_strength <= self.parameters['trend_threshold'] else 'trending'
        
        self._regime_state = RegimeState(
            regime=regime,
            volatility_percentile=vol_percentile,
            trend_strength=trend_strength,
            last_updated=df.index[-1]
        )
        
        self.logger.debug(f"Regime: {regime}, vol_pct: {vol_percentile:.2f}, trend: {trend_strength:.2f}")
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Calculate statistical indicators for signal generation.
        
        Returns comprehensive set of indicators including Z-scores,
        volatility measures, and momentum indicators.
        """
        indicators = {}
        
        # Price-based indicators
        prices = df['close'].values
        returns = np.diff(prices) / prices[:-1]
        
        # Exponentially weighted moving average and std for Z-score
        alpha = 1 - np.exp(-1 / self.parameters['half_life_periods'])
        ewm_mean = pd.Series(prices).ewm(alpha=alpha).mean().values
        ewm_std = pd.Series(prices).ewm(alpha=alpha).std().values
        
        # Z-score calculation - core of the strategy
        indicators['zscore'] = (prices - ewm_mean) / (ewm_std + 1e-8)
        
        # Volatility indicators
        vol_window = self.parameters['volatility_lookback']
        volatility = pd.Series(returns).rolling(window=vol_window).std().values
        indicators['volatility'] = volatility
        
        # Momentum and mean reversion indicators
        indicators['rsi'] = self._calculate_rsi(prices, 14)
        indicators['bollinger_position'] = self._calculate_bollinger_position(prices, 20)
        
        # Volume-based indicators if available
        if 'volume' in df.columns and not df['volume'].isna().all():
            volume = df['volume'].values
            indicators['volume_zscore'] = self._calculate_rolling_zscore(volume, vol_window)
        
        return indicators
    
    def _calculate_rolling_zscore(self, series: np.ndarray, window: int) -> np.ndarray:
        """Calculate rolling Z-score for any time series."""
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            
            rolling_mean = pd.Series(series).rolling(window=window).mean().values
            rolling_std = pd.Series(series).rolling(window=window).std().values
            
            return (series - rolling_mean) / (rolling_std + 1e-8)
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index for momentum confirmation."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = pd.Series(gains).rolling(window=period).mean().values
        avg_losses = pd.Series(losses).rolling(window=period).mean().values
        
        rs = avg_gains / (avg_losses + 1e-8)
        rsi = 100 - (100 / (1 + rs))
        
        return np.concatenate([[np.nan], rsi])
    
    def _calculate_bollinger_position(self, prices: np.ndarray, period: int = 20) -> np.ndarray:
        """Calculate position within Bollinger Bands (0-1 scale)."""
        sma = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values
        
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        
        position = (prices - lower_band) / (upper_band - lower_band + 1e-8)
        return np.clip(position, 0, 1)
    
    def _generate_primary_signal(
        self, 
        df: pd.DataFrame, 
        indicators: Dict[str, np.ndarray], 
        current_position: Optional[Position]
    ) -> Optional[Signal]:
        """
        Generate the primary trading signal based on statistical analysis.
        
        This method implements the core signal logic that identifies
        high-probability mean reversion opportunities using Z-score analysis
        and multi-indicator confirmation.
        """
        latest_idx = -1
        current_time = df.index[latest_idx]
        symbol = df['symbol'].iloc[0]
        
        # Get current indicators
        zscore = indicators['zscore'][latest_idx]
        volatility = indicators['volatility'][latest_idx]
        rsi = indicators['rsi'][latest_idx]
        bollinger_pos = indicators['bollinger_position'][latest_idx]
        
        # Skip if indicators are invalid
        if np.isnan([zscore, volatility, rsi, bollinger_pos]).any():
            return None
        
        # Regime-adjusted thresholds
        entry_threshold = self._get_regime_adjusted_threshold('entry')
        exit_threshold = self._get_regime_adjusted_threshold('exit')
        
        # Determine signal direction
        action = 'HOLD'
        signal_strength = 0
        
        # Check for entry signals
        if current_position is None or current_position.quantity == 0:
            # Long entry: oversold conditions with multi-indicator confirmation
            if (zscore < -entry_threshold and 
                rsi < self.parameters['rsi_oversold'] and 
                bollinger_pos < 0.2):
                action = 'BUY'
                signal_strength = min(abs(zscore) / entry_threshold, 2.0)
            
            # Short entry: overbought conditions with multi-indicator confirmation  
            elif (zscore > entry_threshold and 
                  rsi > self.parameters['rsi_overbought'] and 
                  bollinger_pos > 0.8):
                action = 'SELL'
                signal_strength = min(abs(zscore) / entry_threshold, 2.0)
        
        # Check for exit signals
        elif current_position and current_position.quantity != 0:
            if current_position.quantity > 0:  # Long position
                if zscore > exit_threshold:
                    action = 'SELL'
                    signal_strength = 1.0
            else:  # Short position
                if zscore < -exit_threshold:
                    action = 'BUY'
                    signal_strength = 1.0
        
        if action == 'HOLD':
            return None
        
        # Calculate confidence score
        confidence = self._calculate_confidence(zscore, volatility, rsi, bollinger_pos, signal_strength)
        
        # Filter by minimum confidence
        if confidence < self.parameters['min_confidence']:
            return None
        
        # Create signal - let portfolio_risk module handle position sizing
        signal = Signal(
            action=action,
            symbol=symbol,
            timestamp=current_time,
            confidence=confidence,
            quantity_ratio=1.0,  # Portfolio risk module will determine actual size
            reason=self._generate_signal_reason(zscore, rsi, bollinger_pos, action),
            metadata={
                'zscore': float(zscore),
                'volatility': float(volatility),
                'rsi': float(rsi),
                'bollinger_position': float(bollinger_pos),
                'signal_strength': float(signal_strength),
                'regime': self._regime_state.regime if self._regime_state else 'unknown',
                'entry_threshold': float(entry_threshold),
                'exit_threshold': float(exit_threshold),
                'strategy_type': 'statistical_arbitrage'
            }
        )
        
        return signal
    
    def _get_regime_adjusted_threshold(self, threshold_type: str) -> float:
        """Adjust thresholds based on current market regime."""
        base_threshold = self.parameters[f'zscore_{threshold_type}_threshold']
        
        if not self._regime_state:
            return base_threshold
        
        # Regime-based adjustments
        if self._regime_state.regime == 'volatile':
            return base_threshold * 1.2  # Higher threshold in volatile markets
        elif self._regime_state.regime == 'trending':
            return base_threshold * 1.5  # Much higher threshold in trending markets
        elif self._regime_state.regime == 'mean_reverting':
            return base_threshold * 0.8  # Lower threshold in mean reverting markets
        
        return base_threshold
    
    def _calculate_confidence(
        self, 
        zscore: float, 
        volatility: float, 
        rsi: float, 
        bollinger_pos: float, 
        signal_strength: float
    ) -> float:
        """Calculate signal confidence based on multiple convergent factors."""
        confidence_factors = []
        
        # Z-score confidence (higher absolute value = higher confidence)
        zscore_conf = np.clip(abs(zscore) / 3.0, 0, 1)
        confidence_factors.append(zscore_conf)
        
        # RSI confirmation
        if abs(zscore) > 1.5:
            if zscore < 0 and rsi < 30:  # Oversold confirmation
                confidence_factors.append(0.8)
            elif zscore > 0 and rsi > 70:  # Overbought confirmation
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.3)
        
        # Bollinger Band confirmation
        if bollinger_pos < 0.2 or bollinger_pos > 0.8:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        # Volatility penalty (high volatility reduces confidence)
        vol_penalty = np.clip(1 - volatility * 5, 0.2, 1.0) if not np.isnan(volatility) else 0.5
        confidence_factors.append(vol_penalty)
        
        # Regime confidence adjustment
        if self._regime_state:
            if self._regime_state.regime == 'mean_reverting':
                confidence_factors.append(0.9)
            elif self._regime_state.regime == 'volatile':
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.6)
        
        # Calculate weighted average confidence
        base_confidence = np.mean(confidence_factors)
        
        # Apply signal strength multiplier
        final_confidence = base_confidence * (0.5 + 0.5 * signal_strength)
        
        return np.clip(final_confidence, 0, 1)
    
    def _generate_signal_reason(self, zscore: float, rsi: float, bollinger_pos: float, action: str) -> str:
        """Generate human-readable explanation for the signal."""
        regime = self._regime_state.regime if self._regime_state else 'unknown'
        
        if action == 'BUY':
            return (f"Oversold mean reversion: Z-score {zscore:.2f}, "
                   f"RSI {rsi:.1f}, Bollinger {bollinger_pos:.2f}, Regime: {regime}")
        elif action == 'SELL':
            return (f"Overbought mean reversion: Z-score {zscore:.2f}, "
                   f"RSI {rsi:.1f}, Bollinger {bollinger_pos:.2f}, Regime: {regime}")
        else:
            return f"Exit signal: Z-score normalized, Regime: {regime}"
    
    def update_parameters(self, preset_name: str) -> bool:
        """
        Update strategy parameters from named presets.
        
        Available presets:
        - conservative: Higher thresholds, more selective
        - aggressive: Lower thresholds, more signals
        - balanced: Moderate settings
        """
        try:
            preset_configs = {
                'conservative': {
                    'zscore_entry_threshold': 2.5,
                    'zscore_exit_threshold': 0.3,
                    'min_confidence': 0.7,
                    'volatility_threshold': 0.8,
                    'trend_threshold': 0.25,
                    'rsi_oversold': 25,
                    'rsi_overbought': 75,
                },
                'aggressive': {
                    'zscore_entry_threshold': 1.5,
                    'zscore_exit_threshold': 0.7,
                    'min_confidence': 0.5,
                    'volatility_threshold': 0.7,
                    'trend_threshold': 0.35,
                    'rsi_oversold': 35,
                    'rsi_overbought': 65,
                },
                'balanced': {
                    'zscore_entry_threshold': 2.0,
                    'zscore_exit_threshold': 0.5,
                    'min_confidence': 0.6,
                    'volatility_threshold': 0.75,
                    'trend_threshold': 0.3,
                    'rsi_oversold': 30,
                    'rsi_overbought': 70,
                }
            }
            
            if preset_name not in preset_configs:
                self.logger.error(f"Unknown preset: {preset_name}")
                return False
            
            self.parameters.update(preset_configs[preset_name])
            self.logger.info(f"Parameters updated with preset: {preset_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating parameters: {str(e)}")
            return False
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate strategy parameters for correctness and safety."""
        try:
            required_params = [
                'lookback_window', 'zscore_entry_threshold', 'zscore_exit_threshold', 'min_confidence'
            ]
            
            # Check required parameters exist
            for param in required_params:
                if param not in params:
                    self.logger.error(f"Missing required parameter: {param}")
                    return False
            
            # Validate parameter ranges
            validations = [
                (params['lookback_window'] >= 10, "lookback_window must be >= 10"),
                (params['zscore_entry_threshold'] > 0, "zscore_entry_threshold must be > 0"),
                (params['zscore_exit_threshold'] >= 0, "zscore_exit_threshold must be >= 0"),
                (0 <= params['min_confidence'] <= 1, "min_confidence must be in [0, 1]"),
            ]
            
            for condition, message in validations:
                if not condition:
                    self.logger.error(f"Parameter validation failed: {message}")
                    return False
            
            # Logical consistency checks
            if params['zscore_exit_threshold'] >= params['zscore_entry_threshold']:
                self.logger.error("exit_threshold must be < entry_threshold")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating parameters: {str(e)}")
            return False
    
    def get_required_indicators(self) -> List[str]:
        """Get list of indicators required by this strategy."""
        return [
            'EWMA_10', 'EWMA_20', 'RSI_14', 'BOLLINGER_20_2', 
            'VOLATILITY_20', 'VOLUME_SMA_20'
        ]
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get comprehensive parameter schema for this strategy."""
        return {
            'lookback_window': {
                'type': 'integer',
                'minimum': 10,
                'maximum': 200,
                'default': 50,
                'description': 'Primary lookback window for statistical calculations'
            },
            'zscore_entry_threshold': {
                'type': 'number',
                'minimum': 0.5,
                'maximum': 5.0,
                'default': 2.0,
                'description': 'Z-score threshold for entry signals'
            },
            'zscore_exit_threshold': {
                'type': 'number',
                'minimum': 0.0,
                'maximum': 2.0,
                'default': 0.5,
                'description': 'Z-score threshold for exit signals'
            },
            'min_confidence': {
                'type': 'number',
                'minimum': 0.0,
                'maximum': 1.0,
                'default': 0.6,
                'description': 'Minimum confidence score for signal execution'
            }
        }