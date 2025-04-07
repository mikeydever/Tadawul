"""
Tests for the web API of the Tadawul Golden Cross Alert application.
"""

import pytest
from fastapi.testclient import TestClient

from web.api import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_home_endpoint(client):
    """Test that the home endpoint returns a 200 status code."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Tadawul Golden Cross Alert" in response.text


def test_get_stocks_endpoint(client):
    """Test that the get_stocks endpoint returns a list of stocks."""
    response = client.get("/api/stocks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_results_endpoint(client):
    """Test that the get_results endpoint returns the latest scan results."""
    response = client.get("/api/results")
    assert response.status_code == 200
    assert "golden_crosses" in response.json()
    assert "approaching_crosses" in response.json()
    assert "last_scan_time" in response.json()


def test_trigger_scan_endpoint(client, monkeypatch):
    """Test that the trigger_scan endpoint starts a scan."""
    # Mock the background task to avoid actually running a scan
    def mock_add_task(self, func, *args, **kwargs):
        pass

    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)

    response = client.post("/api/scan")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "message" in response.json()


def test_get_stock_data_endpoint_valid_symbol(client, monkeypatch):
    """Test that the get_stock_data endpoint returns data for a valid symbol."""
    # Mock the fetch_stock_data function
    import pandas as pd
    from datetime import datetime, timedelta

    def mock_fetch_stock_data(symbol):
        # Create a simple DataFrame with test data
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        data = {
            "Open": [100 + i for i in range(30)],
            "High": [105 + i for i in range(30)],
            "Low": [95 + i for i in range(30)],
            "Close": [102 + i for i in range(30)],
            "Volume": [1000000 for _ in range(30)],
            "Date": dates,  # Add Date column for API processing
        }
        df = pd.DataFrame(data, index=dates)
        return df

    # Mock the calculate_indicators function
    def mock_calculate_indicators(df):
        df["SMA_50"] = df["Close"].rolling(window=5).mean()  # Use 5 instead of 50 for test
        df["SMA_200"] = df["Close"].rolling(window=10).mean()  # Use 10 instead of 200 for test
        # Add mock indicator values
        df["RSI"] = 50.0  # Mock RSI value
        df["MACD"] = 0.5  # Mock MACD value
        df["MACD_Signal"] = 0.3  # Mock MACD Signal value
        df["MACD_Histogram"] = 0.2  # Mock MACD Histogram value
        df["BB_Middle"] = df["Close"]  # Mock Bollinger Bands
        df["BB_Upper"] = df["Close"] + 2.0
        df["BB_Lower"] = df["Close"] - 2.0
        df["Stoch_K"] = 60.0  # Mock Stochastic K value
        df["Stoch_D"] = 40.0  # Mock Stochastic D value
        return df

    # Mock the check functions
    def mock_check_golden_cross(df):
        return True

    def mock_check_approaching_golden_cross(df):
        return False

    monkeypatch.setattr("web.api.fetch_stock_data", mock_fetch_stock_data)
    monkeypatch.setattr("web.api.calculate_indicators", mock_calculate_indicators)
    monkeypatch.setattr("web.api.check_golden_cross", mock_check_golden_cross)
    monkeypatch.setattr("web.api.check_approaching_golden_cross", mock_check_approaching_golden_cross)

    response = client.get("/api/stock/2222.SR")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["symbol"] == "2222.SR"
    assert response.json()["is_golden_cross"] is True
    assert response.json()["is_approaching_cross"] is False
    assert "chart_data" in response.json()


def test_get_stock_data_endpoint_invalid_symbol(client, monkeypatch):
    """Test that the get_stock_data endpoint handles invalid symbols."""
    # Mock the fetch_stock_data function to return None
    def mock_fetch_stock_data(symbol):
        return None

    monkeypatch.setattr("web.api.fetch_stock_data", mock_fetch_stock_data)

    response = client.get("/api/stock/INVALID")
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "message" in response.json()