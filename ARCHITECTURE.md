# Architecture Overview

This repository implements a trading bot platform with a FastAPI backend and a React (Vite + Tailwind + TypeScript) frontend. The backend serves the built UI for production while exposing REST endpoints for bot control, metrics, and strategy discovery.

## Components
- Server (`server/`):
  - `main.py`: FastAPI app, CORS, static serving of `ui/dist`, SPA catch-all.
  - `api/routes`: `bots`, `metrics`, `strategies` endpoints.
  - `api/schemas`: Pydantic models shared by routes/services.
  - `services`: Bot services selected via factory: Simple → Integrated → Mock.
- UI (`ui/`): React app built to `ui/dist/` and served by the backend at `/`.
- Trading Modules: `bot_runner/`, `strategy/`, `market_data/`, `execution_engine/`, `portfolio_risk/`, `backtest/` with their own READMEs.
- Scripts: `start_server.py` (all-in-one), `run_bots.py` (demo), `run_tests.py` (strategy tests).

## Startup
- All-in-one: `python start_server.py`
  - Builds `ui/` if needed, then runs `uvicorn server.main:app` on port 8000.
  - Serves UI at `/`, API under `/api/*`, docs at `/docs`.
- Dev split:
  - Backend: `uvicorn server.main:app --reload --port 8000`
  - Frontend: `cd ui && pnpm run dev` (use `VITE_API_BASE_URL` if non-default).

## Request Flow (Examples)
- `GET /api/bots` → `server/api/routes/bots.py` → `get_bot_service().list_bots()`.
- `POST /api/bots/{id}/start|stop|kill` → corresponding service method.
- `GET /api/bots/{id}/status|trades|risk|logs` → service data for the bot.
- `GET /api/metrics/global` → aggregates from service.
- Strategies:
  - `GET /api/strategies` → `StrategyDiscoveryService.discover_strategies()`.
  - `GET /api/configurations` → scan `strategy/configs/*.json`.
  - `POST /api/strategies/{name}/validate` → validate via strategy instance.

## Service Selection
`server/services/bot_service_factory.get_bot_service()` chooses:
1) `SimpleBotService` (default realistic simulation),
2) `IntegratedBotService` (real modules),
3) `MockBotService` (fallback), depending on available imports.

