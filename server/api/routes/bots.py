# This file defines the API routes for bot control and monitoring.
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from server.api.schemas.bots import BotIdentifier, BotStatus, Trade, RiskEvaluation, BotRisk, CreateBotRequest
from server.services.bot_service_factory import get_bot_service

router = APIRouter()

# Get the bot service instance
bot_service = get_bot_service()

@router.post("/bots/{bot_id}/start", response_model=Dict[str, str])
async def start_bot(bot_id: str):
    """
    Starts a specific trading bot.
    """
    if bot_service.start_bot(bot_id):
        return {"message": f"Bot {bot_id} started successfully."}
    raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found or could not be started.")

@router.post("/bots/{bot_id}/stop", response_model=Dict[str, str])
async def stop_bot(bot_id: str):
    """
    Stops a specific trading bot gracefully.
    """
    if bot_service.stop_bot(bot_id):
        return {"message": f"Bot {bot_id} stopped successfully."}
    raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found or could not be stopped.")

@router.post("/bots/{bot_id}/kill", response_model=Dict[str, str])
async def kill_bot(bot_id: str):
    """
    Triggers the kill-switch for a specific trading bot manually.
    """
    if bot_service.kill_bot(bot_id):
        return {"message": f"Kill-switch activated for bot {bot_id}."}
    raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found or kill-switch could not be activated.")

@router.get("/bots/{bot_id}/config", response_model=Dict[str, Any])
async def get_bot_config(bot_id: str):
    """
    Retrieves the configuration of a specific trading bot.
    """
    config = bot_service.get_bot_config(bot_id)
    if config is not None:
        return config
    raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found.")

@router.put("/bots/{bot_id}/config", response_model=Dict[str, str])
async def update_bot_config(bot_id: str, config: Dict[str, Any]):
    """
    Updates the configuration of a specific trading bot live.
    """
    if bot_service.update_bot_config(bot_id, config):
        return {"message": f"Config for bot {bot_id} updated successfully."}
    raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found or config could not be updated.")

@router.post("/bots", response_model=Dict[str, str])
async def create_bot(bot_request: CreateBotRequest):
    """
    Creates a new trading bot with the specified configuration.
    """
    if bot_service.create_bot(bot_request.model_dump()):
        return {"message": f"Bot {bot_request.id} created successfully."}
    raise HTTPException(status_code=400, detail=f"Bot {bot_request.id} could not be created or already exists.")

@router.get("/bots", response_model=List[BotIdentifier])
async def list_bots():
    """
    Lists all trading bots and their metadata.
    """
    return bot_service.list_bots()

@router.get("/bots/{bot_id}/status", response_model=BotStatus)
async def get_bot_status(bot_id: str):
    """
    Retrieves the PnL, positions, balance, and equity for a specific bot.
    """
    status = bot_service.get_bot_status(bot_id)
    if status:
        return status
    raise HTTPException(status_code=404, detail=f"Status for bot {bot_id} not found.")

@router.get("/bots/{bot_id}/trades", response_model=List[Trade])
async def get_bot_trades(bot_id: str):
    """
    Retrieves the full trade history or recent trades for a specific bot.
    """
    trades = bot_service.get_bot_trades(bot_id)
    if trades is not None:
        return trades
    raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found.")

@router.get("/bots/{bot_id}/risk", response_model=BotRisk)
async def get_bot_risk(bot_id: str):
    """
    Retrieves risk rule evaluations, violations, and kill-switch state for a specific bot.
    """
    risk = bot_service.get_bot_risk(bot_id)
    if risk:
        return risk
    raise HTTPException(status_code=404, detail=f"Risk data for bot {bot_id} not found.")

@router.get("/bots/{bot_id}/logs", response_model=List[str])
async def get_bot_logs(bot_id: str):
    """
    Retrieves log stream for a specific bot (mock or load from file).
    """
    logs = bot_service.get_bot_logs(bot_id)
    if logs:
        return logs
    raise HTTPException(status_code=404, detail=f"Logs for bot {bot_id} not found.")

@router.get("/available-strategies", response_model=List[Dict[str, str]])
async def get_available_strategies():
    """
    Retrieves list of available trading strategies.
    """
    strategies = bot_service.get_available_strategies()
    return strategies

@router.get("/available-symbols", response_model=List[Dict[str, str]])
async def get_available_symbols():
    """
    Retrieves list of available trading symbols/pairs.
    """
    symbols = bot_service.get_available_symbols()
    return symbols
