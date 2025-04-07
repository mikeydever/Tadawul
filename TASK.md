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

## MVP Development (Phase 1)

-   [x] Implement configuration loading using `python-dotenv` in `config/settings.py` (load email settings, potentially a test stock symbol). (2025-04-05)
-   [x] Implement basic data fetching function in `scanner/data_fetcher.py` to get ~250 days of historical data for a *single* hardcoded Tadawul stock symbol using `yfinance`. Handle potential `yfinance` errors. (2025-04-05)
-   [x] Implement functions in `scanner/analysis.py` to calculate 50-day and 200-day SMAs from a pandas DataFrame of price data. (2025-04-05)
-   [x] Implement logic in `scanner/analysis.py` to detect if a golden cross occurred *today* (comparing latest SMAs to previous day's). Function should return True/False. (2025-04-05)
-   [x] Implement basic email sending function in `notifier/email_sender.py` using Python's `smtplib`. Function should accept subject, body, recipient. (2025-04-05)
-   [x] Create main script (`main.py`) to:
    -   Load configuration.
    -   Call data fetcher.
    -   Call analysis functions (SMA calc, cross check).
    -   If cross detected, call email sender with appropriate message.
    -   Integrate basic logging using the `logging` module. (2025-04-05)
-   [x] Write unit tests for SMA calculation (`tests/scanner/test_analysis.py`) using sample DataFrame.
-   [x] Write unit tests for golden cross detection logic (`tests/scanner/test_analysis.py`) using sample data representing cross/no cross scenarios.
-   [x] Write unit test for data fetching (`tests/scanner/test_data_fetcher.py`) using `pytest-mock` to mock `yfinance` calls.
-   [x] Write unit test for email sending (`tests/notifier/test_email_sender.py`) using `pytest-mock` to mock `smtplib`.

## Future Tasks (Phase 2+)

-   [x] Fetch list of all Tadawul stocks dynamically or from config/file. (2025-04-06)
-   [x] Modify `main.py` to loop through all stocks, perform analysis, and collect all triggers before sending a single summary email. (2025-04-06)
-   [x] Implement "heading towards" golden cross logic (e.g., 50d SMA within X% of 200d SMA and rising). (2025-04-06)
-   [ ] Research and refactor data source (`scanner/data_fetcher.py`) to use a chosen stable API (e.g., Twelve Data, EODHD) instead of `yfinance`. Update configuration and tests accordingly.
-   [ ] Add Death Cross detection as an optional alert.
-   [ ] Explore adding other indicators (RSI, MACD) for combined signals.
- [x] Consider adding a simple web UI (e.g., using FastAPI) for configuration and viewing results. (2025-04-06)
-   [ ] Implement user management if multiple users are needed.
-   [ ] Add alternative notification options (Push, SMS).
-   [ ] Implement a backtesting feature to evaluate signal effectiveness historically.

## Discovered During Work

*(Add any new tasks or necessary changes identified during development here)*