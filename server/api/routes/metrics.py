# This file defines the API routes for global metrics.
from fastapi import APIRouter
from server.api.schemas.metrics import GlobalMetrics
from server.services.bot_service_factory import get_bot_service

router = APIRouter()

bot_service = get_bot_service()

@router.get("/metrics/global", response_model=GlobalMetrics)
async def get_global_metrics():
    """
    Retrieves optional global statistics (e.g., number of bots running, total equity).
    """
    return bot_service.get_global_metrics()
