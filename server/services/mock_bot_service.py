# This file provides a mock service for bot-related operations.
from typing import List, Dict, Any
from server.api.schemas.bots import BotIdentifier, BotStatus, Trade, BotRisk, RiskEvaluation
from server.api.schemas.metrics import GlobalMetrics

class MockBotService:
    def __init__(self):
        self.mock_bots = {
            "bot_1": {
                "id": "bot_1",
                "mode": "live",
                "status": "running",
                "pnl": 150.75,
                "positions": [{"symbol": "BTC/USDT", "amount": 0.01, "entry_price": 30000}],
                "balance": 10000.0,
                "equity": 10150.75,
                "trades": [
                    {"timestamp": "2023-01-01T10:00:00Z", "symbol": "BTC/USDT", "side": "buy", "price": 30000, "quantity": 0.01},
                    {"timestamp": "2023-01-01T11:00:00Z", "symbol": "BTC/USDT", "side": "sell", "price": 30100, "quantity": 0.005},
                ],
                "risk": {
                    "evaluations": [
                        {"rule_name": "max_drawdown", "is_violated": False, "details": {"current_drawdown": 0.02}},
                        {"rule_name": "max_position_size", "is_violated": False, "details": {"current_size": 0.01}},
                    ],
                    "kill_switch_activated": False,
                },
                "logs": [
                    "[INFO] Bot bot_1 started.",
                    "[DEBUG] Executing trade for BTC/USDT."
                ]
            },
            "bot_2": {
                "id": "bot_2",
                "mode": "backtest",
                "status": "stopped",
                "pnl": -25.00,
                "positions": [],
                "balance": 5000.0,
                "equity": 4975.0,
                "trades": [],
                "risk": {
                    "evaluations": [],
                    "kill_switch_activated": False,
                },
                "logs": [
                    "[INFO] Bot bot_2 initialized."
                ]
            }
        }

    def start_bot(self, bot_id: str) -> bool:
        if bot_id in self.mock_bots:
            self.mock_bots[bot_id]["status"] = "running"
            self.mock_bots[bot_id]["logs"].append(f"[INFO] Bot {bot_id} started by API.")
            return True
        return False

    def stop_bot(self, bot_id: str) -> bool:
        if bot_id in self.mock_bots:
            self.mock_bots[bot_id]["status"] = "stopped"
            self.mock_bots[bot_id]["logs"].append(f"[INFO] Bot {bot_id} stopped by API.")
            return True
        return False

    def kill_bot(self, bot_id: str) -> bool:
        if bot_id in self.mock_bots:
            self.mock_bots[bot_id]["status"] = "killed"
            self.mock_bots[bot_id]["risk"]["kill_switch_activated"] = True
            self.mock_bots[bot_id]["logs"].append(f"[CRITICAL] Kill-switch activated for bot {bot_id} by API.")
            return True
        return False

    def update_bot_config(self, bot_id: str, config: Dict[str, Any]) -> bool:
        if bot_id in self.mock_bots:
            # In a real scenario, this would update the actual bot's config
            # For mock, we just acknowledge the update
            self.mock_bots[bot_id]["logs"].append(f"[INFO] Bot {bot_id} config updated by API: {config}")
            return True
        return False

    def list_bots(self) -> List[BotIdentifier]:
        return [
            BotIdentifier(id=bot_data["id"], mode=bot_data["mode"], status=bot_data["status"])
            for bot_data in self.mock_bots.values()
        ]

    def get_bot_status(self, bot_id: str) -> BotStatus | None:
        bot_data = self.mock_bots.get(bot_id)
        if bot_data:
            return BotStatus(
                pnl=bot_data["pnl"],
                positions=bot_data["positions"],
                balance=bot_data["balance"],
                equity=bot_data["equity"],
            )
        return None

    def get_bot_trades(self, bot_id: str) -> List[Trade] | None:
        bot_data = self.mock_bots.get(bot_id)
        if bot_data:
            return [
                Trade(**trade_data) for trade_data in bot_data["trades"]
            ]
        return None

    def get_bot_config(self, bot_id: str) -> Dict[str, Any] | None:
        """Get bot configuration."""
        bot_data = self.mock_bots.get(bot_id)
        if bot_data:
            return {
                "id": bot_id,
                "strategy": "SMA Crossover",
                "symbol": "BTCUSDT",
                "mode": "paper",
                "initial_balance": 10000.0,
                "parameters": {
                    "fast_period": 10,
                    "slow_period": 20,
                    "position_size": 0.1
                },
                "status": bot_data["status"]
            }
        return None

    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """Get list of available trading strategies."""
        return [
            {"value": "sma_crossover", "label": "SMA Crossover"},
            {"value": "ema_crossover", "label": "EMA Crossover"},
            {"value": "rsi_mean_reversion", "label": "RSI Mean Reversion"},
            {"value": "bollinger_bands", "label": "Bollinger Bands"},
            {"value": "macd_crossover", "label": "MACD Crossover"},
        ]
    
    def get_available_symbols(self) -> List[Dict[str, Any]]:
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

    def get_bot_risk(self, bot_id: str) -> BotRisk | None:
        bot_data = self.mock_bots.get(bot_id)
        if bot_data:
            return BotRisk(
                evaluations=[
                    RiskEvaluation(**eval_data) for eval_data in bot_data["risk"]["evaluations"]
                ],
                kill_switch_activated=bot_data["risk"]["kill_switch_activated"],
            )
        return None

    def get_bot_logs(self, bot_id: str) -> List[str] | None:
        bot_data = self.mock_bots.get(bot_id)
        if bot_data:
            return bot_data["logs"]
        return None

    def get_global_metrics(self) -> GlobalMetrics:
        bots_running = sum(1 for bot in self.mock_bots.values() if bot["status"] == "running")
        total_equity = sum(bot["equity"] for bot in self.mock_bots.values())
        total_pnl = sum(bot["pnl"] for bot in self.mock_bots.values())
        total_trades = sum(len(bot["trades"]) for bot in self.mock_bots.values())
        return GlobalMetrics(
            bots_running=bots_running, 
            total_equity=total_equity,
            total_pnl=total_pnl,
            total_trades=total_trades
        )
