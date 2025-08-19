"""
Main entry point for running the trading bots.

This script demonstrates how to configure and run multiple trading bots
concurrently using the BotManager. It shows how to set up different trading
modes (simulated, paper, live) by injecting the appropriate components.
"""

import asyncio
import logging

# Import all the necessary components from the project
from trador.bot_runner.bot_manager import BotManager
from trador.bot_runner.strategy_runner import StrategyRunner
from trador.strategy.strategies.sma_crossover import SmaCrossoverStrategy
from trador.portfolio_risk.portfolio_manager import PortfolioManager
from trador.execution_engine.engines.simulated import SimulatedExecutionEngine
from trador.market_data.providers.mock import MockProvider
from trador.market_data.providers.binance_rest import BinanceRESTProvider
from trador.execution_engine.models import ExecutionConfig
from trador.market_data.models import MarketDataConfig

# --- Configuration ---

# 1. Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Log to console
        # logging.FileHandler("trador.log") # Optionally log to a file
    ]
)

# 2. Define the bots to run
# Each bot needs a strategy, a symbol, a timeframe, and an initial equity.
BOT_CONFIGS = [
    {
        "strategy_name": "sma_crossover_conservative",
        "strategy_params": {"fast_period": 20, "slow_period": 50},
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "initial_equity": 10000,
        "mode": "paper" # paper, simulated
    },
    {
        "strategy_name": "sma_crossover_aggressive",
        "strategy_params": {"fast_period": 9, "slow_period": 21},
        "symbol": "ETHUSDT",
        "timeframe": "15m",
        "initial_equity": 5000,
        "mode": "simulated"
    }
]

# 3. Define Risk Rules for all strategies
# In a real application, these could be part of the BOT_CONFIGS
RISK_RULES = [
    {"name": "max_position_size", "max_size_usd": 20000},
    {"name": "max_drawdown", "max_drawdown_pct": 15.0}
]


async def main():
    """Main function to set up and run the bots."""
    bot_manager = BotManager()

    for config in BOT_CONFIGS:
        print(f"--- Setting up bot: {config['strategy_name']} on {config['symbol']} ---")

        # 1. Create the PortfolioManager
        portfolio_manager = PortfolioManager(
            strategy_id=config["strategy_name"],
            initial_equity=config["initial_equity"]
        )

        # 2. Create the Strategy
        strategy = SmaCrossoverStrategy(strategy_name=config["strategy_name"])
        strategy.parameters.update(config["strategy_params"])

        # 3. Create the MarketDataProvider and ExecutionEngine based on the mode
        mode = config.get("mode", "paper")
        
        if mode == "simulated":
            # --- SIMULATED MODE ---
            # Uses a mock data provider and a simulated execution engine.
            # Good for testing strategy logic without network requests.
            print("Mode: SIMULATED")
            market_data_provider = MockProvider()
            execution_config = ExecutionConfig() # Default config is fine for mock
            execution_engine = SimulatedExecutionEngine(execution_config, portfolio_manager, RISK_RULES)

        elif mode == "paper":
            # --- PAPER TRADING MODE ---
            # Uses a live data provider (Binance) but a simulated execution engine.
            # Good for testing how a strategy performs with real market data without risking real money.
            print("Mode: PAPER TRADING")
            market_data_config = MarketDataConfig(testnet=True) # Use Binance testnet
            market_data_provider = BinanceRESTProvider(market_data_config)
            execution_config = ExecutionConfig() # Slippage, fees, etc.
            execution_engine = SimulatedExecutionEngine(execution_config, portfolio_manager, RISK_RULES)
        
        elif mode == "live":
            # --- LIVE TRADING MODE ---
            # This would use a live execution engine that places real orders.
            # The implementation of LiveExecutionEngine is not in scope for this example.
            print("Mode: LIVE TRADING (not implemented)")
            # market_data_provider = BinanceRESTProvider(MarketDataConfig(testnet=False))
            # execution_engine = LiveExecutionEngine(api_key, api_secret, ...)
            continue # Skip for now

        else:
            print(f"Unknown mode: {mode}")
            continue

        # 4. Create the StrategyRunner
        runner = StrategyRunner(
            strategy=strategy,
            market_data_provider=market_data_provider,
            execution_engine=execution_engine,
            portfolio_manager=portfolio_manager,
            symbol=config["symbol"],
            timeframe=config["timeframe"]
        )

        # 5. Add the configured bot to the manager
        bot_manager.add_bot(runner)
        print("-----------------------------------------------------
")

    # Run all the bots concurrently
    try:
        await bot_manager.run_all()
    except KeyboardInterrupt:
        print("\nShutdown signal received. Stopping all bots...")
        await bot_manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main())
