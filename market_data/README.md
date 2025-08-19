# Market Data Layer

This module provides a unified interface for accessing cryptocurrency market data from various exchanges.

## Overview

The Market Data Layer supports both historical data fetching and live data streaming. It includes features like intelligent caching, data validation, and normalization to ensure high-quality data for trading strategies and backtesting.

## Core Components

- **Providers**: Pluggable modules for different exchanges (e.g., Binance, Mock).
- **Storage**: Manages caching and persistent storage of market data.
- **Streaming**: Handles real-time data feeds using WebSockets.
- **Utils**: Provides tools for data validation, normalization, and conversion.
