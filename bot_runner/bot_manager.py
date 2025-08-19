"""
Contains the BotManager class for running multiple strategies concurrently.
"""

import asyncio
import logging
from typing import List

from .strategy_runner import StrategyRunner

logger = logging.getLogger(__name__)

class BotManager:
    """
    Manages and runs multiple StrategyRunner instances concurrently.
    """

    def __init__(self):
        self.runners: List[StrategyRunner] = []
        self._tasks: List[asyncio.Task] = []

    def add_bot(self, runner: StrategyRunner):
        """Adds a configured StrategyRunner to the manager."""
        if not isinstance(runner, StrategyRunner):
            raise TypeError("Only StrategyRunner instances can be added.")
        self.runners.append(runner)
        logger.info(f"Added bot for strategy '{runner.strategy.strategy_name}' on {runner.symbol}")

    async def run_all(self):
        """
        Runs all added bots concurrently.
        """
        if not self.runners:
            logger.warning("No bots to run.")
            return

        logger.info(f"Starting BotManager with {len(self.runners)} bots.")
        self._tasks = [asyncio.create_task(runner.run()) for runner in self.runners]
        
        try:
            await asyncio.gather(*self._tasks)
        except Exception as e:
            logger.error(f"An error occurred in BotManager: {e}", exc_info=True)
        finally:
            logger.info("BotManager is shutting down.")

    async def stop_all(self):
        """
        Stops all running bots gracefully.
        """
        logger.info("Stopping all bots...")
        for runner in self.runners:
            await runner.stop()
        
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("All bots have been stopped.")
