# UI Module

This module contains a React-based web user interface for monitoring and controlling the trading bot platform.

## Features

- Displays live strategy status, PnL, positions, and configuration.
- Allows users to start, stop, and update bot configurations, and trigger kill-switches.
- Provides detailed views for trade history and risk evaluations.
- Built with React, TanStack Router, React Query, Tailwind CSS, and shadcn/ui.

## Technologies Used

- **Framework**: React
- **Routing**: TanStack Router
- **Data Fetching**: React Query
- **Styling**: Tailwind CSS, shadcn/ui
- **Language**: TypeScript

## Structure

- `public/`: Static assets.
- `src/`: Source code.
  - `app/`: Contains the main application pages and TanStack Router setup.
  - `components/`: Reusable UI components.
  - `lib/`: API client and utility functions.
  - `hooks/`: Custom React Query hooks for data fetching.
  - `types/`: TypeScript type definitions.
- `package.json`: Project dependencies and scripts.
- `tailwind.config.js`, `postcss.config.js`: Tailwind CSS configuration.
- `tsconfig.json`: TypeScript configuration.
- `.env.local`: Environment variables.
