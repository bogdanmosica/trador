"""
Integrated Bot Service

This service integrates with all the actual bot modules:
- bot_runner: For managing bot lifecycle
- execution_engine: For trade execution
- portfolio_risk: For risk management
- market_data: For data feeds
- strategy: For trading strategies
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import threading
from concurrent.futures import ThreadPoolExecutor

# Import bot modules (add system path for imports)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from bot_runner.bot_manager import BotManager
from bot_runner.strategy_runner import StrategyRunner
from strategy.strategies.sma_crossover import SmaCrossoverStrategy
from portfolio_risk.portfolio_manager import PortfolioManager
try:
    from execution_engine.engines.simulated import SimulatedExecutionEngine
except ImportError:
    # Fallback for missing simulated engine
    SimulatedExecutionEngine = None
from execution_engine.engines.base import ExecutionEngine
try:
    from market_data.providers.mock import MockProvider
    from market_data.providers.binance_rest import BinanceRESTProvider
    from execution_engine.models import ExecutionConfig
    from market_data.models import MarketDataConfig
except ImportError as e:
    # Handle missing dependencies gracefully
    MockProvider = None
    BinanceRESTProvider = None
    ExecutionConfig = None
    MarketDataConfig = None

# Import API schemas
from server.api.schemas.bots import BotIdentifier, BotStatus, Trade, BotRisk, RiskEvaluation
from server.api.schemas.metrics import GlobalMetrics


class IntegratedBotService:
    """
    Service that manages actual trading bots using the real bot modules.
    
    This service replaces the mock implementation and provides integration
    with the actual trading bot infrastructure.
    """
    
    def __init__(self):
        """Initialize the integrated bot service."""
        self.logger = logging.getLogger(__name__)
        
        # Bot management
        self.bot_manager = BotManager()
        self.active_bots: Dict[str, Dict[str, Any]] = {}
        self.bot_configs: Dict[str, Dict[str, Any]] = {}
        
        # Async event loop for bot operations
        self.loop = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize with some default bot configurations
        self._initialize_default_bots()
    
    def _initialize_default_bots(self):
        """Initialize some default bot configurations."""
        self.bot_configs = {
            "sma_bot_btc": {
                "id": "sma_bot_btc",
                "strategy_name": "sma_crossover_conservative",
                "strategy_class": SmaCrossoverStrategy,
                "strategy_params": {"fast_period": 20, "slow_period": 50, "position_size": 0.5},
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "initial_equity": 10000,
                "mode": "paper",
                "status": "stopped"
            },
            "sma_bot_eth": {
                "id": "sma_bot_eth",
                "strategy_name": "sma_crossover_aggressive", 
                "strategy_class": SmaCrossoverStrategy,
                "strategy_params": {"fast_period": 9, "slow_period": 21, "position_size": 0.7},
                "symbol": "ETHUSDT",
                "timeframe": "15m",
                "initial_equity": 5000,
                "mode": "simulated",
                "status": "stopped"
            }
        }
    
    def _get_or_create_event_loop(self):
        """Get or create event loop for async operations."""
        if self.loop is None:
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        return self.loop
    
    async def _create_bot_components(self, config: Dict[str, Any]):
        """Create bot components based on configuration."""
        # 1. Create PortfolioManager
        portfolio_manager = PortfolioManager(
            strategy_id=config["id"],
            initial_equity=config["initial_equity"]
        )
        
        # 2. Create Strategy
        strategy_class = config["strategy_class"]
        strategy = strategy_class(strategy_name=config["strategy_name"])
        strategy.parameters.update(config["strategy_params"])
        
        # 3. Create MarketDataProvider and ExecutionEngine based on mode
        mode = config.get("mode", "paper")
        
        if mode == "simulated":
            market_data_provider = MockProvider()
            execution_config = ExecutionConfig()
            execution_engine = SimulatedExecutionEngine(execution_config, portfolio_manager, [])
        elif mode == "paper":
            market_data_config = MarketDataConfig(testnet=True)
            market_data_provider = BinanceRESTProvider(market_data_config)
            execution_config = ExecutionConfig()
            execution_engine = SimulatedExecutionEngine(execution_config, portfolio_manager, [])
        else:
            raise ValueError(f"Unsupported mode: {mode}")
        
        # 4. Create StrategyRunner
        runner = StrategyRunner(
            strategy=strategy,
            market_data_provider=market_data_provider,
            execution_engine=execution_engine,
            portfolio_manager=portfolio_manager,
            symbol=config["symbol"],
            timeframe=config["timeframe"]
        )
        
        return {
            "runner": runner,
            "portfolio_manager": portfolio_manager,
            "execution_engine": execution_engine,
            "strategy": strategy
        }
    
    def start_bot(self, bot_id: str) -> bool:
        """Start a trading bot."""
        try:
            if bot_id not in self.bot_configs:
                self.logger.error(f"Bot configuration not found: {bot_id}")
                return False
            
            if bot_id in self.active_bots:
                self.logger.warning(f"Bot {bot_id} is already running")
                return False
            
            config = self.bot_configs[bot_id].copy()
            
            # Create bot components asynchronously
            loop = self._get_or_create_event_loop()
            components = loop.run_until_complete(self._create_bot_components(config))
            
            # Store active bot info
            self.active_bots[bot_id] = {
                "config": config,
                "components": components,
                "start_time": datetime.now(timezone.utc),
                "status": "running"
            }
            
            # Update config status
            self.bot_configs[bot_id]["status"] = "running"
            
            # Add to bot manager and start
            self.bot_manager.add_bot(components["runner"])
            
            # Start the bot in background
            def run_bot():
                try:
                    loop.run_until_complete(components["runner"].run())
                except Exception as e:
                    self.logger.error(f"Error running bot {bot_id}: {e}")
                    self.active_bots[bot_id]["status"] = "error"
                    self.bot_configs[bot_id]["status"] = "error"
            
            self.executor.submit(run_bot)
            
            self.logger.info(f"Bot {bot_id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start bot {bot_id}: {e}")
            return False
    
    def stop_bot(self, bot_id: str) -> bool:
        """Stop a trading bot."""
        try:
            if bot_id not in self.active_bots:
                self.logger.warning(f"Bot {bot_id} is not running")
                return False
            
            bot_info = self.active_bots[bot_id]
            runner = bot_info["components"]["runner"]
            
            # Stop the bot
            loop = self._get_or_create_event_loop()
            loop.run_until_complete(runner.stop())
            
            # Update status
            bot_info["status"] = "stopped"
            self.bot_configs[bot_id]["status"] = "stopped"
            
            # Remove from active bots
            del self.active_bots[bot_id]
            
            self.logger.info(f"Bot {bot_id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop bot {bot_id}: {e}")
            return False
    
    def kill_bot(self, bot_id: str) -> bool:
        """Kill a trading bot (emergency stop)."""
        try:
            if bot_id not in self.active_bots:
                self.logger.warning(f"Bot {bot_id} is not running")
                return False
            
            # Force stop the bot
            result = self.stop_bot(bot_id)
            
            if result:
                self.bot_configs[bot_id]["status"] = "killed"
                self.logger.warning(f"Bot {bot_id} killed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to kill bot {bot_id}: {e}")
            return False
    
    def update_bot_config(self, bot_id: str, config: Dict[str, Any]) -> bool:
        """Update bot configuration."""
        try:
            if bot_id not in self.bot_configs:
                return False
            
            # Update configuration
            self.bot_configs[bot_id].update(config)
            
            # If bot is running, update strategy parameters
            if bot_id in self.active_bots:
                strategy = self.active_bots[bot_id]["components"]["strategy"]
                if "strategy_params" in config:
                    strategy.parameters.update(config["strategy_params"])
            
            self.logger.info(f"Bot {bot_id} configuration updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update bot {bot_id} config: {e}")
            return False
    
    def list_bots(self) -> List[BotIdentifier]:
        """List all available bots."""
        bots = []
        for bot_id, config in self.bot_configs.items():
            bots.append(BotIdentifier(
                id=bot_id,
                mode=config.get("mode", "simulated"),
                status=config.get("status", "stopped")
            ))
        return bots
    
    def get_bot_status(self, bot_id: str) -> Optional[BotStatus]:
        """Get detailed status of a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        config = self.bot_configs[bot_id]
        
        # Default values
        pnl = 0.0
        positions = []
        balance = config.get("initial_equity", 10000)
        equity = balance
        
        # Get real data if bot is active
        if bot_id in self.active_bots:
            try:
                portfolio_manager = self.active_bots[bot_id]["components"]["portfolio_manager"]
                
                # Get portfolio metrics
                metrics = portfolio_manager.get_performance_metrics()
                pnl = metrics.get("total_pnl", 0.0)
                balance = metrics.get("cash_balance", balance)
                equity = metrics.get("total_value", equity)
                
                # Get positions
                active_positions = portfolio_manager.active_positions
                for symbol, position in active_positions.items():
                    positions.append({
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "price": position.average_entry_price,
                        "side": "long" if position.is_long else "short"
                    })
                    
            except Exception as e:
                self.logger.error(f"Error getting bot status for {bot_id}: {e}")
        
        return BotStatus(
            pnl=pnl,
            positions=positions,
            balance=balance,
            equity=equity
        )
    
    def get_bot_trades(self, bot_id: str) -> Optional[List[Trade]]:
        """Get trade history for a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        trades = []
        
        # Get real trade data if bot is active
        if bot_id in self.active_bots:
            try:
                portfolio_manager = self.active_bots[bot_id]["components"]["portfolio_manager"]
                
                # Get trade history from portfolio manager
                for trade_record in portfolio_manager.state.trade_history:
                    trades.append(Trade(
                        timestamp=trade_record.entry_timestamp.isoformat(),
                        symbol=trade_record.symbol,
                        side="buy" if trade_record.side.value == "buy" else "sell",
                        price=trade_record.exit_price,
                        quantity=trade_record.quantity
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error getting bot trades for {bot_id}: {e}")
        
        return trades
    
    def get_bot_risk(self, bot_id: str) -> Optional[BotRisk]:
        """Get risk evaluation for a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        evaluations = []
        kill_switch_activated = False
        
        # Get real risk data if bot is active
        if bot_id in self.active_bots:
            try:
                portfolio_manager = self.active_bots[bot_id]["components"]["portfolio_manager"]
                
                # Get risk metrics
                risk_metrics = portfolio_manager.get_risk_metrics()
                performance_metrics = portfolio_manager.get_performance_metrics()
                
                # Create risk evaluations
                evaluations.append(RiskEvaluation(
                    rule_name="max_drawdown",
                    is_violated=performance_metrics.get("max_drawdown", 0) > 15.0,
                    details={
                        "current_drawdown": performance_metrics.get("max_drawdown", 0),
                        "threshold": 15.0
                    }
                ))
                
                evaluations.append(RiskEvaluation(
                    rule_name="position_concentration",
                    is_violated=risk_metrics.get("largest_position_percent", 0) > 50.0,
                    details={
                        "largest_position_percent": risk_metrics.get("largest_position_percent", 0),
                        "threshold": 50.0
                    }
                ))
                
                # Check if kill switch should be activated
                kill_switch_activated = any(eval.is_violated for eval in evaluations)
                
            except Exception as e:
                self.logger.error(f"Error getting bot risk for {bot_id}: {e}")
        
        return BotRisk(
            evaluations=evaluations,
            kill_switch_activated=kill_switch_activated
        )
    
    def get_bot_logs(self, bot_id: str) -> Optional[List[str]]:
        """Get recent logs for a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        # For now, return some placeholder logs
        # In a real implementation, you would capture and store bot logs
        logs = [
            f"[INFO] Bot {bot_id} initialized",
            f"[INFO] Strategy: {self.bot_configs[bot_id].get('strategy_name', 'unknown')}"
        ]
        
        if bot_id in self.active_bots:
            start_time = self.active_bots[bot_id]["start_time"]
            logs.append(f"[INFO] Bot {bot_id} started at {start_time.isoformat()}")
            logs.append(f"[DEBUG] Bot {bot_id} is running normally")
        else:
            logs.append(f"[INFO] Bot {bot_id} is currently stopped")
        
        return logs
    
    def get_global_metrics(self) -> GlobalMetrics:
        """Get global metrics across all bots."""
        bots_running = len([b for b in self.bot_configs.values() if b.get("status") == "running"])
        
        total_equity = 0.0
        total_pnl = 0.0
        total_trades = 0
        
        # Sum up metrics from active bots
        for bot_id in self.active_bots:
            try:
                portfolio_manager = self.active_bots[bot_id]["components"]["portfolio_manager"]
                metrics = portfolio_manager.get_performance_metrics()
                
                total_equity += metrics.get("total_value", 0)
                total_pnl += metrics.get("total_pnl", 0)
                total_trades += metrics.get("total_trades", 0)
                
            except Exception as e:
                self.logger.error(f"Error getting metrics for bot {bot_id}: {e}")
        
        # Add initial equity from stopped bots
        for bot_id, config in self.bot_configs.items():
            if bot_id not in self.active_bots:
                total_equity += config.get("initial_equity", 0)
        
        return GlobalMetrics(
            bots_running=bots_running,
            total_equity=total_equity,
            total_pnl=total_pnl,
            total_trades=total_trades
        )