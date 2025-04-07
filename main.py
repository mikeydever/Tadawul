"""
Main script for the KSA Golden Cross Scanner.

Orchestrates the process of fetching data, analyzing for golden crosses,
and sending notifications.
"""

import logging
import sys
from datetime import datetime

# Import modules after potential logging setup
try:
    from config import settings
    from notifier.email_sender import send_email
    from scanner.analysis import calculate_indicators, check_golden_cross, check_approaching_golden_cross
    from scanner.data_fetcher import fetch_stock_data
except ImportError as e:
    # Use basic print/logging if imports fail early
    print(f"ERROR: Failed to import necessary modules: {e}", file=sys.stderr)
    # Attempt to log if logging might be partially configured
    try:
        logging.getLogger(__name__).critical(f"Failed to import necessary modules: {e}", exc_info=True)
    except Exception:
        pass # Avoid further errors if logging itself fails
    sys.exit(1) # Exit if core components are missing


logger = logging.getLogger(__name__) # Get logger instance for this module


def run_scan():
    """
    Executes the golden cross scanning process for all symbols in stocks.txt.
    Collects triggers and sends a single summary email.
    """
    logger.info("--- Starting Golden Cross Scan ---")
    start_time = datetime.now()

    golden_cross_triggers = [] # List to store symbols with detected crosses
    approaching_cross_triggers = [] # List to store symbols approaching a cross

    if not settings.STOCK_SYMBOLS:
        logger.warning("No stock symbols loaded from configuration. Scan cannot proceed.")
        return

    logger.info(f"Scanning {len(settings.STOCK_SYMBOLS)} symbols: {', '.join(settings.STOCK_SYMBOLS)}")

    for symbol in settings.STOCK_SYMBOLS:
        logger.info(f"--- Processing symbol: {symbol} ---")
        try:
            # 1. Fetch Data
            stock_data = fetch_stock_data(symbol)

            if stock_data is None or stock_data.empty:
                logger.warning(f"Failed to fetch or no data available for {symbol}. Skipping analysis for this symbol.")
                continue # Skip to the next symbol

            # 2. Calculate technical indicators
            stock_data_with_indicators = calculate_indicators(stock_data)

            # Check if SMA calculation added the columns (it might not if data was insufficient)
            short_sma_col = f"SMA_{settings.SHORT_SMA_WINDOW}"
            long_sma_col = f"SMA_{settings.LONG_SMA_WINDOW}"
            if short_sma_col not in stock_data_with_indicators.columns or long_sma_col not in stock_data_with_indicators.columns:
                 logger.warning(f"SMA columns not found after calculation for {symbol}. Cannot check for cross. Skipping.")
                 continue # Skip to the next symbol

            # 3. Check for Golden Cross and Approaching Golden Cross
            is_golden_cross = check_golden_cross(stock_data_with_indicators)
            is_approaching_cross = check_approaching_golden_cross(stock_data_with_indicators)

            # 4. Collect trigger if Golden Cross detected
            if is_golden_cross:
                logger.info(f"Golden Cross detected for {symbol}!")
                golden_cross_triggers.append(symbol)
            elif is_approaching_cross:
                logger.info(f"Approaching Golden Cross detected for {symbol}!")
                approaching_cross_triggers.append(symbol)
            else:
                logger.info(f"No Golden Cross or approaching cross detected for {symbol}.")

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing {symbol}: {e}", exc_info=True)
            # Continue to the next symbol even if one fails
            continue

    # --- Summary Notification ---
    if golden_cross_triggers or approaching_cross_triggers:
        if golden_cross_triggers:
            logger.info(f"Golden Cross detected for {len(golden_cross_triggers)} symbol(s): {', '.join(golden_cross_triggers)}")
        if approaching_cross_triggers:
            logger.info(f"Approaching Golden Cross detected for {len(approaching_cross_triggers)} symbol(s): {', '.join(approaching_cross_triggers)}")

        # Prepare email subject
        if golden_cross_triggers and approaching_cross_triggers:
            subject = f"Golden Cross Alert: {len(golden_cross_triggers)} Crossed, {len(approaching_cross_triggers)} Approaching"
        elif golden_cross_triggers:
            subject = f"Golden Cross Alert: {len(golden_cross_triggers)} Symbol(s) Triggered"
        else:
            subject = f"Golden Cross Alert: {len(approaching_cross_triggers)} Symbol(s) Approaching"
        
        # Prepare email body
        body_lines = [f"Golden Cross Analysis Results for {datetime.now().strftime('%Y-%m-%d')}:\n"]
        
        # Add golden cross symbols if any
        if golden_cross_triggers:
            body_lines.append("\nGolden Cross patterns were detected for the following symbols:")
            for trigger_symbol in golden_cross_triggers:
                body_lines.append(f"- {trigger_symbol}")
        
        # Add approaching cross symbols if any
        if approaching_cross_triggers:
            body_lines.append("\nThe following symbols are approaching a Golden Cross:")
            body_lines.append(f"(Within {settings.APPROACHING_THRESHOLD}% and trending upward for {settings.TREND_DAYS} days)")
            for approaching_symbol in approaching_cross_triggers:
                body_lines.append(f"- {approaching_symbol}")

        body_lines.append("\nPlease verify these signals with further analysis.")
        body = "\n".join(body_lines)

        recipient = settings.EMAIL_RECIPIENT
        if not recipient:
            logger.warning("EMAIL_RECIPIENT is not set. Cannot send summary notification.")
        else:
            logger.info(f"Sending summary notification to {recipient}...")
            success = send_email(subject=subject, body=body, recipient=recipient)
            if success:
                logger.info("Summary notification email sent successfully.")
            else:
                logger.error("Failed to send summary notification email.")
    else:
        logger.info("No Golden Crosses or approaching crosses detected in this scan.")

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"--- Scan finished in {duration}. Processed {len(settings.STOCK_SYMBOLS)} symbols. ---")


if __name__ == "__main__":
    # This ensures the scan runs only when the script is executed directly
    run_scan()