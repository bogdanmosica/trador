# Bot Runner Module

This module is responsible for running and managing trading bots.

## Overview

The Bot Runner module provides the core infrastructure for executing trading strategies in real-time. It includes a `BotManager` for concurrently running multiple strategies and a `StrategyRunner` that orchestrates the event loop for a single strategy, connecting market data, strategy logic, and the execution engine.

## Core Components

- **Bot Manager**: Manages and runs multiple `StrategyRunner` instances concurrently.
- **Strategy Runner**: Orchestrates the real-time event loop for a single trading strategy.
