"""
Unit tests for the scanner.data_fetcher module.
"""

import pandas as pd
import pytest
from pandas import Timestamp

from scanner.data_fetcher import fetch_stock_data


@pytest.fixture
def mock_yfinance_ticker(mocker):
    """
    Creates a mock for the yfinance.Ticker class.
    """
    # Create a mock for the Ticker class
    mock_ticker = mocker.patch("yfinance.Ticker", autospec=True)
    
    # Create a sample DataFrame to return from the history method
    dates = pd.date_range(start="2023-01-01", periods=300, freq="D")
    sample_data = pd.DataFrame(
        {
            "Open": [100 + i * 0.1 for i in range(300)],
            "High": [101 + i * 0.1 for i in range(300)],
            "Low": [99 + i * 0.1 for i in range(300)],
            "Close": [100 + i * 0.1 for i in range(300)],
            "Volume": [1000000 for _ in range(300)],
            "Dividends": [0 for _ in range(300)],
            "Stock Splits": [0 for _ in range(300)],
        },
        index=dates,
    )
    
    # Configure the mock to return the sample data
    mock_ticker.return_value.history.return_value = sample_data
    
    return mock_ticker


def test_fetch_stock_data_success(mock_yfinance_ticker):
    """
    Tests successful data fetching.
    """
    # Call the function with a test symbol
    result = fetch_stock_data("TEST.SR")
    
    # Check that yfinance.Ticker was called with the correct symbol
    mock_yfinance_ticker.assert_called_once_with("TEST.SR")
    
    # Check that the history method was called
    mock_yfinance_ticker.return_value.history.assert_called_once()
    
    # Check that the result is a DataFrame with the expected structure
    assert isinstance(result, pd.DataFrame)
    assert "Open" in result.columns
    assert "High" in result.columns
    assert "Low" in result.columns
    assert "Close" in result.columns
    assert "Volume" in result.columns
    
    # Check that the DataFrame has the expected number of rows
    assert len(result) == 300


def test_fetch_stock_data_empty_result(mocker, mock_yfinance_ticker):
    """
    Tests handling of empty result from yfinance.
    """
    # Configure the mock to return an empty DataFrame
    mock_yfinance_ticker.return_value.history.return_value = pd.DataFrame()
    
    # Call the function
    result = fetch_stock_data("TEST.SR")
    
    # Check that the result is None
    assert result is None


def test_fetch_stock_data_exception(mocker, mock_yfinance_ticker):
    """
    Tests handling of exceptions during data fetching.
    """
    # Configure the mock to raise an exception
    mock_yfinance_ticker.return_value.history.side_effect = Exception("Test exception")
    
    # Call the function
    result = fetch_stock_data("TEST.SR")
    
    # Check that the result is None
    assert result is None


def test_fetch_stock_data_timezone_handling(mocker, mock_yfinance_ticker):
    """
    Tests handling of timezone-aware DatetimeIndex.
    """
    # Create a sample DataFrame with timezone-aware index
    dates = pd.date_range(start="2023-01-01", periods=300, freq="D", tz="UTC")
    sample_data = pd.DataFrame(
        {
            "Open": [100 + i * 0.1 for i in range(300)],
            "High": [101 + i * 0.1 for i in range(300)],
            "Low": [99 + i * 0.1 for i in range(300)],
            "Close": [100 + i * 0.1 for i in range(300)],
            "Volume": [1000000 for _ in range(300)],
        },
        index=dates,
    )
    
    # Configure the mock to return the timezone-aware data
    mock_yfinance_ticker.return_value.history.return_value = sample_data
    
    # Call the function
    result = fetch_stock_data("TEST.SR")
    
    # Check that the result has a timezone-naive index
    assert result.index.tz is None