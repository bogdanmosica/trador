# Server Module

This module contains a FastAPI-based API server to provide a control and monitoring layer for the trading bot system.

## Features

- Exposes endpoints to control and monitor trading bots.
- Provides real-time strategy status and metrics.
- Allows starting, stopping, and updating bot configurations.
- Returns data in JSON format for consumption by a frontend application.

## Structure

- `api/`: Contains the API-related modules.
  - `routes/`: Defines the API endpoints.
  - `schemas/`: Contains Pydantic models for request and response data.
- `services/`: Contains mock services for backend components.
- `main.py`: The main entry point for the FastAPI application.
