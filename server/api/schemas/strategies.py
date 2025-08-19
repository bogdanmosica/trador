"""
Pydantic Schemas for Strategy API

Defines the data models used for strategy-related API requests and responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class StrategyParameterSchema(BaseModel):
    """Schema definition for a strategy parameter."""
    type: str = Field(..., description="Parameter type (integer, number, string, boolean)")
    minimum: Optional[float] = Field(None, description="Minimum value for numeric parameters")
    maximum: Optional[float] = Field(None, description="Maximum value for numeric parameters")
    default: Any = Field(..., description="Default parameter value")
    description: str = Field(..., description="Parameter description")
    enum: Optional[List[Any]] = Field(None, description="Allowed values for enum parameters")


class StrategyMetadata(BaseModel):
    """Additional metadata about a strategy or configuration."""
    risk_profile: Optional[str] = Field(None, description="Risk profile (low, medium, high)")
    expected_sharpe: Optional[float] = Field(None, description="Expected Sharpe ratio")
    max_drawdown_target: Optional[float] = Field(None, description="Maximum drawdown target (%)")
    avg_holding_period_hours: Optional[float] = Field(None, description="Average holding period in hours")
    suitable_for: Optional[List[str]] = Field(None, description="Suitable use cases")
    version: Optional[str] = Field(None, description="Strategy version")
    author: Optional[str] = Field(None, description="Strategy author")
    created_date: Optional[datetime] = Field(None, description="Creation date")
    last_updated: Optional[datetime] = Field(None, description="Last update date")


class TradingSchedule(BaseModel):
    """Trading schedule configuration."""
    enabled: bool = Field(True, description="Whether schedule is enabled")
    trading_hours: Optional[Dict[str, str]] = Field(None, description="Trading hours (start/end times)")
    trading_days: Optional[List[str]] = Field(None, description="Allowed trading days")
    blackout_periods: Optional[List[Dict[str, Any]]] = Field(None, description="Blackout periods")


class StrategyPerformanceMetrics(BaseModel):
    """Performance metrics for a strategy."""
    total_return: Optional[float] = Field(None, description="Total return (%)")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown (%)")
    win_rate: Optional[float] = Field(None, description="Win rate (%)")
    profit_factor: Optional[float] = Field(None, description="Profit factor")
    total_trades: Optional[int] = Field(None, description="Total number of trades")
    avg_trade_duration: Optional[float] = Field(None, description="Average trade duration (hours)")


class StrategyBacktestRequest(BaseModel):
    """Request to backtest a strategy."""
    strategy_name: str = Field(..., description="Strategy class name")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(10000.0, description="Initial capital for backtest")
    symbols: List[str] = Field(..., description="Symbols to test")
    timeframe: str = Field("1h", description="Data timeframe")


class StrategyBacktestResponse(BaseModel):
    """Response from strategy backtest."""
    strategy_name: str = Field(..., description="Strategy that was tested")
    backtest_id: str = Field(..., description="Unique backtest identifier")
    status: str = Field(..., description="Backtest status (running, completed, failed)")
    start_time: datetime = Field(..., description="Backtest start time")
    end_time: Optional[datetime] = Field(None, description="Backtest end time")
    parameters: Dict[str, Any] = Field(..., description="Parameters used")
    performance: Optional[StrategyPerformanceMetrics] = Field(None, description="Performance results")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class StrategyComparisonRequest(BaseModel):
    """Request to compare multiple strategies."""
    strategies: List[Dict[str, Any]] = Field(..., description="List of strategy configs to compare")
    comparison_metrics: List[str] = Field(
        default=["sharpe_ratio", "max_drawdown", "total_return"],
        description="Metrics to compare"
    )
    start_date: datetime = Field(..., description="Comparison start date")
    end_date: datetime = Field(..., description="Comparison end date")


class StrategyComparisonResponse(BaseModel):
    """Response from strategy comparison."""
    comparison_id: str = Field(..., description="Unique comparison identifier")
    strategies: List[str] = Field(..., description="Strategies that were compared")
    results: Dict[str, StrategyPerformanceMetrics] = Field(..., description="Results for each strategy")
    ranking: List[str] = Field(..., description="Strategies ranked by performance")
    best_strategy: str = Field(..., description="Best performing strategy")
    comparison_date: datetime = Field(..., description="When comparison was performed")


class StrategyOptimizationRequest(BaseModel):
    """Request to optimize strategy parameters."""
    strategy_name: str = Field(..., description="Strategy to optimize")
    parameter_ranges: Dict[str, Dict[str, float]] = Field(..., description="Parameter ranges for optimization")
    optimization_target: str = Field("sharpe_ratio", description="Metric to optimize")
    max_iterations: int = Field(100, description="Maximum optimization iterations")
    start_date: datetime = Field(..., description="Optimization period start")
    end_date: datetime = Field(..., description="Optimization period end")


class StrategyOptimizationResponse(BaseModel):
    """Response from parameter optimization."""
    optimization_id: str = Field(..., description="Unique optimization identifier")
    strategy_name: str = Field(..., description="Strategy that was optimized")
    best_parameters: Dict[str, Any] = Field(..., description="Optimal parameters found")
    best_score: float = Field(..., description="Best optimization score achieved")
    iterations_completed: int = Field(..., description="Number of iterations completed")
    optimization_time: float = Field(..., description="Time taken for optimization (seconds)")
    status: str = Field(..., description="Optimization status")


class StrategyDeploymentRequest(BaseModel):
    """Request to deploy a strategy for live trading."""
    strategy_name: str = Field(..., description="Strategy to deploy")
    configuration_name: str = Field(..., description="Configuration to use")
    symbol: str = Field(..., description="Symbol to trade")
    initial_capital: float = Field(..., description="Initial capital allocation")
    max_position_size: float = Field(0.1, description="Maximum position size (fraction of capital)")
    risk_limits: Dict[str, float] = Field(default_factory=dict, description="Risk management limits")


class StrategyDeploymentResponse(BaseModel):
    """Response from strategy deployment."""
    deployment_id: str = Field(..., description="Unique deployment identifier")
    strategy_name: str = Field(..., description="Deployed strategy")
    status: str = Field(..., description="Deployment status")
    live_since: datetime = Field(..., description="When strategy went live")
    current_position: Optional[Dict[str, Any]] = Field(None, description="Current position details")
    daily_pnl: float = Field(0.0, description="Current day P&L")
    total_pnl: float = Field(0.0, description="Total P&L since deployment")