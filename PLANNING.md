# PLANNING.md - KSA Golden Cross Scanner

## 1. Project Goal

To develop an automated application that scans stocks listed on the Saudi Stock Exchange (Tadawul) daily to identify potential "Golden Cross" technical patterns (50-day SMA crossing above 200-day SMA). The application will notify the user (initially via email) when such patterns are detected.

## 2. Core Features (MVP - Phase 1)

-   **Data Fetching:** Retrieve daily End-of-Day (EOD) price data for specified Tadawul stocks.
-   **SMA Calculation:** Calculate the 50-day and 200-day Simple Moving Averages (SMAs) for each stock.
-   **Golden Cross Detection:** Identify stocks where the 50-day SMA has crossed above the 200-day SMA on the most recent trading day.
-   **Notification:** Send an email alert listing the stocks that triggered the golden cross signal.
-   **Configuration:** Load necessary settings (e.g., email credentials, potentially stock list) from environment variables.
-   **Logging:** Basic logging of operations and errors.

## 3. Technology Stack

-   **Language:** Python 3.x
-   **Data Handling:** pandas
-   **Initial Data Source:** yfinance (Note: Plan to replace with a more robust API in Phase 2 due to potential reliability issues).
-   **Configuration:** python-dotenv
-   **Testing:** pytest, pytest-mock
-   **Formatting:** black
-   **Linting/Style:** PEP8, Type Hints
-   **Dependency Management:** requirements.txt

*(Future considerations: FastAPI for potential API, SQLAlchemy/SQLModel if database storage is added)*

## 4. Architecture (Initial - Script-based)

-   A main script (`main.py`) will orchestrate the daily scan.
-   Modular structure:
    -   `scanner` module for data fetching and analysis logic.
    -   `notifier` module for handling email notifications.
    -   `config` module for loading settings.
-   The script is intended to be run daily via a scheduler (e.g., cron, Task Scheduler, cloud scheduler).
-   No persistent database in the MVP.

## 5. File Structure (Initial Plan)