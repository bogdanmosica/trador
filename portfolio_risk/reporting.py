"""
Generates reports from portfolio data.

This module provides functions to export portfolio data, such as trade logs
and equity curves, into common formats like CSV.
"""

import csv
from .portfolio_manager import PortfolioManager

def generate_trade_log_csv(portfolio_manager: PortfolioManager, output_path: str):
    """
    Generates a CSV file of the trade history from a PortfolioManager.

    Args:
        portfolio_manager: The PortfolioManager instance containing the trade data.
        output_path: The path to write the CSV file to.
    """
    with open(output_path, 'w', newline='') as csvfile:
        if not portfolio_manager.state.trade_history:
            csvfile.write("No trades recorded.")
            return

        # Use the fields from the Trade dataclass as headers
        fieldnames = portfolio_manager.state.trade_history[0].__dict__.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for trade in portfolio_manager.state.trade_history:
            writer.writerow(trade.__dict__)

    print(f"Trade log successfully generated at: {output_path}")

def generate_equity_curve_csv(portfolio_manager: PortfolioManager, output_path: str):
    """
    Generates a CSV file of the equity curve from a PortfolioManager.

    Args:
        portfolio_manager: The PortfolioManager instance containing the equity data.
        output_path: The path to write the CSV file to.
    """
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "equity"])
        
        if not portfolio_manager.state.equity_curve:
            return

        for timestamp, equity in portfolio_manager.state.equity_curve:
            writer.writerow([timestamp.isoformat(), equity])

    print(f"Equity curve successfully generated at: {output_path}")
