# This file defines the Pydantic schemas for metrics-related API endpoints.
from pydantic import BaseModel

class GlobalMetrics(BaseModel):
    bots_running: int
    total_equity: float
    total_pnl: float
    total_trades: int
