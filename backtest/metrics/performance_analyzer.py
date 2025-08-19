"""
Performance Analyzer

Calculates comprehensive performance metrics for backtesting results.
Provides detailed analysis of returns, risk, and trading statistics
for strategy evaluation and comparison.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..models import Trade
from ..portfolio import PortfolioSnapshot


logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Analyzes backtest performance with comprehensive metrics.
    
    Calculates risk-adjusted returns, drawdown analysis, trading statistics,
    and other performance metrics essential for strategy evaluation.
    """
    
    def __init__(self, initial_balance: float):
        """
        Initialize performance analyzer.
        
        Args:
            initial_balance (float): Starting portfolio value
        """
        self.initial_balance = initial_balance
    
    def analyze_performance(
        self,
        snapshots: List[PortfolioSnapshot],
        trades: List[Trade]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive performance analysis.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots over time
            trades (List[Trade]): Executed trades
            
        Returns:
            Dict[str, Any]: Comprehensive performance metrics
        """
        if not snapshots:
            return self._empty_metrics()
        
        # Convert to DataFrame for analysis
        equity_curve = self._create_equity_curve(snapshots)
        
        # Calculate metrics
        metrics = {}
        
        # Basic performance metrics
        metrics.update(self._calculate_basic_metrics(equity_curve, trades))
        
        # Risk metrics
        metrics.update(self._calculate_risk_metrics(equity_curve))
        
        # Drawdown analysis
        metrics.update(self._calculate_drawdown_metrics(equity_curve))
        
        # Trading statistics
        metrics.update(self._calculate_trading_stats(trades))
        
        # Advanced metrics
        metrics.update(self._calculate_advanced_metrics(equity_curve))
        
        return metrics
    
    def _create_equity_curve(self, snapshots: List[PortfolioSnapshot]) -> pd.DataFrame:
        """
        Create equity curve DataFrame from portfolio snapshots.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            
        Returns:
            pd.DataFrame: Equity curve with timestamps and values
        """
        data = []
        for snapshot in snapshots:
            data.append({
                'timestamp': snapshot.timestamp,
                'equity': snapshot.total_equity,
                'cash': snapshot.cash_balance,
                'unrealized_pnl': snapshot.unrealized_pnl,
                'realized_pnl': snapshot.realized_pnl,
                'total_fees': snapshot.total_fees
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate returns
        df['returns'] = df['equity'].pct_change()
        df['cumulative_returns'] = (df['equity'] / self.initial_balance - 1) * 100
        
        return df
    
    def _calculate_basic_metrics(self, equity_curve: pd.DataFrame, trades: List[Trade]) -> Dict[str, float]:
        """
        Calculate basic performance metrics.
        
        Args:
            equity_curve (pd.DataFrame): Equity curve data
            trades (List[Trade]): Executed trades
            
        Returns:
            Dict[str, float]: Basic performance metrics
        """
        if equity_curve.empty:
            return {}
        
        final_equity = equity_curve['equity'].iloc[-1]
        total_return = (final_equity / self.initial_balance - 1) * 100
        
        # Calculate CAGR (Compound Annual Growth Rate)
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        if days > 0:
            years = days / 365.25
            cagr = ((final_equity / self.initial_balance) ** (1 / years) - 1) * 100
        else:
            cagr = 0.0
        
        return {
            'total_return_pct': total_return,
            'final_equity': final_equity,
            'cagr_pct': cagr,
            'total_trades': len(trades),
            'period_days': days if 'days' in locals() else 0
        }
    
    def _calculate_risk_metrics(self, equity_curve: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate risk-related metrics.
        
        Args:
            equity_curve (pd.DataFrame): Equity curve data
            
        Returns:
            Dict[str, float]: Risk metrics
        """
        if equity_curve.empty or len(equity_curve) < 2:
            return {}
        
        returns = equity_curve['returns'].dropna()
        
        if returns.empty:
            return {}
        
        # Volatility (annualized)
        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(252) * 100  # Assuming daily data
        
        # Sharpe ratio (simplified, assuming 0% risk-free rate)
        avg_return = returns.mean()
        sharpe_ratio = (avg_return / daily_vol) * np.sqrt(252) if daily_vol > 0 else 0.0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_vol = downside_returns.std()
            sortino_ratio = (avg_return / downside_vol) * np.sqrt(252) if downside_vol > 0 else 0.0
        else:
            sortino_ratio = float('inf') if avg_return > 0 else 0.0
        
        # Calmar ratio (CAGR / Max Drawdown)
        max_dd = self._calculate_max_drawdown(equity_curve['equity'])
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        if days > 0:
            years = days / 365.25
            final_equity = equity_curve['equity'].iloc[-1]
            cagr = ((final_equity / self.initial_balance) ** (1 / years) - 1) * 100
            calmar_ratio = cagr / abs(max_dd) if max_dd != 0 else float('inf')
        else:
            calmar_ratio = 0.0
        
        return {
            'volatility_pct': annual_vol,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio
        }
    
    def _calculate_drawdown_metrics(self, equity_curve: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate drawdown-related metrics.
        
        Args:
            equity_curve (pd.DataFrame): Equity curve data
            
        Returns:
            Dict[str, float]: Drawdown metrics
        """
        if equity_curve.empty:
            return {}
        
        equity = equity_curve['equity']
        
        # Calculate drawdown
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max * 100
        
        max_drawdown = drawdown.min()
        
        # Average drawdown
        negative_dd = drawdown[drawdown < 0]
        avg_drawdown = negative_dd.mean() if len(negative_dd) > 0 else 0.0
        
        # Max drawdown duration
        max_dd_duration = self._calculate_max_drawdown_duration(equity)
        
        # Current drawdown
        current_drawdown = drawdown.iloc[-1]
        
        return {
            'max_drawdown_pct': max_drawdown,
            'avg_drawdown_pct': avg_drawdown,
            'current_drawdown_pct': current_drawdown,
            'max_drawdown_duration_days': max_dd_duration
        }
    
    def _calculate_trading_stats(self, trades: List[Trade]) -> Dict[str, float]:
        """
        Calculate trading statistics.
        
        Args:
            trades (List[Trade]): Executed trades
            
        Returns:
            Dict[str, float]: Trading statistics
        """
        if not trades:
            return {
                'win_rate_pct': 0.0,
                'avg_win_pct': 0.0,
                'avg_loss_pct': 0.0,
                'profit_factor': 0.0,
                'avg_trade_duration_hours': 0.0
            }
        
        # Group trades by order_id to get complete round trips
        trade_groups = {}
        for trade in trades:
            if trade.order_id not in trade_groups:
                trade_groups[trade.order_id] = []
            trade_groups[trade.order_id].append(trade)
        
        # Calculate P&L for each trade group
        trade_pnls = []
        trade_durations = []
        
        for order_id, order_trades in trade_groups.items():
            total_pnl = sum(trade.net_value for trade in order_trades)
            trade_pnls.append(total_pnl)
            
            # Calculate duration (simplified)
            if len(order_trades) > 1:
                duration = order_trades[-1].timestamp - order_trades[0].timestamp
                trade_durations.append(duration.total_seconds() / 3600)  # Hours
        
        # Win rate
        winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
        losing_trades = [pnl for pnl in trade_pnls if pnl < 0]
        
        win_rate = (len(winning_trades) / len(trade_pnls)) * 100 if trade_pnls else 0.0
        
        # Average win/loss
        avg_win = np.mean(winning_trades) if winning_trades else 0.0
        avg_loss = np.mean(losing_trades) if losing_trades else 0.0
        
        # Profit factor
        total_wins = sum(winning_trades) if winning_trades else 0.0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Average trade duration
        avg_duration = np.mean(trade_durations) if trade_durations else 0.0
        
        return {
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_trade_duration_hours': avg_duration,
            'total_winning_trades': len(winning_trades),
            'total_losing_trades': len(losing_trades)
        }
    
    def _calculate_advanced_metrics(self, equity_curve: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate advanced performance metrics.
        
        Args:
            equity_curve (pd.DataFrame): Equity curve data
            
        Returns:
            Dict[str, float]: Advanced metrics
        """
        if equity_curve.empty or len(equity_curve) < 2:
            return {}
        
        returns = equity_curve['returns'].dropna()
        
        if returns.empty:
            return {}
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) * 100
        
        # Expected Shortfall (Conditional VaR)
        var_threshold = np.percentile(returns, 5)
        tail_returns = returns[returns <= var_threshold]
        expected_shortfall = tail_returns.mean() * 100 if len(tail_returns) > 0 else 0.0
        
        # Skewness and Kurtosis
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        # Information ratio (simplified)
        tracking_error = returns.std()
        info_ratio = returns.mean() / tracking_error if tracking_error > 0 else 0.0
        
        return {
            'var_95_pct': var_95,
            'expected_shortfall_pct': expected_shortfall,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'information_ratio': info_ratio
        }
    
    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            equity (pd.Series): Equity values
            
        Returns:
            float: Maximum drawdown percentage
        """
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max * 100
        return drawdown.min()
    
    def _calculate_max_drawdown_duration(self, equity: pd.Series) -> int:
        """
        Calculate maximum drawdown duration in days.
        
        Args:
            equity (pd.Series): Equity values with datetime index
            
        Returns:
            int: Maximum drawdown duration in days
        """
        running_max = equity.expanding().max()
        drawdown = equity - running_max
        
        # Find periods where we're in drawdown
        in_drawdown = drawdown < 0
        
        if not in_drawdown.any():
            return 0
        
        # Calculate consecutive drawdown periods
        drawdown_periods = []
        start_date = None
        
        for date, is_dd in in_drawdown.items():
            if is_dd and start_date is None:
                start_date = date
            elif not is_dd and start_date is not None:
                duration = (date - start_date).days
                drawdown_periods.append(duration)
                start_date = None
        
        # Handle case where drawdown continues to end
        if start_date is not None:
            duration = (equity.index[-1] - start_date).days
            drawdown_periods.append(duration)
        
        return max(drawdown_periods) if drawdown_periods else 0
    
    def _empty_metrics(self) -> Dict[str, float]:
        """
        Return empty metrics dictionary.
        
        Returns:
            Dict[str, float]: Empty metrics with default values
        """
        return {
            'total_return_pct': 0.0,
            'final_equity': self.initial_balance,
            'cagr_pct': 0.0,
            'volatility_pct': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown_pct': 0.0,
            'win_rate_pct': 0.0,
            'total_trades': 0
        }
    
    def calculate_monthly_returns(self, snapshots: List[PortfolioSnapshot]) -> pd.DataFrame:
        """
        Calculate monthly returns breakdown.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            
        Returns:
            pd.DataFrame: Monthly returns breakdown
        """
        if not snapshots:
            return pd.DataFrame()
        
        equity_curve = self._create_equity_curve(snapshots)
        
        # Resample to monthly
        monthly_equity = equity_curve['equity'].resample('M').last()
        monthly_returns = monthly_equity.pct_change() * 100
        
        monthly_df = pd.DataFrame({
            'equity': monthly_equity,
            'return_pct': monthly_returns
        })
        
        return monthly_df.dropna()
    
    def calculate_rolling_metrics(
        self,
        snapshots: List[PortfolioSnapshot],
        window_days: int = 30
    ) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            window_days (int): Rolling window size in days
            
        Returns:
            pd.DataFrame: Rolling metrics over time
        """
        if not snapshots:
            return pd.DataFrame()
        
        equity_curve = self._create_equity_curve(snapshots)
        
        if len(equity_curve) < window_days:
            return pd.DataFrame()
        
        rolling_df = pd.DataFrame(index=equity_curve.index)
        
        # Rolling returns
        rolling_df['rolling_return_pct'] = equity_curve['returns'].rolling(window_days).mean() * 100
        
        # Rolling volatility
        rolling_df['rolling_volatility_pct'] = equity_curve['returns'].rolling(window_days).std() * 100
        
        # Rolling Sharpe ratio
        rolling_df['rolling_sharpe'] = (
            rolling_df['rolling_return_pct'] / rolling_df['rolling_volatility_pct']
        ).fillna(0)
        
        # Rolling max drawdown
        rolling_df['rolling_max_dd_pct'] = equity_curve['equity'].rolling(window_days).apply(
            lambda x: self._calculate_max_drawdown(x)
        )
        
        return rolling_df.dropna()