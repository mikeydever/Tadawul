# PLANNING.md - KSA Golden Cross Scanner

## 1. Project Goal

To develop an automated application that scans stocks listed on the Saudi Stock Exchange (Tadawul) daily to identify potential "Golden Cross" technical patterns (50-day SMA crossing above 200-day SMA) and other relevant technical indicators. The application will provide a web interface for viewing results and triggering scans, and optionally notify users (initially via email) when specific patterns are detected.

## 2. Core Features

-   **Data Fetching:** Retrieve daily End-of-Day (EOD) price data for specified Tadawul stocks.
-   **Indicator Calculation:** Calculate 50-day/200-day SMAs, RSI, MACD, Bollinger Bands, Stochastic Oscillator.
-   **Pattern Detection:** Identify Golden Crosses and potentially other patterns (e.g., approaching crosses, Death Crosses).
-   **Web Interface:** Provide a UI to view monitored stocks, trigger scans, see scan results, and view detailed stock charts with technical indicators.
-   **(Optional) Notification:** Send email alerts for detected patterns (if configured).
-   **Configuration:** Load necessary settings (e.g., email credentials, stock list) from environment variables or configuration files.
-   **Logging:** Logging of backend operations and errors.
-   **(Future) User Accounts:** Allow users to register/login to receive personalized alerts.

## 3. Technology Stack

-   **Language:** Python 3.x
-   **Backend Framework:** FastAPI
-   **Web Server:** Uvicorn
-   **Frontend Framework/UI:** React (or Next.js - typical for shadcn/ui)
-   **UI Components:** shadcn/ui
-   **CSS Framework:** Tailwind CSS
-   **Charting:** Chart.js (or similar JavaScript library)
-   **Data Handling:** pandas
-   **Initial Data Source:** yfinance (Note: Plan to replace with a more robust API due to potential reliability issues).
-   **Configuration:** python-dotenv
-   **Testing:** pytest, pytest-mock
-   **Formatting:** black
-   **Linting/Style:** PEP8, Type Hints
-   **Dependency Management:** requirements.txt (Python), package.json (Node.js/Frontend)
-   **(Future) Database:** SQLAlchemy/SQLModel with SQLite/PostgreSQL (for user accounts)

## 4. Architecture (Web Application)

-   **Backend API:** A FastAPI application (`web/api.py` or similar) serves data and handles requests from the frontend.
-   **Frontend:** A separate frontend application built with React/Next.js, using `shadcn/ui` components and Tailwind CSS for styling. Served as static files or via a Node.js server.
-   **Backend Modules:**
    -   `scanner` module for data fetching and analysis logic.
    -   `notifier` module for handling email notifications.
    *   `config` module for loading settings.
    *   `(Future)` Database models and interaction logic.
-   Scans can be triggered via the web UI (running as background tasks in FastAPI) or potentially run on a schedule.

## 5. File Structure (Revised Plan - Example)