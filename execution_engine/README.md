# Execution Engine

This module handles order execution for both simulated and live trading environments.

## Overview

The Execution Engine processes trading signals, manages orders, and interacts with a portfolio manager to track positions and balances. It supports realistic market simulation, including slippage and fees.

## Core Components

- **Simulated Engine**: For backtesting and paper trading.
- **Live Engine**: Interface for real exchange integration.
- **Portfolio Manager**: Tracks positions, PnL, and risk.
- **Order Management**: Manages the lifecycle of orders.
- **Signal Processing**: Converts trading signals into executable orders.
