# Trador - Trading Bot Dashboard

A comprehensive trading bot management system with a modern web interface and FastAPI backend.

## 🚀 Quick Start

### Method 1: All-in-One Server (Recommended)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the frontend:**
   ```bash
   cd ui
   pnpm install
   pnpm build
   cd ..
   ```

3. **Start the server:**
   ```bash
   python start_server.py
   ```

   The application will be available at:
   - **Dashboard:** http://localhost:8000
   - **API Docs:** http://localhost:8000/docs
   - **API Base:** http://localhost:8000/api

### Method 2: Development Mode (Frontend + Backend separate)

1. **Terminal 1 - Start Backend:**
   ```bash
   pip install -r requirements.txt
   python -m uvicorn server.main:app --reload --port 8000
   ```

2. **Terminal 2 - Start Frontend:**
   ```bash
   cd ui
   pnpm install
   pnpm run dev
   ```

## 📁 Project Structure

```
trador/
├── server/              # FastAPI backend
│   ├── main.py         # Main application entry
│   ├── api/            # API routes and schemas
│   └── services/       # Business logic
├── ui/                 # React frontend
│   ├── src/            # Source code
│   ├── dist/           # Built files (served by backend)
│   └── package.json    # Node.js dependencies
├── backtest/           # Backtesting module
├── bot_runner/         # Bot execution engine
├── execution_engine/   # Trade execution
├── market_data/        # Data providers
├── portfolio_risk/     # Risk management
├── strategy/           # Trading strategies
└── requirements.txt    # Python dependencies
```

## 🤖 Features

### Dashboard
- **Overview:** Total bots, active status, P&L summary
- **Bot Management:** Start/stop bots, view details
- **Real-time Metrics:** Live trading statistics

### API Endpoints
- `GET /api/bots` - List all bots
- `POST /api/bots/{id}/start` - Start a bot
- `POST /api/bots/{id}/stop` - Stop a bot
- `GET /api/bots/{id}/status` - Get bot status
- `GET /api/bots/{id}/trades` - Get trade history
- `GET /api/bots/{id}/risk` - Get risk evaluation
- `GET /api/metrics/global` - Global metrics

### Frontend Features
- **Responsive Design:** Works on desktop and mobile
- **Real-time Updates:** Live bot status and metrics
- **Navigation:** Easy switching between dashboard and bot details
- **Modern UI:** Clean, professional interface with Tailwind CSS

## 🛠 Development

### Backend Development
```bash
cd server
python -m uvicorn main:app --reload
```

### Frontend Development
```bash
cd ui
pnpm run dev
```

### Build for Production
```bash
cd ui
pnpm run build
```

## 📦 Dependencies

### Backend (Python)
- FastAPI - Modern web framework
- Uvicorn - ASGI server
- Pydantic - Data validation

### Frontend (Node.js)
- React 19 - UI framework
- TanStack Router - Client-side routing
- TanStack Query - Data fetching
- Tailwind CSS - Styling
- TypeScript - Type safety

## 🔧 Configuration

The server automatically:
- Serves the built frontend at the root URL
- Provides API endpoints at `/api/*`
- Handles client-side routing for the React app
- Includes CORS configuration for development

## 📊 Mock Data

The application includes mock trading bots with:
- **bot_1:** Running live bot with positive P&L
- **bot_2:** Stopped backtest bot with negative P&L

Perfect for testing and demonstration purposes.

## 🚀 Deployment

For production deployment:

1. Build the frontend: `cd ui && pnpm run build`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run the server: `python start_server.py`

The server will serve both the API and frontend on port 8000.