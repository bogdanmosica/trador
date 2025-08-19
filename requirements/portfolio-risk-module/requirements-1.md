## ✅ Updated Prompt – **Portfolio & Risk Engine** (with Embedded Clarifications)

 You are an expert in portfolio accounting and risk management for algorithmic trading. I’m building a 24/7 crypto bot in Python and have completed:

 * A modular **Strategy Module** (with YAML-configurable classes)
 * A realistic **Backtester**
 * A **Market Data Layer** (Binance support, async)
 * An **Execution Engine** (market/limit orders, fill simulation)

 Now I want your help designing the **Portfolio & Risk Engine**, which will:

 * Track per-strategy portfolio state (balances, PnL, leverage, open positions)
 * Handle margin/futures trading from day one (not just spot)
 * Enforce **per-strategy** risk rules like max drawdown or position size

 ---

 ### 🎯 Objective

 Build a `PortfolioManager` + `RiskEngine` for **per-strategy tracking** that:

 * Responds to order fills from the Execution Engine
 * Calculates realized/unrealized PnL, account equity, and exposure
 * Checks risk constraints and rejects trades that exceed limits
 * Supports margin and leverage logic
 * Can trigger a kill-switch or flatten positions under risky conditions

 ---

 ### ✅ Functional Requirements

 #### 1. **Portfolio Tracking**

 * Track balances per base asset (e.g., USDT)
 * Support **margin/futures positions**, including leverage
 * Track:

   * Open positions (symbol, side, entry price, qty, leverage)
   * Trade history (entry/exit, PnL, fee)
   * Equity over time (snapshots)
   * Realized/unrealized PnL

 #### 2. **Risk Management Rules**

 * Apply risk rules **per strategy**
 * Rules include:

   * Max position size (USD)
   * Max drawdown (% of equity)
   * Daily loss limit
   * Max leverage
   * Max open positions
   * Kill-switch logic
 * All rules should be defined in a **modular, pluggable format**

 #### 3. **Execution Integration**

 * The Execution Engine calls `PortfolioManager.apply_fill()` when an order is filled
 * Before executing, the bot should ask `RiskEngine.check_all()`
 * If any risk rule fails, the trade should be rejected
 * Optional: include a method to trigger kill-switch and flatten positions

 #### 4. **Reporting**

 * Export:

   * Trade logs (CSV/JSON)
   * Equity curve data
   * Risk violations log
 * Optionally produce snapshots for live dashboards

 ---

 ### 🔧 Technical Constraints

 * Python 3.11+
 * Must support async execution loops
 * One `PortfolioManager` per strategy
 * Risk rules defined **per strategy**, based on its config
 * Mark prices come from live or historical candles

 ---

 ### 👇 Your Deliverables

 1. Propose a clean folder/module structure for the Portfolio & Risk Engine
 2. Design class: `PortfolioManager` for per-strategy tracking
 3. Design class: `RiskEngine` to check rules pre-trade and post-trade
 4. Include a few example risk rules (e.g. max drawdown, max position size)
 5. Show how the risk engine integrates into the trading execution loop
 6. (Optional) Add kill-switch logic to flatten and disable a strategy under critical risk events
