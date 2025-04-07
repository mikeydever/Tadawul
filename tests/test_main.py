"""
Unit tests for the main script (main.py).
"""

import logging
from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest


# Fixture to provide basic stock data for mocking
@pytest.fixture
def mock_stock_data():
    dates = pd.date_range(start="2023-01-01", periods=250, freq="D")
    df = pd.DataFrame(
        {
            "Close": [100 + i * 0.1 for i in range(250)],
            "SMA_50": [90 + i * 0.1 for i in range(250)], # Example SMA data
            "SMA_200": [80 + i * 0.1 for i in range(250)], # Example SMA data
        },
        index=dates,
    )
    return df

# Test case: No symbols configured
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_no_symbols(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings):
    """Tests run_scan when settings.STOCK_SYMBOLS is empty."""
    mock_settings.STOCK_SYMBOLS = []
    mock_settings.EMAIL_RECIPIENT = "test@example.com" # Needed for later checks

    # Import run_scan here after patching settings
    from main import run_scan
    run_scan()

    # Assertions
    mock_fetch.assert_not_called()
    mock_calc_indicators.assert_not_called()
    mock_check_cross.assert_not_called()
    mock_approaching_cross.assert_not_called()
    mock_send_email.assert_not_called()

# Test case: One symbol triggers a cross
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_one_trigger(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests run_scan with one symbol triggering a golden cross."""
    mock_settings.STOCK_SYMBOLS = ["TICK1.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50 # Needed for SMA col checks
    mock_settings.LONG_SMA_WINDOW = 200 # Needed for SMA col checks

    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data # Assume indicators are calculated correctly
    mock_check_cross.return_value = True # Simulate golden cross
    mock_approaching_cross.return_value = False # Not approaching (already crossed)

    from main import run_scan
    run_scan()

    # Assertions
    mock_fetch.assert_called_once_with("TICK1.SR")
    mock_calc_indicators.assert_called_once_with(mock_stock_data)
    mock_check_cross.assert_called_once_with(mock_stock_data)
    mock_approaching_cross.assert_called_once_with(mock_stock_data) # Always called
    mock_send_email.assert_called_once()
    # Check email content (basic check)
    call_args, call_kwargs = mock_send_email.call_args
    assert "Golden Cross Alert: 1 Symbol(s) Triggered" in call_kwargs["subject"]
    assert "TICK1.SR" in call_kwargs["body"]
    assert call_kwargs["recipient"] == "test@example.com"

# Test case: Multiple symbols trigger a cross
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_multiple_triggers(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests run_scan with multiple symbols triggering."""
    mock_settings.STOCK_SYMBOLS = ["TICK1.SR", "TICK2.SR", "TICK3.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200

    # Simulate fetch and calc returning valid data
    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data

    # Simulate cross for TICK1 and TICK3, no cross for TICK2
    mock_check_cross.side_effect = [True, False, True]
    # Called for all symbols
    mock_approaching_cross.side_effect = [False, True, False]

    from main import run_scan
    run_scan()

    # Assertions
    assert mock_fetch.call_count == 3
    assert mock_calc_indicators.call_count == 3
    assert mock_check_cross.call_count == 3
    assert mock_approaching_cross.call_count == 3 # Called for all symbols
    mock_send_email.assert_called_once()
    # Check email content
    call_args, call_kwargs = mock_send_email.call_args
    assert "Golden Cross Alert:" in call_kwargs["subject"]
    assert "TICK1.SR" in call_kwargs["body"]
    assert "TICK3.SR" in call_kwargs["body"]
    assert call_kwargs["recipient"] == "test@example.com"

# Test case: No symbols trigger a cross
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_no_triggers(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests run_scan with no symbols triggering."""
    mock_settings.STOCK_SYMBOLS = ["TICK1.SR", "TICK2.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200

    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data
    mock_check_cross.return_value = False # No crosses
    mock_approaching_cross.return_value = False # No approaching crosses

    from main import run_scan
    run_scan()

    # Assertions
    assert mock_fetch.call_count == 2
    assert mock_calc_indicators.call_count == 2
    assert mock_check_cross.call_count == 2
    assert mock_approaching_cross.call_count == 2
    mock_send_email.assert_not_called() # No email should be sent

# Test case: Fetch fails for one symbol
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_fetch_fails(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests that the scan continues if fetching fails for one symbol."""
    mock_settings.STOCK_SYMBOLS = ["GOOD.SR", "BAD.SR", "GOOD2.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200

    # Simulate fetch failing for BAD.SR, succeeding for others
    mock_fetch.side_effect = [mock_stock_data, None, mock_stock_data]
    mock_calc_indicators.return_value = mock_stock_data
    # Simulate cross for GOOD.SR and GOOD2.SR
    mock_check_cross.side_effect = [True, True] # Only called for successful fetches
    mock_approaching_cross.side_effect = [False, False] # Called for successful fetches

    from main import run_scan
    run_scan()

    # Assertions
    assert mock_fetch.call_count == 3
    assert mock_calc_indicators.call_count == 2 # Not called for BAD.SR
    assert mock_check_cross.call_count == 2 # Not called for BAD.SR
    assert mock_approaching_cross.call_count == 2 # Called for successful fetches
    mock_send_email.assert_called_once()
    # Check email content
    call_args, call_kwargs = mock_send_email.call_args
    assert "Golden Cross Alert:" in call_kwargs["subject"]
    assert "GOOD.SR" in call_kwargs["body"]
    assert "BAD.SR" not in call_kwargs["body"]
    assert "GOOD2.SR" in call_kwargs["body"]

# Test case: SMA calculation fails (missing columns) for one symbol
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_sma_calc_fails(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests that the scan continues if SMA calculation fails for one symbol."""
    mock_settings.STOCK_SYMBOLS = ["GOOD.SR", "BAD.SR", "GOOD2.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200

    # Data without SMA columns
    bad_sma_data = mock_stock_data.copy().drop(columns=["SMA_50", "SMA_200"])

    mock_fetch.return_value = mock_stock_data # Fetch always succeeds
    # Simulate SMA calc returning data without SMA cols for BAD.SR
    mock_calc_indicators.side_effect = [mock_stock_data, bad_sma_data, mock_stock_data]
    # Simulate cross for GOOD.SR and GOOD2.SR
    mock_check_cross.side_effect = [True, True] # Only called for successful SMA calcs
    mock_approaching_cross.side_effect = [False, False] # Called for successful SMA calcs

    from main import run_scan
    run_scan()

    # Assertions
    assert mock_fetch.call_count == 3
    assert mock_calc_indicators.call_count == 3
    assert mock_check_cross.call_count == 2 # Not called for BAD.SR
    assert mock_approaching_cross.call_count == 2 # Called for successful SMA calcs
    mock_send_email.assert_called_once()
    # Check email content
    call_args, call_kwargs = mock_send_email.call_args
    assert "Golden Cross Alert:" in call_kwargs["subject"]
    assert "GOOD.SR" in call_kwargs["body"]
    assert "BAD.SR" not in call_kwargs["body"]
    assert "GOOD2.SR" in call_kwargs["body"]

# Test case: Unexpected exception during processing
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_unexpected_exception(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests that the scan continues if an unexpected exception occurs for one symbol."""
    mock_settings.STOCK_SYMBOLS = ["GOOD.SR", "BAD.SR", "GOOD2.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200

    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data
    # Simulate exception during check_cross for BAD.SR
    mock_check_cross.side_effect = [True, Exception("Test Error"), True]
    mock_approaching_cross.side_effect = [False, False] # Called for successful symbols

    from main import run_scan
    run_scan()

    # Assertions
    assert mock_fetch.call_count == 3
    assert mock_calc_indicators.call_count == 3
    assert mock_check_cross.call_count == 3 # Called for all, but raises on second
    assert mock_approaching_cross.call_count == 2 # Called for successful symbols
    mock_send_email.assert_called_once()
    # Check email content - only GOOD symbols should be included
    call_args, call_kwargs = mock_send_email.call_args
    assert "Golden Cross Alert:" in call_kwargs["subject"]
    assert "GOOD.SR" in call_kwargs["body"]
    assert "BAD.SR" not in call_kwargs["body"]
    assert "GOOD2.SR" in call_kwargs["body"]

# Test case: Email sending fails
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_email_fails(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests behavior when send_email returns False."""
    mock_settings.STOCK_SYMBOLS = ["TICK1.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200

    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data
    mock_check_cross.return_value = True # Trigger cross
    mock_approaching_cross.return_value = False # Not approaching
    mock_send_email.return_value = False # Simulate email failure

    from main import run_scan
    run_scan()

    # Assertions
    mock_fetch.assert_called_once_with("TICK1.SR")
    mock_calc_indicators.assert_called_once_with(mock_stock_data)
    mock_check_cross.assert_called_once_with(mock_stock_data)
    mock_approaching_cross.assert_called_once_with(mock_stock_data) # Always called
    mock_send_email.assert_called_once() # Email was attempted

# Test case: No email recipient configured
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_no_recipient(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests that email is not sent if EMAIL_RECIPIENT is not set."""
    mock_settings.STOCK_SYMBOLS = ["TICK1.SR"]
    mock_settings.EMAIL_RECIPIENT = "" # No recipient
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200

    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data
    mock_check_cross.return_value = True # Trigger cross
    mock_approaching_cross.return_value = False # Not approaching

    from main import run_scan
    run_scan()

    # Assertions
    mock_fetch.assert_called_once_with("TICK1.SR")
    mock_calc_indicators.assert_called_once_with(mock_stock_data)
    mock_check_cross.assert_called_once_with(mock_stock_data)
    mock_approaching_cross.assert_called_once_with(mock_stock_data) # Always called
    mock_send_email.assert_not_called() # Email should not be attempted


# Test case: Only approaching crosses, no actual crosses
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_only_approaching_crosses(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests run_scan with only approaching crosses, no actual crosses."""
    mock_settings.STOCK_SYMBOLS = ["TICK1.SR", "TICK2.SR", "TICK3.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200
    mock_settings.APPROACHING_THRESHOLD = 5.0
    mock_settings.TREND_DAYS = 5

    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data
    
    # No golden crosses, but some approaching crosses
    mock_check_cross.return_value = False
    mock_approaching_cross.side_effect = [True, False, True]

    from main import run_scan
    run_scan()

    # Assertions
    assert mock_fetch.call_count == 3
    assert mock_calc_indicators.call_count == 3
    assert mock_check_cross.call_count == 3
    assert mock_approaching_cross.call_count == 3
    mock_send_email.assert_called_once()
    
    # Check email content
    call_args, call_kwargs = mock_send_email.call_args
    assert "Golden Cross Alert: 2 Symbol(s) Approaching" in call_kwargs["subject"]
    assert "approaching a Golden Cross" in call_kwargs["body"]
    assert "TICK1.SR" in call_kwargs["body"]
    assert "TICK2.SR" not in call_kwargs["body"]
    assert "TICK3.SR" in call_kwargs["body"]
    assert call_kwargs["recipient"] == "test@example.com"


# Test case: Both actual crosses and approaching crosses
@patch("main.settings")
@patch("main.fetch_stock_data")
@patch("main.calculate_indicators")
@patch("main.check_golden_cross")
@patch("main.check_approaching_golden_cross")
@patch("main.send_email")
def test_run_scan_mixed_crosses(mock_send_email, mock_approaching_cross, mock_check_cross, mock_calc_indicators, mock_fetch, mock_settings, mock_stock_data):
    """Tests run_scan with a mix of actual crosses and approaching crosses."""
    mock_settings.STOCK_SYMBOLS = ["TICK1.SR", "TICK2.SR", "TICK3.SR", "TICK4.SR"]
    mock_settings.EMAIL_RECIPIENT = "test@example.com"
    mock_settings.SHORT_SMA_WINDOW = 50
    mock_settings.LONG_SMA_WINDOW = 200
    mock_settings.APPROACHING_THRESHOLD = 5.0
    mock_settings.TREND_DAYS = 5

    mock_fetch.return_value = mock_stock_data
    mock_calc_indicators.return_value = mock_stock_data
    
    # TICK1: golden cross, TICK2: no cross, TICK3: approaching, TICK4: golden cross
    mock_check_cross.side_effect = [True, False, False, True]
    # Called for all symbols
    mock_approaching_cross.side_effect = [False, False, True, False]

    from main import run_scan
    run_scan()

    # Assertions
    assert mock_fetch.call_count == 4
    assert mock_calc_indicators.call_count == 4
    assert mock_check_cross.call_count == 4
    assert mock_approaching_cross.call_count == 4 # Called for all symbols
    mock_send_email.assert_called_once()
    
    # Check email content
    call_args, call_kwargs = mock_send_email.call_args
    assert "2 Crossed, 1 Approaching" in call_kwargs["subject"]
    assert "Golden Cross patterns were detected" in call_kwargs["body"]
    assert "approaching a Golden Cross" in call_kwargs["body"]
    assert "TICK1.SR" in call_kwargs["body"]
    assert "TICK2.SR" not in call_kwargs["body"]
    assert "TICK3.SR" in call_kwargs["body"]
    assert "TICK4.SR" in call_kwargs["body"]