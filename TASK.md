# TASK.md - KSA Golden Cross Scanner

*   Format: `- [ ] Task Description (YYYY-MM-DD)`
*   Mark completed tasks with `[x]`

## Initial Setup (2025-04-05)

-   [x] Create project directory structure as outlined in `PLANNING.md`.
-   [x] Initialize Git repository and create `.gitignore` (include `.env`, `__pycache__/`, `*.pyc`, virtual env folder).
-   [x] Set up Python virtual environment (e.g., `python -m venv venv`).
-   [x] Create initial `requirements.txt` with `python-dotenv`, `yfinance`, `pandas`, `pytest`, `pytest-mock`, `black`.
-   [x] Create basic `README.md` with project title and brief description.
-   [x] Create empty `__init__.py` files in `scanner`, `notifier`, `config`, `tests`, `tests/scanner`, `tests/notifier` directories.

## MVP Development (Phase 1 - Script-based)

-   [x] Implement configuration loading using `python-dotenv` in `config/settings.py`. (2025-04-05)
-   [x] Implement basic data fetching function in `scanner/data_fetcher.py` for a single stock using `yfinance`. (2025-04-05)
-   [x] Implement functions in `scanner/analysis.py` to calculate 50-day and 200-day SMAs. (2025-04-05)
-   [x] Implement logic in `scanner/analysis.py` to detect golden cross occurrence. (2025-04-05)
-   [x] Implement basic email sending function in `notifier/email_sender.py`. (2025-04-05)
-   [x] Create main script (`main.py`) orchestrating the scan and notification for a single stock. (2025-04-05)
-   [x] Write unit tests for analysis, data fetching, and email sending. (2025-04-05)

## Backend Enhancements (Phase 2)

-   [x] Implement loading stock list from `stocks.txt`. (2025-04-06)
-   [x] Modify backend logic (`main.py` or equivalent) to loop through all stocks from `stocks.txt`. (2025-04-06)
-   [x] Implement "approaching golden cross" detection logic in `scanner/analysis.py`. (2025-04-06)
-   [x] Implement backend calculation for additional indicators (RSI, MACD, Bollinger Bands, Stochastic Oscillator) in `scanner/analysis.py`. (2025-04-06)
-   [x] Create initial FastAPI backend (`web/api.py`, `run_web.py`) to serve data and trigger scans. (2025-04-06)
-   [x] Add/Update tests for multi-stock scanning, approaching crosses, indicator calculations, and basic API endpoints. (2025-04-06)

## Frontend Overhaul (shadcn/ui - 2025-04-07)

-   [x] Set up new Next.js frontend project (presumably in `frontend/` or similar). (2025-04-07)
-   [x] Initialize shadcn/ui in the new frontend project. (2025-04-07)
-   [x] Apply provided theme variables to shadcn/ui. (2025-04-07)
-   [x] Rebuild the UI to display scan status, monitored stocks, and basic golden cross results (fetching from FastAPI backend). (2025-04-07)
-   [x] Add basic navigation/layout using shadcn/ui components. (2025-04-07)
-   [x] Update backend API (`web/api.py`) for CORS to support the new frontend. (2025-04-07)
-   [x] Implement frontend display (charts/visualizations) for RSI, MACD, and Stochastic Oscillator in the stock details view. (2025-04-07)
-   [x] **Fix Bug:** Bollinger Bands are calculated and mentioned in the UI, but are not visually rendered on the main price chart in the stock details view. Ensure they are correctly overlaid.
-   [x] Add unit/integration tests for the new frontend components. (2025-04-09)

## User Accounts & Personalized Alerts (Phase 3 - Future)

-   [x] Choose and integrate a database (e.g., SQLite with SQLModel). (2025-04-09)
-   [x] Define User model (email, hashed_password). (2025-04-09)
-   [x] Implement password hashing (e.g., using passlib). (2025-04-09)
-   [x] Create backend API endpoints for user registration. (2025-04-07 - Backend only)
-   [x] Create backend API endpoints for user login (e.g., returning JWT token). (2025-04-09)
-   [x] Implement token-based authentication for protected API endpoints. (2025-04-09)
-   [x] Fix SQLModel import error and run tests successfully. (2025-04-09)
-   [ ] Create frontend registration page/form. (Currently missing)
-   [ ] Create frontend login page/form.
-   [ ] Implement frontend logic to handle login tokens/sessions and protect routes.
-   [ ] Add logout functionality.
-   [ ] Modify email notification logic to send reports based on registered user preferences (requires defining preferences first).
-   [ ] Add tests for authentication and user management.

## Other Future Tasks / Improvements

-   [ ] Research and refactor data source (`scanner/data_fetcher.py`) to use a chosen stable API (e.g., Twelve Data, EODHD) instead of `yfinance`. Update configuration and tests accordingly.
-   [ ] Add Death Cross detection as an optional alert (backend and frontend).
-   [ ] Add alternative notification options (Push, SMS).
-   [ ] Implement a backtesting feature to evaluate signal effectiveness historically.
-   [ ] Consider deployment strategy (e.g., Docker, cloud platform).
-   [ ] Refactor project structure (e.g., separate `backend/` and `frontend/` folders).

## Discovered During Work

*(Add any new tasks or necessary changes identified during development here)*