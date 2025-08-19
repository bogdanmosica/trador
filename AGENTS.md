# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `src/` (libraries, domain modules) and entry points under `bin/` or `apps/` if present. Tests are in `tests/` mirroring `src/` paths. Shared scripts go in `scripts/`. Static assets in `assets/` or `public/`. Config and samples in `config/` and `.env.example`.
- Prefer small, focused modules. Group by domain (e.g., `src/orders/`, `src/core/`) with an `index`/`__init__` that exposes public APIs.

## Build, Test, and Development Commands
- Install: use the project’s tool if present
  - Node: `npm ci` or `pnpm i`
  - Python: `poetry install` or `pip install -r requirements.txt`
  - Rust: `cargo build`
- Run locally: check `Makefile` or `package.json` scripts; common: `make dev`, `npm run dev`, or `python -m <module>`.
- Tests: `npm test`, `pytest -q`, or `cargo test` depending on stack.
- Lint/format: `npm run lint && npm run format`, `ruff check --fix && black .`, or `cargo fmt && cargo clippy -D warnings`.

## Coding Style & Naming Conventions
- Indentation: 2 spaces (JS/TS), 4 spaces (Python).
- Names: `camelCase` variables/functions, `PascalCase` classes/types, `snake_case` files (Python) or `kebab-case` (JS/TS CLI/util files).
- Keep modules <300 lines; prefer pure functions and clear boundaries.
- Run formatters before committing (Prettier/ESLint, Black/Ruff, rustfmt/clippy as applicable).

## Testing Guidelines
- Place unit tests in `tests/` mirroring source paths (`tests/orders/test_service.*`, `src/orders/service.*`).
- Use descriptive, behavior-focused names: `should_do_x_when_y` (JS) or `test_does_x_when_y` (Python).
- Aim for meaningful coverage on core logic; run with `--coverage`/`--cov` if configured.

## Commit & Pull Request Guidelines
- Commits: imperative mood; prefer Conventional Commits when possible: `feat:`, `fix:`, `chore:`, `docs:`, `test:`.
- Branches: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`.
- PRs: concise title, problem/solution summary, linked issues (`Closes #123`), screenshots or logs when UI/behavior changes. Ensure CI green and lint/format run locally.

## Security & Configuration
- Do not commit secrets. Use `.env` (gitignored) and keep `.env.example` up to date.
- Validate inputs at module boundaries; handle errors explicitly; avoid broad catches and silent failures.
