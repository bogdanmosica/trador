# This file defines the Pydantic schemas for bot-related API endpoints.
from pydantic import BaseModel
from typing import List, Dict, Any

class BotIdentifier(BaseModel):
    id: str
    mode: str
    status: str

class BotStatus(BaseModel):
    pnl: float
    positions: List[Dict[str, Any]]
    balance: float
    equity: float

class Trade(BaseModel):
    timestamp: str
    symbol: str
    side: str
    price: float
    quantity: float
    type: str = "unknown"  # "open", "close", or "unknown"
    pnl: float = 0.0  # P&L for closing trades

class RiskEvaluation(BaseModel):
    rule_name: str
    is_violated: bool
    details: Dict[str, Any]

class BotRisk(BaseModel):
    evaluations: List[RiskEvaluation]
    kill_switch_activated: bool

class CreateBotRequest(BaseModel):
    id: str
    strategy: str = "SMA Crossover"
    symbol: str = "BTCUSDT" 
    mode: str = "paper"  # "paper", "simulated", "live"
    initial_balance: float = 10000.0
    parameters: Dict[str, Any] = {
        "fast_period": 20,
        "slow_period": 50,
        "position_size": 0.5
    }
