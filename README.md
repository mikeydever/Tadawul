# KSA Golden Cross Scanner

An automated application to scan stocks listed on the Saudi Stock Exchange (Tadawul) daily for potential "Golden Cross" technical patterns (50-day SMA crossing above 200-day SMA) and notify the user.

## Features

- **Data Fetching:** Retrieves daily End-of-Day (EOD) price data for specified Tadawul stocks.
- **SMA Calculation:** Calculates the 50-day and 200-day Simple Moving Averages (SMAs) for each stock.
- **Golden Cross Detection:** Identifies stocks where the 50-day SMA has crossed above the 200-day SMA on the most recent trading day.
- **Approaching Cross Detection:** Identifies stocks that are approaching a Golden Cross (within a configurable threshold).
- **Email Notifications:** Sends email alerts listing the stocks that triggered the golden cross signal.
- **Web Interface:** Provides a web-based UI for viewing scan results and stock details.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd tadawul-golden-cross-alert
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   EMAIL_HOST=your-smtp-server.com
   EMAIL_PORT=587
   EMAIL_USER=your-email@example.com
   EMAIL_PASSWORD=your-password
   EMAIL_RECIPIENT=recipient@example.com
   EMAIL_SENDER_NAME=Golden Cross Alert
   ```

5. Create a `stocks.txt` file with the list of Tadawul stock symbols to monitor (one per line).

## Usage

### Command-line Interface

Run the scanner from the command line:

```
python main.py
```

This will scan all stocks in `stocks.txt` for Golden Cross patterns and send an email notification if any are found.

### Web Interface

Start the web server:

```
python run_web.py
```

Then open your browser and navigate to `http://localhost:8000` to access the web interface.

The web interface allows you to:
- View the list of monitored stocks
- View the results of the latest scan
- Trigger a new scan manually
- View detailed charts for each stock

## Running Tests

Run the tests using pytest:

```
pytest
```

## License

[MIT License](LICENSE)