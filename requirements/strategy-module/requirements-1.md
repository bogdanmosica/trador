You are an expert in algorithmic trading systems and Python architecture. I’m building a modular crypto trading bot that will eventually run 24/7 and support multiple users. I want your help **designing the Strategy Module** — the first core component of the system.

### 🧠 Objective:

Build a pluggable, configurable **Strategy Module** that outputs trade signals based on defined logic and market data. This logic will later feed into separate components for backtesting, execution, and monitoring.

---

### ✅ Requirements:

#### 1. **Strategy Class Design**

* Each strategy should be implemented as a Python class with a common interface, e.g.:

  * `.generate_signals(market_data, current_position, strategy_params)`
  * `.update_parameters(preset_name)`
* Strategies should be stateless and side-effect-free (they should *not* execute orders).

#### 2. **Parameter Configuration**

* Parameters should be stored in **templated YAML or JSON configs**, e.g.:

  ```yaml
  name: sma_crossover_live_v2
  base_strategy: sma_crossover
  params:
    fast_period: 9
    slow_period: 21
    symbol: BTCUSDT
    time_frame: 1h
  metadata:
    status: live
    created_at: 2025-08-15
    notes: "Live-tested on BTC, medium volatility regime"
  ```
* Strategies should load parameter presets dynamically from a directory or DB.

#### 3. **Versioning (Named Presets)**

* Support basic versioning with:

  * Named presets (`draft_v1`, `backtest_v2`, `live_v3`)
  * Associated metadata (status, date, changelog note)
* No Git-style diffs or branching needed (for now).

#### 4. **Initial Strategy to Implement**

* Recommend a simple but realistic **starter strategy** from this list:

  * SMA/EMA crossover
  * RSI-based mean reversion
  * Bollinger Band breakout
  * Any other effective but easy-to-test strategy
* Use this strategy as a reference implementation for the class interface + config structure.

---

### 🔧 Tech Notes:

* Python 3.11+
* No external libraries unless justified (standard libs preferred for now)
* The strategy module will eventually connect to:

  * Data layer (candles, indicators, OHLCV)
  * Execution engine (via queue or API)
  * Web UI (for param config and version control)
* Emphasis on **clean code**, **testability**, and **future extensibility**