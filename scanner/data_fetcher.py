"""
Fetches historical stock data using the yfinance library.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from config import settings # Import settings from the config package

logger = logging.getLogger(__name__)


def fetch_stock_data(symbol: str) -> pd.DataFrame | None:
    """
    Fetches historical stock data for a given symbol.

    Retrieves daily End-of-Day (EOD) data for the specified number of days
    defined in `config.settings.DATA_FETCH_DAYS`.

    Args:
        symbol: The stock symbol to fetch data for (e.g., "2222.SR").
                Should follow yfinance conventions (e.g., append ".SR" for Tadawul).

    Returns:
        A pandas DataFrame containing the historical data (Date, Open, High,
        Low, Close, Volume, Dividends, Stock Splits), indexed by Date.
        Returns None if data fetching fails or no data is returned.

    Raises:
        # Potentially specific yfinance exceptions if not caught,
        # but aiming to catch broadly and return None.
        pass # No explicit raises defined, handles errors internally.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=settings.DATA_FETCH_DAYS)

    logger.info(
        f"Fetching data for {symbol} from {start_date.strftime('%Y-%m-%d')} "
        f"to {end_date.strftime('%Y-%m-%d')}"
    )

    try:
        ticker = yf.Ticker(symbol)
        # Use start/end dates for clarity, period can sometimes be inconsistent
        hist_df = ticker.history(start=start_date, end=end_date, interval="1d")

        if hist_df.empty:
            logger.warning(f"No data returned for symbol: {symbol}")
            return None

        # yfinance sometimes returns data slightly outside the requested range
        # Ensure the index is timezone-naive for consistency if needed,
        # though yfinance usually handles this. Let's check:
        if hist_df.index.tz is not None:
             hist_df.index = hist_df.index.tz_localize(None)

        logger.info(f"Successfully fetched {len(hist_df)} data points for {symbol}")
        return hist_df

    except Exception as e:
        # Catching a broad exception for now, can be refined if specific
        # yfinance errors need distinct handling.
        logger.error(f"Failed to fetch data for {symbol}: {e}", exc_info=True)
        return None

# Example usage (optional, for testing during development)
# if __name__ == "__main__":
#     # Ensure you have a .env file or environment variables set
#     # for TEST_STOCK_SYMBOL if running this directly
#     test_symbol = settings.TEST_STOCK_SYMBOL
#     data = fetch_stock_data(test_symbol)
#     if data is not None:
#         print(f"\n--- Sample Data for {test_symbol} ---")
#         print(data.tail())
#         print("\n--- Data Info ---")
#         data.info()
#     else:
#         print(f"Could not fetch data for {test_symbol}.")