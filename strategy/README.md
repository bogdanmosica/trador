# Strategy Module

This module contains the trading strategies and their configuration.

## Overview

The strategy module is responsible for generating trading signals based on market data and pre-defined logic. Strategies are designed to be pluggable and configurable, allowing for easy integration with the rest of the trading system.

## Core Components

- **Base Strategy**: An abstract base class that defines the common interface for all strategies.
- **Config Manager**: Manages the loading and saving of strategy configurations from YAML files.
- **Strategies**: Concrete implementations of trading strategies (e.g., SMA Crossover).
