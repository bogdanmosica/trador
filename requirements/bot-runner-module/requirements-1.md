## ✅ Updated Prompt – Real-Time Strategy Bot Runner (with embedded answers)

 You are an expert in designing real-time orchestrators for crypto trading bots. I’m building a 24/7 modular bot system in Python and have already implemented:

 * ✅ Strategy Module (YAML-configurable, generates signals)
 * ✅ Backtester (market/limit fills)
 * ✅ Market Data Layer (Binance OHLCV, async)
 * ✅ Execution Engine (paper/live/simulated)
 * ✅ Portfolio & Risk Engine (per-strategy, with kill-switch)

 I want to build a **`StrategyRunner` class** that acts as the real-time event loop. It should:

 * Run **multiple bots in parallel** (each with its own strategy, market feed, portfolio, execution engine, etc.)
 * Support **real-time simulation**, **paper trading**, and **live mode**
 * Use **async tasks** for concurrency (faster, lower latency than multiprocess for now)

 ---

 ### 🎯 Objective

 Design a `StrategyRunner` (and optionally a `BotManager`) that:

 * Receives market data (live or mock)
 * Passes data to Strategy → receives Signal
 * Validates Signal via RiskEngine
 * Sends safe signals to ExecutionEngine → receives Order/Fill
 * Applies fill to PortfolioManager
 * Emits/logs live state and reacts to kill-switch

 ---

 ### ✅ Functional Requirements

 #### 1. Strategy Loop

 * Async loop:

   * Wait for next candle or tick
   * Call `strategy.generate_signal(market_data)`
   * Check signal with `risk_engine.check_all()`
   * If OK: call `execution_engine.execute_signal(...)`
   * Update portfolio with `portfolio.apply_fill(...)`
   * Emit logs, update snapshot

 #### 2. Modes Supported

 * **Simulated (backtest-style)** — with mock data and fill model
 * **Paper trading** — real prices, no real order placement
 * **Live trading** — execution via exchange APIs (e.g. Binance)
 * Switching modes = swap injected `ExecutionEngine` and `MarketDataProvider`

 #### 3. Concurrency

 * Each strategy bot runs as its own **async task**
 * Optionally: wrap with `BotManager` to launch and monitor multiple runners

 #### 4. Kill-Switch Handling

 * Risk rules can trigger runner to:

   * Flatten all positions
   * Stop its loop
   * Log reason + notify

 ---

 ### 🔧 Tech Constraints

 * Python 3.11+
 * Uses `asyncio` tasks for concurrency
 * External components (strategy, market, execution, etc.) injected
 * No global state — each bot is isolated

 ---

 ### 👇 Your Deliverables

 1. Propose folder/module structure for `runner/`
 2. Implement `StrategyRunner` class with async loop logic
 3. Include basic `BotManager` to run multiple bots concurrently
 4. Show how to switch modes (simulated, paper, live) via component injection
 5. Include kill-switch logic and graceful shutdown behavior

---

This prompt now reflects everything we've discussed — including:

* Multi-bot support ✅
* Async over multiprocessing ✅
* Mode-switching (sim/paper/live) ✅
* Per-strategy tracking ✅

---

Would you like me to now generate the **simulated GPT response** with the full `StrategyRunner`, `BotManager`, and async trading loop implementation?
