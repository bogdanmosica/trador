"""
Report Generator

Creates comprehensive backtest reports in multiple formats including
CSV, JSON, and HTML. Provides detailed analysis summaries and
visualization-ready data exports.
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..models import Trade
from ..portfolio import PortfolioSnapshot
from .performance_analyzer import PerformanceAnalyzer


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive backtest reports in multiple formats.
    
    Creates detailed reports including performance metrics, trade history,
    and portfolio analytics suitable for strategy evaluation and sharing.
    """
    
    def __init__(self, output_dir: str = "./backtest_reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir (str): Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_full_report(
        self,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        snapshots: List[PortfolioSnapshot],
        trades: List[Trade],
        performance_metrics: Dict[str, Any],
        initial_balance: float,
        config_dict: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate a complete backtest report in multiple formats.
        
        Args:
            strategy_name (str): Name of tested strategy
            symbol (str): Trading symbol
            start_date (datetime): Backtest start date
            end_date (datetime): Backtest end date
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            trades (List[Trade]): Executed trades
            performance_metrics (Dict[str, Any]): Performance metrics
            initial_balance (float): Starting balance
            config_dict (Dict[str, Any]): Backtest configuration
            
        Returns:
            Dict[str, str]: Dictionary of generated file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{strategy_name}_{symbol}_{timestamp}"
        
        generated_files = {}
        
        # Generate JSON report
        json_path = self._generate_json_report(
            base_filename,
            strategy_name,
            symbol,
            start_date,
            end_date,
            snapshots,
            trades,
            performance_metrics,
            initial_balance,
            config_dict
        )
        generated_files['json'] = str(json_path)
        
        # Generate CSV reports
        csv_files = self._generate_csv_reports(
            base_filename,
            snapshots,
            trades,
            performance_metrics
        )
        generated_files.update(csv_files)
        
        # Generate summary report
        summary_path = self._generate_summary_report(
            base_filename,
            strategy_name,
            symbol,
            start_date,
            end_date,
            performance_metrics,
            initial_balance
        )
        generated_files['summary'] = str(summary_path)
        
        logger.info(f"Generated reports in: {self.output_dir}")
        return generated_files
    
    def _generate_json_report(
        self,
        base_filename: str,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        snapshots: List[PortfolioSnapshot],
        trades: List[Trade],
        performance_metrics: Dict[str, Any],
        initial_balance: float,
        config_dict: Dict[str, Any]
    ) -> Path:
        """
        Generate comprehensive JSON report.
        
        Args:
            base_filename (str): Base filename for report
            strategy_name (str): Strategy name
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            trades (List[Trade]): Trades
            performance_metrics (Dict[str, Any]): Performance metrics
            initial_balance (float): Initial balance
            config_dict (Dict[str, Any]): Configuration
            
        Returns:
            Path: Path to generated JSON file
        """
        report_data = {
            'metadata': {
                'strategy_name': strategy_name,
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days,
                'initial_balance': initial_balance,
                'report_generated': datetime.now().isoformat()
            },
            'configuration': config_dict,
            'performance_metrics': performance_metrics,
            'portfolio_snapshots': [
                {
                    'timestamp': snapshot.timestamp.isoformat(),
                    'total_equity': snapshot.total_equity,
                    'cash_balance': snapshot.cash_balance,
                    'total_position_value': snapshot.total_position_value,
                    'unrealized_pnl': snapshot.unrealized_pnl,
                    'realized_pnl': snapshot.realized_pnl,
                    'total_fees': snapshot.total_fees,
                    'trade_count': snapshot.trade_count,
                    'total_return': snapshot.total_return
                }
                for snapshot in snapshots
            ],
            'trades': [
                {
                    'trade_id': trade.trade_id,
                    'order_id': trade.order_id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'timestamp': trade.timestamp.isoformat(),
                    'fees': trade.fees,
                    'fee_currency': trade.fee_currency,
                    'is_maker': trade.is_maker,
                    'notional_value': trade.notional_value,
                    'net_value': trade.net_value,
                    'metadata': trade.metadata
                }
                for trade in trades
            ]
        }
        
        json_path = self.output_dir / f"{base_filename}_full_report.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return json_path
    
    def _generate_csv_reports(
        self,
        base_filename: str,
        snapshots: List[PortfolioSnapshot],
        trades: List[Trade],
        performance_metrics: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate CSV reports for different data types.
        
        Args:
            base_filename (str): Base filename
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            trades (List[Trade]): Trades
            performance_metrics (Dict[str, Any]): Performance metrics
            
        Returns:
            Dict[str, str]: Dictionary of generated CSV file paths
        """
        csv_files = {}
        
        # Portfolio equity curve CSV
        equity_path = self.output_dir / f"{base_filename}_equity_curve.csv"
        with open(equity_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'total_equity', 'cash_balance', 'unrealized_pnl',
                'realized_pnl', 'total_fees', 'total_return_pct'
            ])
            
            for snapshot in snapshots:
                writer.writerow([
                    snapshot.timestamp.isoformat(),
                    snapshot.total_equity,
                    snapshot.cash_balance,
                    snapshot.unrealized_pnl,
                    snapshot.realized_pnl,
                    snapshot.total_fees,
                    snapshot.total_return
                ])
        
        csv_files['equity_curve'] = str(equity_path)
        
        # Trades CSV
        trades_path = self.output_dir / f"{base_filename}_trades.csv"
        with open(trades_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'trade_id', 'order_id', 'symbol', 'side', 'quantity', 'price',
                'timestamp', 'fees', 'notional_value', 'net_value', 'is_maker'
            ])
            
            for trade in trades:
                writer.writerow([
                    trade.trade_id,
                    trade.order_id,
                    trade.symbol,
                    trade.side,
                    trade.quantity,
                    trade.price,
                    trade.timestamp.isoformat(),
                    trade.fees,
                    trade.notional_value,
                    trade.net_value,
                    trade.is_maker
                ])
        
        csv_files['trades'] = str(trades_path)
        
        # Performance metrics CSV
        metrics_path = self.output_dir / f"{base_filename}_metrics.csv"
        with open(metrics_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['metric', 'value'])
            
            for metric, value in performance_metrics.items():
                writer.writerow([metric, value])
        
        csv_files['metrics'] = str(metrics_path)
        
        return csv_files
    
    def _generate_summary_report(
        self,
        base_filename: str,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        performance_metrics: Dict[str, Any],
        initial_balance: float
    ) -> Path:
        """
        Generate human-readable summary report.
        
        Args:
            base_filename (str): Base filename
            strategy_name (str): Strategy name
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            performance_metrics (Dict[str, Any]): Performance metrics
            initial_balance (float): Initial balance
            
        Returns:
            Path: Path to generated summary file
        """
        summary_path = self.output_dir / f"{base_filename}_summary.txt"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"BACKTEST SUMMARY REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            # Basic information
            f.write("BASIC INFORMATION\n")
            f.write("-" * 20 + "\n")
            f.write(f"Strategy: {strategy_name}\n")
            f.write(f"Symbol: {symbol}\n")
            f.write(f"Period: {start_date.date()} to {end_date.date()}\n")
            f.write(f"Duration: {(end_date - start_date).days} days\n")
            f.write(f"Initial Balance: ${initial_balance:,.2f}\n\n")
            
            # Performance metrics
            f.write("PERFORMANCE METRICS\n")
            f.write("-" * 20 + "\n")
            
            final_equity = performance_metrics.get('final_equity', initial_balance)
            total_return = performance_metrics.get('total_return_pct', 0)
            cagr = performance_metrics.get('cagr_pct', 0)
            max_dd = performance_metrics.get('max_drawdown_pct', 0)
            sharpe = performance_metrics.get('sharpe_ratio', 0)
            
            f.write(f"Final Equity: ${final_equity:,.2f}\n")
            f.write(f"Total Return: {total_return:.2f}%\n")
            f.write(f"CAGR: {cagr:.2f}%\n")
            f.write(f"Maximum Drawdown: {max_dd:.2f}%\n")
            f.write(f"Sharpe Ratio: {sharpe:.2f}\n")
            f.write(f"Volatility: {performance_metrics.get('volatility_pct', 0):.2f}%\n\n")
            
            # Trading statistics
            f.write("TRADING STATISTICS\n")
            f.write("-" * 20 + "\n")
            
            total_trades = performance_metrics.get('total_trades', 0)
            win_rate = performance_metrics.get('win_rate_pct', 0)
            avg_win = performance_metrics.get('avg_win', 0)
            avg_loss = performance_metrics.get('avg_loss', 0)
            profit_factor = performance_metrics.get('profit_factor', 0)
            
            f.write(f"Total Trades: {total_trades}\n")
            f.write(f"Win Rate: {win_rate:.2f}%\n")
            f.write(f"Average Win: ${avg_win:.2f}\n")
            f.write(f"Average Loss: ${avg_loss:.2f}\n")
            f.write(f"Profit Factor: {profit_factor:.2f}\n")
            f.write(f"Total Fees: ${performance_metrics.get('total_fees', 0):.2f}\n\n")
            
            # Risk metrics
            f.write("RISK METRICS\n")
            f.write("-" * 20 + "\n")
            
            f.write(f"Sortino Ratio: {performance_metrics.get('sortino_ratio', 0):.2f}\n")
            f.write(f"Calmar Ratio: {performance_metrics.get('calmar_ratio', 0):.2f}\n")
            f.write(f"VaR (95%): {performance_metrics.get('var_95_pct', 0):.2f}%\n")
            f.write(f"Expected Shortfall: {performance_metrics.get('expected_shortfall_pct', 0):.2f}%\n\n")
            
            # Footer
            f.write("=" * 60 + "\n")
            f.write(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n")
        
        return summary_path
    
    def generate_comparison_report(
        self,
        results: List[Dict[str, Any]],
        comparison_name: str = "strategy_comparison"
    ) -> str:
        """
        Generate comparison report for multiple backtest results.
        
        Args:
            results (List[Dict[str, Any]]): List of backtest results to compare
            comparison_name (str): Name for comparison report
            
        Returns:
            str: Path to generated comparison report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_path = self.output_dir / f"{comparison_name}_{timestamp}.csv"
        
        if not results:
            logger.warning("No results provided for comparison report")
            return str(comparison_path)
        
        # Extract key metrics for comparison
        comparison_data = []
        
        for result in results:
            metrics = result.get('performance_metrics', {})
            metadata = result.get('metadata', {})
            
            row = {
                'strategy_name': metadata.get('strategy_name', 'Unknown'),
                'symbol': metadata.get('symbol', 'Unknown'),
                'duration_days': metadata.get('duration_days', 0),
                'total_return_pct': metrics.get('total_return_pct', 0),
                'cagr_pct': metrics.get('cagr_pct', 0),
                'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'sortino_ratio': metrics.get('sortino_ratio', 0),
                'win_rate_pct': metrics.get('win_rate_pct', 0),
                'total_trades': metrics.get('total_trades', 0),
                'profit_factor': metrics.get('profit_factor', 0),
                'volatility_pct': metrics.get('volatility_pct', 0)
            }
            comparison_data.append(row)
        
        # Write comparison CSV
        with open(comparison_path, 'w', newline='', encoding='utf-8') as f:
            if comparison_data:
                writer = csv.DictWriter(f, fieldnames=comparison_data[0].keys())
                writer.writeheader()
                writer.writerows(comparison_data)
        
        logger.info(f"Comparison report generated: {comparison_path}")
        return str(comparison_path)
    
    def export_for_visualization(
        self,
        snapshots: List[PortfolioSnapshot],
        trades: List[Trade],
        export_name: str = "visualization_data"
    ) -> Dict[str, str]:
        """
        Export data in format suitable for visualization tools.
        
        Args:
            snapshots (List[PortfolioSnapshot]): Portfolio snapshots
            trades (List[Trade]): Trade history
            export_name (str): Base name for exported files
            
        Returns:
            Dict[str, str]: Dictionary of exported file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{export_name}_{timestamp}"
        
        exported_files = {}
        
        # OHLC-style data for charting
        ohlc_path = self.output_dir / f"{base_name}_ohlc.csv"
        with open(ohlc_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'equity', 'drawdown_pct'])
            
            max_equity = 0
            for snapshot in snapshots:
                if snapshot.total_equity > max_equity:
                    max_equity = snapshot.total_equity
                
                drawdown = (max_equity - snapshot.total_equity) / max_equity * 100 if max_equity > 0 else 0
                
                writer.writerow([
                    snapshot.timestamp.isoformat(),
                    snapshot.total_equity,
                    drawdown
                ])
        
        exported_files['ohlc'] = str(ohlc_path)
        
        # Trade markers for overlaying on charts
        markers_path = self.output_dir / f"{base_name}_trade_markers.csv"
        with open(markers_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'price', 'side', 'quantity', 'trade_id'])
            
            for trade in trades:
                writer.writerow([
                    trade.timestamp.isoformat(),
                    trade.price,
                    trade.side,
                    trade.quantity,
                    trade.trade_id
                ])
        
        exported_files['trade_markers'] = str(markers_path)
        
        return exported_files