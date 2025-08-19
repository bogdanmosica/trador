# Portfolio Risk Module

This module is responsible for managing the risk of a trading portfolio.

## Overview

The Portfolio Risk module provides a framework for defining and evaluating risk rules for a trading portfolio. It includes a `RiskEngine` that can be configured with a set of rules to be checked before and after trades are executed. The module also includes a `PortfolioManager` that tracks the state of the portfolio and provides the necessary data for the `RiskEngine` to evaluate the rules.

## Core Components

- **Risk Engine**: The main engine for evaluating risk rules.
- **Portfolio Manager**: Manages the state of the portfolio.
- **Rules**: A set of modular risk rules that can be configured and used by the `RiskEngine`.
