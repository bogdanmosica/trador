"""
Risk Metrics Calculator

Specialized risk analysis calculations for portfolio and strategy evaluation.
Provides advanced risk metrics including VaR, Expected Shortfall, and
stress testing capabilities.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from ..models import Trade
from ..portfolio import PortfolioSnapshot


logger = logging.getLogger(__name__)


class RiskMetrics:
    """
    Calculates advanced risk metrics for backtesting results.
    
    Provides comprehensive risk analysis including Value at Risk,
    Expected Shortfall, stress testing, and correlation analysis.
    """
    
    def __init__(self, confidence_levels: List[float] = [0.95, 0.99]):
        """
        Initialize risk metrics calculator.
        
        Args:
            confidence_levels (List[float]): Confidence levels for VaR calculations
        """
        self.confidence_levels = confidence_levels
    
    def calculate_var_metrics(
        self,
        snapshots: List[PortfolioSnapshot],
        method: str = 'historical'
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk metrics using different methods.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            method (str): VaR calculation method ('historical', 'parametric', 'monte_carlo')
            
        Returns:
            Dict[str, float]: VaR metrics for different confidence levels
        """
        if len(snapshots) < 2:
            return {}
        
        # Calculate returns
        returns = self._calculate_returns(snapshots)
        
        if returns.empty:
            return {}
        
        var_metrics = {}
        
        for confidence_level in self.confidence_levels:
            confidence_pct = int(confidence_level * 100)
            
            if method == 'historical':
                var = self._historical_var(returns, confidence_level)
                es = self._expected_shortfall(returns, confidence_level)
            elif method == 'parametric':
                var = self._parametric_var(returns, confidence_level)
                es = self._parametric_expected_shortfall(returns, confidence_level)
            else:
                # Default to historical
                var = self._historical_var(returns, confidence_level)
                es = self._expected_shortfall(returns, confidence_level)
            
            var_metrics[f'var_{confidence_pct}_pct'] = var * 100
            var_metrics[f'es_{confidence_pct}_pct'] = es * 100
        
        return var_metrics
    
    def calculate_risk_adjusted_returns(
        self,
        snapshots: List[PortfolioSnapshot],
        risk_free_rate: float = 0.02
    ) -> Dict[str, float]:
        """
        Calculate risk-adjusted return metrics.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            risk_free_rate (float): Annual risk-free rate for Sharpe calculation
            
        Returns:
            Dict[str, float]: Risk-adjusted return metrics
        """
        if len(snapshots) < 2:
            return {}
        
        returns = self._calculate_returns(snapshots)
        
        if returns.empty:
            return {}
        
        # Convert risk-free rate to period rate
        daily_rf_rate = risk_free_rate / 252  # Assuming daily data
        
        # Excess returns
        excess_returns = returns - daily_rf_rate
        
        # Sharpe ratio
        sharpe_ratio = (
            (excess_returns.mean() / returns.std()) * np.sqrt(252)
            if returns.std() > 0 else 0.0
        )
        
        # Sortino ratio (using downside deviation)
        downside_returns = returns[returns < daily_rf_rate]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0.0
        sortino_ratio = (
            (excess_returns.mean() / downside_std) * np.sqrt(252)
            if downside_std > 0 else float('inf')
        )
        
        # Information ratio (simplified - tracking error vs benchmark)
        tracking_error = returns.std()
        information_ratio = returns.mean() / tracking_error if tracking_error > 0 else 0.0
        
        # Treynor ratio (simplified - assuming beta = 1)
        treynor_ratio = excess_returns.mean() * 252  # Annualized excess return
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'information_ratio': information_ratio,
            'treynor_ratio': treynor_ratio,
            'calmar_ratio': self._calculate_calmar_ratio(snapshots)
        }
    
    def calculate_drawdown_analysis(
        self,
        snapshots: List[PortfolioSnapshot]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive drawdown analysis.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            
        Returns:
            Dict[str, Any]: Drawdown analysis metrics
        """
        if not snapshots:
            return {}
        
        equity_values = [snapshot.total_equity for snapshot in snapshots]
        timestamps = [snapshot.timestamp for snapshot in snapshots]
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_values)
        
        # Calculate drawdown
        drawdown = (np.array(equity_values) - running_max) / running_max
        drawdown_pct = drawdown * 100
        
        # Find drawdown periods
        drawdown_periods = self._identify_drawdown_periods(timestamps, drawdown_pct)
        
        # Calculate statistics
        max_drawdown = np.min(drawdown_pct)
        avg_drawdown = np.mean(drawdown_pct[drawdown_pct < 0]) if np.any(drawdown_pct < 0) else 0.0
        
        # Current drawdown
        current_drawdown = drawdown_pct[-1]
        
        # Drawdown duration statistics
        if drawdown_periods:
            durations = [period['duration_days'] for period in drawdown_periods]
            max_duration = max(durations)
            avg_duration = np.mean(durations)
        else:
            max_duration = 0
            avg_duration = 0
        
        return {
            'max_drawdown_pct': max_drawdown,
            'avg_drawdown_pct': avg_drawdown,
            'current_drawdown_pct': current_drawdown,
            'max_drawdown_duration_days': max_duration,
            'avg_drawdown_duration_days': avg_duration,
            'total_drawdown_periods': len(drawdown_periods),
            'drawdown_periods': drawdown_periods
        }
    
    def calculate_tail_risk_metrics(
        self,
        snapshots: List[PortfolioSnapshot]
    ) -> Dict[str, float]:
        """
        Calculate tail risk metrics including skewness and kurtosis.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            
        Returns:
            Dict[str, float]: Tail risk metrics
        """
        if len(snapshots) < 2:
            return {}
        
        returns = self._calculate_returns(snapshots)
        
        if returns.empty:
            return {}
        
        # Skewness (measure of asymmetry)
        skewness = returns.skew()
        
        # Kurtosis (measure of tail heaviness)
        kurtosis = returns.kurtosis()
        
        # Jarque-Bera test statistic for normality
        n = len(returns)
        jb_statistic = (n / 6) * (skewness**2 + (kurtosis**2) / 4)
        
        # Semi-variance (downside variance)
        mean_return = returns.mean()
        downside_variance = np.mean(np.minimum(returns - mean_return, 0)**2)
        
        # Lower partial moments
        lpm_1 = np.mean(np.maximum(mean_return - returns, 0))  # First lower partial moment
        lpm_2 = np.mean(np.maximum(mean_return - returns, 0)**2)  # Second lower partial moment
        
        return {
            'skewness': skewness,
            'kurtosis': kurtosis,
            'jarque_bera_stat': jb_statistic,
            'downside_variance': downside_variance,
            'lower_partial_moment_1': lpm_1,
            'lower_partial_moment_2': lpm_2
        }
    
    def calculate_stress_test_metrics(
        self,
        snapshots: List[PortfolioSnapshot],
        stress_scenarios: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Perform stress testing on portfolio returns.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            stress_scenarios (Optional[Dict[str, float]]): Custom stress scenarios
            
        Returns:
            Dict[str, Any]: Stress test results
        """
        if len(snapshots) < 2:
            return {}
        
        returns = self._calculate_returns(snapshots)
        
        if returns.empty:
            return {}
        
        # Default stress scenarios
        if stress_scenarios is None:
            stress_scenarios = {
                'market_crash_5pct': -0.05,
                'market_crash_10pct': -0.10,
                'market_crash_20pct': -0.20,
                'volatility_spike_2x': returns.std() * 2,
                'volatility_spike_3x': returns.std() * 3
            }
        
        stress_results = {}
        current_equity = snapshots[-1].total_equity
        
        for scenario_name, shock_magnitude in stress_scenarios.items():
            if 'volatility' in scenario_name:
                # For volatility scenarios, simulate impact on portfolio
                stressed_return = returns.mean() - shock_magnitude
                stressed_equity = current_equity * (1 + stressed_return)
            else:
                # For price shock scenarios
                stressed_equity = current_equity * (1 + shock_magnitude)
            
            stress_impact = (stressed_equity - current_equity) / current_equity * 100
            
            stress_results[scenario_name] = {
                'shocked_equity': stressed_equity,
                'impact_pct': stress_impact,
                'scenario_description': f"Portfolio impact under {scenario_name}"
            }
        
        # Historical stress periods (worst consecutive periods)
        worst_periods = self._find_worst_periods(returns)
        
        return {
            'stress_scenarios': stress_results,
            'worst_historical_periods': worst_periods
        }
    
    def calculate_concentration_risk(
        self,
        trades: List[Trade],
        snapshots: List[PortfolioSnapshot]
    ) -> Dict[str, Any]:
        """
        Analyze concentration risk in trading activity.
        
        Args:
            trades (List[Trade]): Trade history
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            
        Returns:
            Dict[str, Any]: Concentration risk metrics
        """
        if not trades:
            return {}
        
        # Symbol concentration
        symbol_exposure = {}
        total_volume = sum(trade.notional_value for trade in trades)
        
        for trade in trades:
            if trade.symbol not in symbol_exposure:
                symbol_exposure[trade.symbol] = 0
            symbol_exposure[trade.symbol] += trade.notional_value
        
        # Calculate concentration metrics
        symbol_concentrations = {
            symbol: (volume / total_volume * 100) if total_volume > 0 else 0
            for symbol, volume in symbol_exposure.items()
        }
        
        # Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum((conc / 100) ** 2 for conc in symbol_concentrations.values())
        
        # Top concentrations
        sorted_concentrations = sorted(
            symbol_concentrations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'symbol_concentrations': symbol_concentrations,
            'herfindahl_index': hhi,
            'top_3_concentration_pct': sum(conc for _, conc in sorted_concentrations[:3]),
            'most_concentrated_symbol': sorted_concentrations[0] if sorted_concentrations else None,
            'diversification_ratio': 1 / hhi if hhi > 0 else 0
        }
    
    def _calculate_returns(self, snapshots: List[PortfolioSnapshot]) -> pd.Series:
        """Calculate returns from portfolio snapshots."""
        if len(snapshots) < 2:
            return pd.Series()
        
        equity_values = [snapshot.total_equity for snapshot in snapshots]
        timestamps = [snapshot.timestamp for snapshot in snapshots]
        
        df = pd.DataFrame({'equity': equity_values}, index=timestamps)
        returns = df['equity'].pct_change().dropna()
        
        return returns
    
    def _historical_var(self, returns: pd.Series, confidence_level: float) -> float:
        """Calculate historical VaR."""
        if returns.empty:
            return 0.0
        
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    def _parametric_var(self, returns: pd.Series, confidence_level: float) -> float:
        """Calculate parametric VaR assuming normal distribution."""
        if returns.empty:
            return 0.0
        
        from scipy.stats import norm
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Z-score for confidence level
        z_score = norm.ppf(1 - confidence_level)
        
        return mean_return + z_score * std_return
    
    def _expected_shortfall(self, returns: pd.Series, confidence_level: float) -> float:
        """Calculate Expected Shortfall (Conditional VaR)."""
        if returns.empty:
            return 0.0
        
        var_threshold = self._historical_var(returns, confidence_level)
        tail_returns = returns[returns <= var_threshold]
        
        return tail_returns.mean() if len(tail_returns) > 0 else 0.0
    
    def _parametric_expected_shortfall(self, returns: pd.Series, confidence_level: float) -> float:
        """Calculate parametric Expected Shortfall."""
        if returns.empty:
            return 0.0
        
        from scipy.stats import norm
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Z-score for confidence level
        z_score = norm.ppf(1 - confidence_level)
        
        # Expected shortfall formula for normal distribution
        es = mean_return - std_return * norm.pdf(z_score) / (1 - confidence_level)
        
        return es
    
    def _calculate_calmar_ratio(self, snapshots: List[PortfolioSnapshot]) -> float:
        """Calculate Calmar ratio (CAGR / Max Drawdown)."""
        if len(snapshots) < 2:
            return 0.0
        
        # Calculate CAGR
        initial_equity = snapshots[0].total_equity
        final_equity = snapshots[-1].total_equity
        
        days = (snapshots[-1].timestamp - snapshots[0].timestamp).days
        if days <= 0:
            return 0.0
        
        years = days / 365.25
        cagr = (final_equity / initial_equity) ** (1 / years) - 1
        
        # Calculate max drawdown
        equity_values = [snapshot.total_equity for snapshot in snapshots]
        running_max = np.maximum.accumulate(equity_values)
        drawdown = (np.array(equity_values) - running_max) / running_max
        max_drawdown = abs(np.min(drawdown))
        
        return cagr / max_drawdown if max_drawdown > 0 else float('inf')
    
    def _identify_drawdown_periods(
        self,
        timestamps: List[datetime],
        drawdown_pct: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Identify and analyze drawdown periods."""
        periods = []
        in_drawdown = False
        start_idx = None
        
        for i, dd in enumerate(drawdown_pct):
            if dd < -0.01 and not in_drawdown:  # Start of drawdown (> 1%)
                in_drawdown = True
                start_idx = i
            elif dd >= -0.01 and in_drawdown:  # End of drawdown
                in_drawdown = False
                if start_idx is not None:
                    period_dd = drawdown_pct[start_idx:i+1]
                    periods.append({
                        'start_date': timestamps[start_idx],
                        'end_date': timestamps[i],
                        'duration_days': (timestamps[i] - timestamps[start_idx]).days,
                        'max_drawdown_pct': np.min(period_dd),
                        'recovery_time_days': 0  # Could be enhanced to calculate recovery time
                    })
        
        # Handle case where drawdown continues to end
        if in_drawdown and start_idx is not None:
            period_dd = drawdown_pct[start_idx:]
            periods.append({
                'start_date': timestamps[start_idx],
                'end_date': timestamps[-1],
                'duration_days': (timestamps[-1] - timestamps[start_idx]).days,
                'max_drawdown_pct': np.min(period_dd),
                'recovery_time_days': None  # Ongoing
            })
        
        return periods
    
    def _find_worst_periods(self, returns: pd.Series, window: int = 5) -> List[Dict[str, Any]]:
        """Find worst consecutive return periods."""
        if len(returns) < window:
            return []
        
        rolling_returns = returns.rolling(window).sum()
        worst_periods = []
        
        # Find the 5 worst periods
        for i in range(5):
            if rolling_returns.empty:
                break
            
            min_idx = rolling_returns.idxmin()
            min_return = rolling_returns.loc[min_idx]
            
            # Get the window dates
            start_idx = returns.index.get_loc(min_idx) - window + 1
            start_date = returns.index[max(0, start_idx)]
            
            worst_periods.append({
                'period': f"{start_date.date()} to {min_idx.date()}",
                'cumulative_return_pct': min_return * 100,
                'window_days': window
            })
            
            # Remove this period from consideration
            rolling_returns = rolling_returns.drop(min_idx)
        
        return worst_periods