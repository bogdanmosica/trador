This is the component that **takes signals from your Strategy Module**, interprets them into **orders**, and **simulates or executes** them — depending on whether you're in backtest, paper, or live mode.

---

## ✅ Chapter 4 Prompt – Execution Engine (Simulation-Ready)

 You are an expert in algorithmic trading system design. I’m building a 24/7 crypto bot using Python. I've completed:

 * A Strategy Module that outputs trade signals
 * A Backtesting Engine (realistic, with market/limit orders)
 * A Market Data Layer (supports Binance, async, 1m OHLCV)

 Now I want your help designing an **Execution Engine** that handles:

 * Order generation and simulation (in backtest/paper mode)
 * Fill logic for market/limit orders
 * Integration with portfolio state
 * Future transition to live trading

 ---

 ### 🎯 Objective

 Build a modular, realistic **Execution Engine** that:

 * Accepts **signal objects** from strategies
 * Creates and simulates **market/limit orders**
 * Tracks **order status, partial fills, fees**
 * Updates the portfolio (PnL, positions)
 * Logs all order events and fills

 ---

 ### ✅ Functional Requirements

 #### 1. **Signal to Order Handling**

 * Accept signal intent from strategy (e.g., `"BUY 1 BTCUSDT @ market"`)
 * Convert to order object with:

   * symbol, side, quantity
   * type: market, limit
   * TIF: GTC, IOC, etc.
   * status: new, filled, partial, cancelled

 #### 2. **Execution Simulation Logic**

 * Market Order:

   * Fill immediately at next candle’s open/close
   * Slippage modeled (configurable % or absolute)
 * Limit Order:

   * Check if price crosses limit in candle (high/low vs limit price)
   * Partial fill if volume constraints added later
 * Fees:

   * Maker/taker configurable per symbol
   * Deducted from quote asset

 #### 3. **Portfolio & Position Integration**

 * Pass fills to `PortfolioManager` to:

   * Open/close/update positions
   * Update cash balance
   * Track realized/unrealized PnL
   * Apply leverage if enabled

 #### 4. **Order Tracking & Logs**

 * Maintain full list of:

   * Submitted orders
   * Fills (price, time, size)
   * Cancelled/rejected orders
 * Export to JSON/CSV

 #### 5. **Pluggable Modes**

 * Abstract base:

   * `ExecutionEngine`
 * Implement:

   * `SimulatedExecutionEngine` (for backtest/paper)
   * `LiveExecutionEngine` (future, using REST/WebSocket APIs)

 ---

 ### 🔧 Tech Constraints

 * Python 3.11+
 * Async or sync acceptable (depends on market data mode)
 * Data types:

   * Signal: structured dict or class (`symbol`, `side`, `price`, `qty`, `order_type`)
   * Order/Fills: stored objects or data classes
 * Should be compatible with:

   * Strategy module
   * Backtester loop
   * Real-time runner (paper/live)

 ---

 ### 👇 Your Deliverables

 1. Propose folder/module structure for the Execution Engine
 2. Design base class `ExecutionEngine` and implementation `SimulatedExecutionEngine`
 3. Define data models: `Signal`, `Order`, `Fill`, `OrderStatus`
 4. Show how order fills would be simulated using OHLCV candle data
 5. Describe integration points with Portfolio tracking
 6. (Optional) Sketch how a live execution engine would differ

Example of future Portfolio Manager:

```python
from models import Order

class PortfolioManager:
    def __init__(self, starting_cash=10000):
        self.cash = starting_cash
        self.positions = {}  # symbol -> qty
        self.trade_log = []

    def apply_fill(self, order: Order):
        qty = order.filled_qty
        symbol = order.signal.symbol
        side = order.signal.side
        cost = order.fill_price * qty + order.fee

        if side.name == "BUY":
            self.positions[symbol] = self.positions.get(symbol, 0) + qty
            self.cash -= cost
        else:  # SELL
            self.positions[symbol] = self.positions.get(symbol, 0) - qty
            self.cash += order.fill_price * qty - order.fee

        self.trade_log.append(order)
```
