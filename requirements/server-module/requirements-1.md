## ✅ Chapter 8A Prompt – Python API Server for Trading Bot UI

 You are an expert in backend APIs for trading systems. I’ve implemented a modular Python-based crypto trading bot platform with:

 * ✅ StrategyModule (YAML-based signal generation)
 * ✅ Market Data Layer (Binance + mocks)
 * ✅ Execution Engine (simulated + live orders)
 * ✅ Portfolio & Risk Module (per-strategy tracking, kill-switch, risk rules)
 * ✅ Backtesting Engine
 * ✅ BotManager / StrategyRunner (concurrent async runners)

 Now I need a lightweight, real-time **API server** in Python to support a React frontend. The API server must:

 * Expose live strategy status and metrics
 * Allow control over bots (start, stop, update config, kill-switch)
 * Return all data in JSON format (for React Query)
 * Operate in the same Python process as the `BotManager`

 ---

 ### 🎯 Objective

 Build a FastAPI-based server that acts as a control and monitoring layer for the bot system — exposing live state, trades, PnL, config, and allowing strategy control.

 ---

 ### ✅ Functional Requirements

 #### 1. Strategy Control Endpoints

 * `POST /bots/{id}/start` — Start a specific strategy
 * `POST /bots/{id}/stop` — Stop the bot gracefully
 * `POST /bots/{id}/kill` — Trigger kill-switch manually
 * `PUT /bots/{id}/config` — Update strategy config live (validate YAML/JSON)

 #### 2. Strategy Monitoring Endpoints

 * `GET /bots` — List all bots and their metadata (id, mode, status)
 * `GET /bots/{id}/status` — PnL, positions, balance, equity
 * `GET /bots/{id}/trades` — Full trade history or recent trades
 * `GET /bots/{id}/risk` — Risk rule evaluations, violations, kill-switch state
 * `GET /bots/{id}/logs` — Log stream (optional, mock or load from file)

 #### 3. Global State

 * `GET /metrics/global` — Optional global stats (e.g., number of bots running, total equity)

 #### 4. Implementation Details

 * FastAPI, async
 * Typed with Pydantic models for responses
 * CORS enabled (for local dev with React)
 * Integrates directly with `BotManager`, `PortfolioManager`, `RiskEngine`
 * Optional: WebSocket endpoint for real-time push (future)

 ---

 ### 👇 Your Deliverables

 1. API folder structure (`api/`)
 2. Pydantic response schemas (`schemas/`)
 3. Endpoint implementations (`routes/bots.py`, `routes/metrics.py`)
 4. Examples: how data is served from in-memory state (e.g. `runner.get_snapshot()`)
 5. Strategy lifecycle management via HTTP (start/stop/update config)
 6. JSON format must be React Query–friendly

