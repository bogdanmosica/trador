## ✅ Chapter 8B Prompt – React Web UI for Trading Bot Platform

 You are an expert in building operational dashboards for real-time trading systems. I’ve built a modular backend crypto bot system, and I’m now creating a modern, maintainable **frontend** to:

 * Monitor live strategies
 * View trades, PnL, positions, config
 * Trigger actions (start/stop bot, kill switch)

 ---

 ### 🎯 Objective

 Build a **React-based dashboard** using:

 * ✅ TanStack Router
 * ✅ React Query (for API)
 * ✅ Tailwind + shadcn/ui for styling
 * ✅ TypeScript-first
 * Focused only on features already implemented in the backend

 ---

 ### ✅ Functional Requirements

 #### 1. Page Structure & Routing (TanStack)

 * `/bots` → List of running strategies
 * `/bots/:id` → Overview (PnL, status, config, last signal, kill-switch)
 * `/bots/:id/trades` → Trade history table
 * `/bots/:id/risk` → Risk rule status, violations
 * `/bots/:id/logs` → (Optional) live log stream

 #### 2. Components

 * **BotCard**: Name, status, PnL, control buttons
 * **StrategyDetails**: Equity, risk violations, current config
 * **TradesTable**: Paginated history with filter
 * **RiskPanel**: Pass/fail per rule with visual flags
 * **BotControls**: Start/Stop/Update Config/Kill buttons

 #### 3. Data Layer (React Query)

 * Use declarative fetches:

   * `useBots()`, `useBotStatus(id)`, `useBotTrades(id)`, etc.
 * Cache bot state for quick navigation
 * Show loading/success/error states

 #### 4. Styling & UI Framework

 * Tailwind CSS + `shadcn/ui`
 * Minimal design, high usability
 * Focused on operator visibility

 #### 5. Dev Experience

 * Fully type-safe
 * Uses environment variable for API URL
 * Easily dockerized or hosted via static export

 ---

 ### 👇 Your Deliverables

 1. Folder structure: `src/app/` (TanStack router) + `src/components/`
 2. Fetch layer using React Query (`lib/api.ts`)
 3. Example pages: Bots list, Bot detail (status + controls), Trades
 4. TypeScript API client with zod or OpenAPI (optional)
 5. Minimal global layout + dark mode toggle (shadcn config)

---

## ✅ Summary of Architecture

```
React UI (TanStack, shadcn)
   ↕️ REST API (FastAPI)
      ↔️ BotManager / StrategyRunner
          ↔️ Strategy / MarketData / Execution / Portfolio / Risk
```

---

## 🧠 Optional Next Steps

Would you like me to:

1. Simulate the **FastAPI implementation** now (schemas, routes, examples)?
2. Simulate the **React UI layout** (folder structure, pages, hooks)?
3. Or write out both side by side?

Let me know where you want to start.
