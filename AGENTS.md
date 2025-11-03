# Repository Guidelines

## Project Structure & Module Organization
- `backend/` hosts the FastAPI service (entrypoint `app/main.py`, domain logic in `app/services/`, background tasks in `app/tasks/`). Reusable ingestion utilities live in `scripts/`.
- `frontend/` delivers the mobile Vue 3 client; views under `src/views/`, shared API client at `src/api/client.ts`, and Vite config in `vite.config.ts`.
- `admin-frontend/` contains the Element Plus admin console; routing and stores mirror the mobile app to simplify feature parity.
- `nginx/nginx.conf` defines the reverse proxy used by `docker-compose.yml`; update alongside any new service ports.
- Reference docs (`PROJECT_STRUCTURE.md`, `API_DOCUMENTATION.md`) must be updated whenever these folders or endpoints change.

## Build, Test, and Development Commands
- Backend: `python -m venv .venv && .venv\\Scripts\\activate` then `pip install -r requirements.txt`; launch with `uvicorn app.main:app --reload --port 8000`.
- Frontends: inside `frontend/` or `admin-frontend/`, run `npm install` once, `npm run dev` for hot reload, `npm run build` for production bundles, and `npm run preview` to smoke-test builds.
- Full stack: `docker-compose up --build` starts Postgres, Redis, backend, and Nginx with default ports.
- Data pipelines: run scripts from `backend/scripts/` (e.g., `python scripts/crawl_and_ingest.py`) after exporting required env vars.

## Coding Style & Naming Conventions
- Python modules use 4-space indentation, snake_case files, and typed FastAPI endpoints that delegate work to `services/`. Prefer Pydantic models from `schemas.py` for IO contracts.
- Vue/TypeScript code relies on 2-space indentation, single quotes, `PascalCase.vue` component names, and `camelCase.ts` utilities. Centralize API paths in `src/api/`.
- Environment keys stay UPPER_SNAKE_CASE; mirror `.env.example` when adding configuration.

## Testing Guidelines
- No automated suite is checked in yet. Add backend tests with Pytest under `backend/tests/` and expose a `python -m pytest` runner before merging service-level changes.
- For Vue apps, scaffold component tests with Vitest in `src/__tests__/` and run via an `npm run test` script when introduced.
- Document manual verification steps (API smoke, UI flows) in PRs until automated coverage exists.

## Commit & Pull Request Guidelines
- Follow imperative, scoped commit subjects (e.g., `backend: add crawler scheduler`). Keep message bodies under 72 characters per line and note migrations or scripts to rerun.
- PRs require a problem statement, solution summary, affected services, and screenshots or GIFs for UI changes. Link issues via `Resolves #id`.
- Request reviews from the owning squad and confirm `.env` updates, database migrations, and documentation changes in the checklist.

## Configuration & Security Notes
- Copy `.env.example` to `.env` per service; never commit secrets or production URLs.
- Keep port and host mappings aligned across `docker-compose.yml`, service `.env`, and `nginx/nginx.conf` to avoid split-brain routing.
- After schema updates, execute `python migrate_database.py` from `backend/` and capture results in the release notes.
