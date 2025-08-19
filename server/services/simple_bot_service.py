"""
Simple Bot Service

A simplified bot service that provides real bot management functionality
without requiring the complex module dependencies.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import threading
import random
import time

# Import API schemas
from server.api.schemas.bots import BotIdentifier, BotStatus, Trade, BotRisk, RiskEvaluation
from server.api.schemas.metrics import GlobalMetrics


class SimpleBotService:
    """
    A simplified bot service that provides real functionality
    without complex dependencies.
    
    This service manages bot state, executes basic trading logic,
    and provides realistic data for the frontend.
    """
    
    def __init__(self):
        """Initialize the simple bot service."""
        self.logger = logging.getLogger(__name__)
        
        # Bot configurations and state
        self.bot_configs = {
            "sma_bot_btc": {
                "id": "sma_bot_btc",
                "strategy": "SMA Crossover",
                "symbol": "BTCUSDT",
                "mode": "paper",
                "status": "stopped",
                "initial_balance": 10000.0,
                "current_balance": 10000.0,
                "equity": 10000.0,
                "pnl": 0.0,
                "positions": [],
                "trades": [],
                "created_at": datetime.now(timezone.utc),
                "parameters": {
                    "fast_period": 20,
                    "slow_period": 50,
                    "position_size": 0.5
                }
            },
            "sma_bot_eth": {
                "id": "sma_bot_eth",
                "strategy": "SMA Crossover Aggressive",
                "symbol": "ETHUSDT", 
                "mode": "simulated",
                "status": "stopped",
                "initial_balance": 5000.0,
                "current_balance": 5000.0,
                "equity": 5000.0,
                "pnl": 0.0,
                "positions": [],
                "trades": [],
                "created_at": datetime.now(timezone.utc),
                "parameters": {
                    "fast_period": 9,
                    "slow_period": 21,
                    "position_size": 0.7
                }
            }
        }
        
        # Running bots (bot_id -> thread info)
        self.running_bots = {}
        
        # Simulation parameters
        self.price_data = {
            "BTCUSDT": 45000.0,
            "ETHUSDT": 3000.0
        }
    
    def _simulate_trading(self, bot_id: str):
        """Simulate trading activity for a bot."""
        config = self.bot_configs[bot_id]
        symbol = config["symbol"]
        
        self.logger.info(f"Starting trading simulation for bot {bot_id}")
        
        while config["status"] == "running":
            try:
                # Simulate price movement
                current_price = self.price_data[symbol]
                price_change = random.uniform(-0.02, 0.02)  # ±2% price movement
                new_price = current_price * (1 + price_change)
                self.price_data[symbol] = new_price
                
                # Simulate trading decisions (simplified)
                if random.random() < 0.1:  # 10% chance of trade
                    self._execute_simulated_trade(bot_id, new_price)
                
                # Update positions P&L
                self._update_positions_pnl(bot_id, new_price)
                
                # Check risk rules and enforce kill switch
                self._check_and_enforce_risk_rules(bot_id)
                
                # Sleep before next iteration
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in trading simulation for {bot_id}: {e}")
                break
        
        self.logger.info(f"Trading simulation stopped for bot {bot_id}")
    
    def _execute_simulated_trade(self, bot_id: str, price: float):
        """Execute a simulated trade."""
        config = self.bot_configs[bot_id]
        symbol = config["symbol"]
        
        # Determine trade type based on current position
        current_positions = config["positions"]
        has_position = len(current_positions) > 0
        
        if not has_position and random.random() < 0.7:  # 70% chance to open position
            # Open position
            side = "buy" if random.random() < 0.6 else "sell"  # 60% bias toward long
            position_size = config["parameters"]["position_size"]
            quantity = (config["current_balance"] * position_size) / price
            
            # Create position
            position = {
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "side": "long" if side == "buy" else "short",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            config["positions"].append(position)
            
            # Create trade record
            trade = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "side": side,
                "price": price,
                "quantity": quantity,
                "type": "open"
            }
            config["trades"].append(trade)
            
            # Update balance (simplified)
            cost = quantity * price
            config["current_balance"] -= cost if side == "buy" else -cost
            
            self.logger.info(f"Bot {bot_id}: Opened {side} position for {symbol} at {price}")
        
        elif has_position and random.random() < 0.3:  # 30% chance to close position
            # Close position
            position = current_positions[0]  # Close first position
            close_side = "sell" if position["side"] == "long" else "buy"
            
            # Calculate P&L
            entry_price = position["price"]
            quantity = position["quantity"]
            
            if position["side"] == "long":
                pnl = (price - entry_price) * quantity
            else:
                pnl = (entry_price - price) * quantity
            
            # Update P&L and balance
            config["pnl"] += pnl
            config["current_balance"] += quantity * price if close_side == "sell" else -quantity * price
            
            # Create trade record
            trade = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "side": close_side,
                "price": price,
                "quantity": quantity,
                "type": "close",
                "pnl": pnl
            }
            config["trades"].append(trade)
            
            # Remove position
            config["positions"].remove(position)
            
            self.logger.info(f"Bot {bot_id}: Closed position for {symbol} at {price}, P&L: {pnl:.2f}")
    
    def _update_positions_pnl(self, bot_id: str, current_price: float):
        """Update unrealized P&L for open positions."""
        config = self.bot_configs[bot_id]
        
        total_unrealized_pnl = 0.0
        for position in config["positions"]:
            entry_price = position["price"]
            quantity = position["quantity"]
            
            if position["side"] == "long":
                unrealized_pnl = (current_price - entry_price) * quantity
            else:
                unrealized_pnl = (entry_price - current_price) * quantity
            
            total_unrealized_pnl += unrealized_pnl
        
        # Update equity
        config["equity"] = config["current_balance"] + total_unrealized_pnl
    
    def _check_and_enforce_risk_rules(self, bot_id: str):
        """Check risk rules and automatically stop bot if kill switch should be activated."""
        config = self.bot_configs[bot_id]
        
        # Get current risk evaluation
        risk_evaluation = self.get_bot_risk(bot_id)
        if not risk_evaluation:
            return
        
        # Check if kill switch should be activated
        if risk_evaluation.kill_switch_activated:
            # Automatically stop the bot due to risk violation
            self.logger.warning(f"RISK VIOLATION: Kill switch activated for bot {bot_id}")
            self.logger.warning(f"Automatically stopping bot {bot_id} due to risk rules violation")
            
            # Close all open positions immediately (emergency exit)
            self._emergency_close_all_positions(bot_id)
            
            # Stop the bot
            config["status"] = "killed"
            
            # Remove from running bots
            if bot_id in self.running_bots:
                del self.running_bots[bot_id]
            
            # Log the risk details
            for evaluation in risk_evaluation.evaluations:
                if evaluation.is_violated:
                    self.logger.error(f"Risk rule violated - {evaluation.rule_name}: {evaluation.details}")
    
    def _emergency_close_all_positions(self, bot_id: str):
        """Emergency close all positions when kill switch is activated."""
        config = self.bot_configs[bot_id]
        symbol = config["symbol"]
        current_price = self.price_data[symbol]
        
        # Close all open positions at current market price
        positions_to_close = config["positions"].copy()
        for position in positions_to_close:
            # Determine close side
            close_side = "sell" if position["side"] == "long" else "buy"
            quantity = position["quantity"]
            
            # Calculate P&L for the emergency close
            entry_price = position["price"]
            if position["side"] == "long":
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity
            
            # Update P&L and balance
            config["pnl"] += pnl
            config["current_balance"] += quantity * current_price if close_side == "sell" else -quantity * current_price
            
            # Create emergency close trade record
            trade = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "side": close_side,
                "price": current_price,
                "quantity": quantity,
                "type": "close",
                "pnl": pnl,
                "emergency_close": True  # Mark as emergency close
            }
            config["trades"].append(trade)
            
            self.logger.warning(f"Emergency close: {close_side} {quantity:.4f} {symbol} at {current_price:.2f}, P&L: {pnl:.2f}")
        
        # Clear all positions
        config["positions"].clear()
        
        # Update equity
        config["equity"] = config["current_balance"]
    
    def create_bot(self, bot_config: dict) -> bool:
        """Create a new trading bot with the specified configuration."""
        bot_id = bot_config["id"]
        
        # Check if bot already exists
        if bot_id in self.bot_configs:
            self.logger.warning(f"Bot {bot_id} already exists")
            return False
        
        # Validate required fields
        required_fields = ["id", "strategy", "symbol", "mode", "initial_balance"]
        for field in required_fields:
            if field not in bot_config:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Create bot configuration
        self.bot_configs[bot_id] = {
            "id": bot_id,
            "strategy": bot_config["strategy"],
            "symbol": bot_config["symbol"],
            "mode": bot_config["mode"],
            "status": "stopped",
            "initial_balance": bot_config["initial_balance"],
            "current_balance": bot_config["initial_balance"],
            "equity": bot_config["initial_balance"],
            "pnl": 0.0,
            "positions": [],
            "trades": [],
            "created_at": datetime.now(timezone.utc),
            "parameters": bot_config.get("parameters", {
                "fast_period": 20,
                "slow_period": 50,
                "position_size": 0.5
            })
        }
        
        # Initialize price data for new symbol if not exists
        if bot_config["symbol"] not in self.price_data:
            # Set initial price based on symbol
            if "BTC" in bot_config["symbol"]:
                self.price_data[bot_config["symbol"]] = 45000.0
            elif "ETH" in bot_config["symbol"]:
                self.price_data[bot_config["symbol"]] = 3000.0
            else:
                self.price_data[bot_config["symbol"]] = 100.0  # Default price
        
        self.logger.info(f"Bot {bot_id} created successfully with strategy {bot_config['strategy']}")
        return True
    
    def start_bot(self, bot_id: str) -> bool:
        """Start a trading bot."""
        if bot_id not in self.bot_configs:
            self.logger.error(f"Bot {bot_id} not found")
            return False
        
        if bot_id in self.running_bots:
            self.logger.warning(f"Bot {bot_id} is already running")
            return False
        
        # Update status
        self.bot_configs[bot_id]["status"] = "running"
        
        # Start simulation thread
        thread = threading.Thread(target=self._simulate_trading, args=(bot_id,))
        thread.daemon = True
        thread.start()
        
        self.running_bots[bot_id] = {
            "thread": thread,
            "start_time": datetime.now(timezone.utc)
        }
        
        self.logger.info(f"Bot {bot_id} started successfully")
        return True
    
    def stop_bot(self, bot_id: str) -> bool:
        """Stop a trading bot."""
        if bot_id not in self.bot_configs:
            return False
        
        # Update status (this will stop the simulation loop)
        self.bot_configs[bot_id]["status"] = "stopped"
        
        # Remove from running bots
        if bot_id in self.running_bots:
            del self.running_bots[bot_id]
        
        self.logger.info(f"Bot {bot_id} stopped successfully")
        return True
    
    def kill_bot(self, bot_id: str) -> bool:
        """Kill a trading bot (emergency stop)."""
        if bot_id not in self.bot_configs:
            return False
        
        # Force stop
        self.bot_configs[bot_id]["status"] = "killed"
        
        # Remove from running bots
        if bot_id in self.running_bots:
            del self.running_bots[bot_id]
        
        self.logger.warning(f"Bot {bot_id} killed")
        return True
    
    def update_bot_config(self, bot_id: str, config: Dict[str, Any]) -> bool:
        """Update bot configuration."""
        if bot_id not in self.bot_configs:
            return False
        
        # Update configuration
        if "parameters" in config:
            self.bot_configs[bot_id]["parameters"].update(config["parameters"])
        
        # Update other config fields
        for key, value in config.items():
            if key in ["mode", "initial_balance"]:
                self.bot_configs[bot_id][key] = value
        
        self.logger.info(f"Bot {bot_id} configuration updated")
        return True
    
    def get_bot_config(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get bot configuration."""
        if bot_id not in self.bot_configs:
            return None
        
        config = self.bot_configs[bot_id]
        # Return a copy of the config without sensitive data
        return {
            "id": bot_id,
            "strategy": config["strategy"],
            "symbol": config["symbol"],
            "mode": config["mode"],
            "initial_balance": config["initial_balance"],
            "parameters": config["parameters"].copy(),
            "status": config["status"]
        }
    
    def get_available_strategies(self) -> List[Dict[str, str]]:
        """Get list of available trading strategies."""
        return [
            {"value": "sma_crossover", "label": "SMA Crossover"},
            {"value": "ema_crossover", "label": "EMA Crossover"},
            {"value": "rsi_mean_reversion", "label": "RSI Mean Reversion"},
            {"value": "bollinger_bands", "label": "Bollinger Bands"},
            {"value": "macd_crossover", "label": "MACD Crossover"},
        ]
    
    def get_available_symbols(self) -> List[Dict[str, str]]:
        """Get list of available trading symbols/pairs."""
        return [
            {"value": "BTCUSDT", "label": "BTC/USDT"},
            {"value": "ETHUSDT", "label": "ETH/USDT"},
            {"value": "ADAUSDT", "label": "ADA/USDT"},
            {"value": "DOTUSDT", "label": "DOT/USDT"},
            {"value": "LINKUSDT", "label": "LINK/USDT"},
            {"value": "SOLUSDT", "label": "SOL/USDT"},
            {"value": "MATICUSDT", "label": "MATIC/USDT"},
            {"value": "AVAXUSDT", "label": "AVAX/USDT"},
            {"value": "UNIUSDT", "label": "UNI/USDT"},
            {"value": "AAVEUSDT", "label": "AAVE/USDT"},
        ]
    
    def list_bots(self) -> List[BotIdentifier]:
        """List all available bots."""
        return [
            BotIdentifier(
                id=bot_id,
                mode=config["mode"],
                status=config["status"]
            )
            for bot_id, config in self.bot_configs.items()
        ]
    
    def get_bot_status(self, bot_id: str) -> Optional[BotStatus]:
        """Get detailed status of a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        config = self.bot_configs[bot_id]
        
        # Convert positions to API format
        positions = []
        for pos in config["positions"]:
            positions.append({
                "symbol": pos["symbol"],
                "quantity": pos["quantity"],
                "price": pos["price"],
                "side": pos["side"]
            })
        
        return BotStatus(
            pnl=config["pnl"],
            positions=positions,
            balance=config["current_balance"],
            equity=config["equity"]
        )
    
    def get_bot_trades(self, bot_id: str) -> Optional[List[Trade]]:
        """Get trade history for a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        config = self.bot_configs[bot_id]
        
        return [
            Trade(
                timestamp=trade["timestamp"],
                symbol=trade["symbol"],
                side=trade["side"],
                price=trade["price"],
                quantity=trade["quantity"],
                type=trade.get("type", "unknown"),
                pnl=trade.get("pnl", 0.0)
            )
            for trade in config["trades"]
        ]
    
    def get_bot_risk(self, bot_id: str) -> Optional[BotRisk]:
        """Get risk evaluation for a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        config = self.bot_configs[bot_id]
        
        # Calculate risk metrics
        max_drawdown_pct = abs(min(0, config["pnl"] / config["initial_balance"] * 100))
        position_concentration = len(config["positions"]) / 5.0 * 100  # Assume max 5 positions
        
        evaluations = [
            RiskEvaluation(
                rule_name="max_drawdown",
                is_violated=max_drawdown_pct > 10.0,
                details={
                    "current_drawdown_pct": max_drawdown_pct,
                    "threshold_pct": 10.0
                }
            ),
            RiskEvaluation(
                rule_name="position_concentration",
                is_violated=position_concentration > 50.0,
                details={
                    "concentration_pct": position_concentration,
                    "threshold_pct": 50.0
                }
            )
        ]
        
        kill_switch_activated = any(eval.is_violated for eval in evaluations)
        
        return BotRisk(
            evaluations=evaluations,
            kill_switch_activated=kill_switch_activated
        )
    
    def get_bot_logs(self, bot_id: str) -> Optional[List[str]]:
        """Get recent logs for a specific bot."""
        if bot_id not in self.bot_configs:
            return None
        
        config = self.bot_configs[bot_id]
        
        logs = [
            f"[INFO] Bot {bot_id} initialized with strategy: {config['strategy']}",
            f"[INFO] Trading symbol: {config['symbol']}",
            f"[INFO] Mode: {config['mode']}",
            f"[INFO] Initial balance: ${config['initial_balance']:,.2f}"
        ]
        
        if config["status"] == "running":
            logs.extend([
                f"[INFO] Bot {bot_id} is currently running",
                f"[DEBUG] Current equity: ${config['equity']:,.2f}",
                f"[DEBUG] P&L: ${config['pnl']:,.2f}",
                f"[DEBUG] Open positions: {len(config['positions'])}"
            ])
        else:
            logs.append(f"[INFO] Bot {bot_id} is currently {config['status']}")
        
        # Add recent trade logs
        recent_trades = config["trades"][-5:]  # Last 5 trades
        for trade in recent_trades:
            logs.append(f"[TRADE] {trade['side']} {trade['quantity']:.4f} {trade['symbol']} at {trade['price']:.2f}")
        
        return logs
    
    def get_global_metrics(self) -> GlobalMetrics:
        """Get global metrics across all bots."""
        bots_running = sum(1 for config in self.bot_configs.values() if config["status"] == "running")
        
        total_equity = sum(config["equity"] for config in self.bot_configs.values())
        total_pnl = sum(config["pnl"] for config in self.bot_configs.values())
        total_trades = sum(len(config["trades"]) for config in self.bot_configs.values())
        
        return GlobalMetrics(
            bots_running=bots_running,
            total_equity=total_equity,
            total_pnl=total_pnl,
            total_trades=total_trades
        )