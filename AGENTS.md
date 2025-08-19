# Repository Guidelines

## Project Structure & Module Organization
- Backend: `server/` (FastAPI). Entry: `server/main.py`; routers in `server/api/routes/`; schemas in `server/api/schemas/`; services in `server/services/` via a factory (simple → integrated → mock).
- Frontend: `ui/` (React + Vite + Tailwind + TS). Built assets in `ui/dist/` served by the backend.
- Bot modules: `bot_runner/`, `strategy/`, `market_data/`, `execution_engine/`, `portfolio_risk/`, `backtest/` with their own READMEs.
- Scripts: `start_server.py` (serve UI + API), `run_bots.py` (demo runners), `run_tests.py` (strategy tests). Tests for API in `server/tests/`.

## Build, Test, and Development Commands
- Backend deps: `pip install -r requirements.txt`
- Frontend build: `cd ui && pnpm install && pnpm run build`
- All-in-one server: `python start_server.py` → http://localhost:8000
- Dev mode: backend `python -m uvicorn server.main:app --reload --port 8000`; frontend `cd ui && pnpm run dev`
- Server tests (if pytest installed): `pytest -q server/tests`
- Strategy tests: `python run_tests.py`

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indent, type hints, PEP 257 docstrings. Follow CLAUDE.md: top-of-file comments and clear function docs.
- TypeScript/React: keep components small; use Prettier/ESLint (see `ui` configs). Use `PascalCase` for components, `camelCase` for vars.
- Modules organized by domain (e.g., `server/services/*`, `strategy/strategies/*`).

## Testing Guidelines
- API tests: `server/tests/` use `httpx.AsyncClient`. Validate JSON shapes (bots list, metrics, root message).
- Frontend: use manual dev verification against local API (`VITE_API_BASE_URL` if needed).
- Coverage optional; prioritize core endpoints and service paths.

## Commit & Pull Request Guidelines
- Commits: Conventional Commit style (`feat:`, `fix:`, `chore:`, `docs:`, `test:`) in imperative mood.
- PRs: include problem/solution summary, steps to verify (commands/URLs), and link issues (`Closes #123`). Attach screenshots/logs for UI/API changes.

## Security & Configuration Tips
- Do not commit secrets. Backend env via `.env` (gitignored); frontend uses `.env.local` and `VITE_API_BASE_URL`.
- CORS is enabled for local dev (see `server/main.py`). Validate inputs at API boundaries; avoid broad exception handling in services.
