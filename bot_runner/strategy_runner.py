"""
Contains the StrategyRunner class, the core logic for running a single trading strategy.
"""

import asyncio
import logging
from typing import Coroutine

from trador.strategy.base_strategy import BaseStrategy
from trador.market_data.providers.base import MarketDataProvider
from trador.execution_engine.engines.base import ExecutionEngine
from trador.portfolio_risk.portfolio_manager import PortfolioManager
from trador.portfolio_risk.exceptions import RiskViolationError

logger = logging.getLogger(__name__)

class StrategyRunner:
    """
    Orchestrates the real-time event loop for a single trading strategy.

    This class connects the market data feed, the strategy logic, and the
    execution engine, and it manages the main async loop for a bot.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        market_data_provider: MarketDataProvider,
        execution_engine: ExecutionEngine,
        portfolio_manager: PortfolioManager,
        symbol: str,
        timeframe: str
    ):
        self.strategy = strategy
        self.market_data_provider = market_data_provider
        self.execution_engine = execution_engine
        self.portfolio_manager = portfolio_manager
        self.symbol = symbol
        self.timeframe = timeframe
        
        self._is_running = False
        self._main_task: Coroutine | None = None

    async def run(self):
        """
        Starts the main event loop for the strategy.

        This loop listens for new market data, generates signals, and executes trades.
        """
        self._is_running = True
        logger.info(f"Starting runner for strategy '{self.strategy.strategy_name}' on {self.symbol}...")

        try:
            # Start all components
            await self.market_data_provider.connect()
            await self.execution_engine.start()

            candle_stream = self.market_data_provider.stream_candles(self.symbol, self.timeframe)

            async for candle in candle_stream:
                if not self._is_running:
                    break

                # 1. Get current position state from the portfolio manager
                current_position = self.portfolio_manager.state.open_positions.get(self.symbol)

                # 2. Generate signals from the strategy
                # The base strategy expects a list of market data
                signals = self.strategy.generate_signals([candle], current_position, self.strategy.parameters)

                if not signals:
                    continue

                # 3. Submit signals to the execution engine
                for signal in signals:
                    try:
                        logger.info(f"Generated signal: {signal.action} {self.symbol}")
                        await self.execution_engine.submit_signal(signal)
                    except RiskViolationError as e:
                        logger.warning(f"Trade rejected for strategy '{self.strategy.strategy_name}': {e}")
                        # If it was a critical violation, the engine will have initiated a flatten.
                        # We should stop the runner.
                        if e.violations and any("Drawdown" in v for v in e.violations):
                            logger.critical("Kill-switch activated due to drawdown. Stopping runner.")
                            self._is_running = False
                    except Exception as e:
                        logger.error(f"Error executing signal for strategy '{self.strategy.strategy_name}': {e}", exc_info=True)

        except Exception as e:
            logger.error(f"An unexpected error occurred in the runner for '{self.strategy.strategy_name}': {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        """Stops the event loop and cleans up resources."""
        if not self._is_running:
            return
            
        self._is_running = False
        logger.info(f"Stopping runner for strategy '{self.strategy.strategy_name}'...")

        # Stop the components
        if self.execution_engine._is_running:
            await self.execution_engine.stop()
        if self.market_data_provider:
             await self.market_data_provider.disconnect()

        logger.info(f"Runner for '{self.strategy.strategy_name}' has stopped.")
