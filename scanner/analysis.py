"""
Performs technical analysis calculations, specifically Simple Moving Averages (SMAs),
Golden Cross detection, and approaching Golden Cross detection.
"""

import logging
import numpy as np
import pandas as pd

from config import settings # Import window settings

logger = logging.getLogger(__name__)


def calculate_smas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates short-term and long-term Simple Moving Averages (SMAs).

    Adds 'SMA_short' and 'SMA_long' columns to the input DataFrame based on
    the 'Close' price and the window sizes defined in `config.settings`.

    Args:
        df: A pandas DataFrame with historical stock data, must include
            a 'Close' column and be indexed by date (ascending).

    Returns:
        The original DataFrame augmented with 'SMA_short' and 'SMA_long' columns.
        Returns the original DataFrame unmodified if 'Close' column is missing
        or if there's insufficient data for calculation.
    """
    if "Close" not in df.columns:
        logger.error("DataFrame missing 'Close' column. Cannot calculate SMAs.")
        return df # Return unmodified

    short_window = settings.SHORT_SMA_WINDOW
    long_window = settings.LONG_SMA_WINDOW

    # Use f-strings for column names based on settings
    short_sma_col = f"SMA_{short_window}"
    long_sma_col = f"SMA_{long_window}"

    if len(df) < long_window:
        logger.warning(
            f"Insufficient data ({len(df)} points) to calculate "
            f"{long_window}-day SMA. Skipping SMA calculation."
        )
        # Optionally, still calculate short SMA if enough data exists
        if len(df) >= short_window:
             df[short_sma_col] = df["Close"].rolling(window=short_window).mean()
             df[long_sma_col] = pd.NA # Or np.nan
        else:
             # Not enough data for either
             df[short_sma_col] = pd.NA
             df[long_sma_col] = pd.NA
        return df # Return potentially partially modified or unmodified

    logger.info(
        f"Calculating {short_window}-day and {long_window}-day SMAs..."
    )

    # Calculate SMAs
    df[short_sma_col] = df["Close"].rolling(window=short_window).mean()
    df[long_sma_col] = df["Close"].rolling(window=long_window).mean()

    logger.info("SMA calculation complete.")
    return df

def check_golden_cross(df: pd.DataFrame) -> bool:
    """
    Checks if a Golden Cross occurred on the most recent day of data.

    A Golden Cross occurs when the short-term SMA crosses above the
    long-term SMA. This function checks if:
    - Today: SMA_short > SMA_long
    - Yesterday: SMA_short <= SMA_long

    Args:
        df: A pandas DataFrame containing historical stock data with
            'SMA_{short_window}' and 'SMA_{long_window}' columns calculated,
            indexed by date (ascending).

    Returns:
        True if a Golden Cross occurred on the last day, False otherwise.
    """
    short_window = settings.SHORT_SMA_WINDOW
    long_window = settings.LONG_SMA_WINDOW
    short_sma_col = f"SMA_{short_window}"
    long_sma_col = f"SMA_{long_window}"

    if short_sma_col not in df.columns or long_sma_col not in df.columns:
        logger.warning(
            f"Missing SMA columns ('{short_sma_col}', '{long_sma_col}'). "
            "Cannot check for Golden Cross."
        )
        return False

    # Need at least two days of SMA data to check for a cross
    # Drop rows where *either* SMA is NaN before checking length
    df_valid_smas = df.dropna(subset=[short_sma_col, long_sma_col])
    if len(df_valid_smas) < 2:
        logger.info(
            f"Insufficient data points ({len(df_valid_smas)}) with valid SMAs "
            "to check for Golden Cross."
        )
        return False

    # Get the last two days of data where both SMAs are valid
    latest_data = df_valid_smas.iloc[-1]
    previous_data = df_valid_smas.iloc[-2]

    # Check the Golden Cross condition
    today_short_sma = latest_data[short_sma_col]
    today_long_sma = latest_data[long_sma_col]
    yesterday_short_sma = previous_data[short_sma_col]
    yesterday_long_sma = previous_data[long_sma_col]

    # Explicitly check for NaN values before comparison, although dropna should handle this
    if pd.isna(today_short_sma) or pd.isna(today_long_sma) or \
       pd.isna(yesterday_short_sma) or pd.isna(yesterday_long_sma):
        logger.warning("NaN values encountered in SMAs near the end of the series. Cannot reliably check cross.")
        return False


    golden_cross_occurred = (
        today_short_sma > today_long_sma and yesterday_short_sma <= yesterday_long_sma
    )

    if golden_cross_occurred:
        # Ensure index is datetime-like before formatting
        latest_date_str = latest_data.name.strftime('%Y-%m-%d') if hasattr(latest_data.name, 'strftime') else str(latest_data.name)
        previous_date_str = previous_data.name.strftime('%Y-%m-%d') if hasattr(previous_data.name, 'strftime') else str(previous_data.name)

        logger.info(
            f"Golden Cross detected! "
            f"Today ({latest_date_str}): "
            f"SMA{short_window}={today_short_sma:.2f}, SMA{long_window}={today_long_sma:.2f}. "
            f"Yesterday ({previous_date_str}): "
            f"SMA{short_window}={yesterday_short_sma:.2f}, SMA{long_window}={yesterday_long_sma:.2f}."
        )
    else:
         logger.debug("No Golden Cross detected on the latest date.") # Use debug level for non-events

    return bool(golden_cross_occurred)


def check_approaching_golden_cross(df: pd.DataFrame) -> bool:
    """
    Checks if a stock is approaching a Golden Cross.
    
    A stock is considered to be approaching a Golden Cross when:
    1. The short-term SMA is below but within X% of the long-term SMA
    2. The short-term SMA has been trending upward for the last N days
    
    Args:
        df: A pandas DataFrame containing historical stock data with
            'SMA_{short_window}' and 'SMA_{long_window}' columns calculated,
            indexed by date (ascending).
            
    Returns:
        True if the stock is approaching a Golden Cross, False otherwise.
    """
    short_window = settings.SHORT_SMA_WINDOW
    long_window = settings.LONG_SMA_WINDOW
    short_sma_col = f"SMA_{short_window}"
    long_sma_col = f"SMA_{long_window}"
    threshold_pct = settings.APPROACHING_THRESHOLD
    trend_days = settings.TREND_DAYS
    
    # Basic validation checks
    if short_sma_col not in df.columns or long_sma_col not in df.columns:
        logger.warning(
            f"Missing SMA columns ('{short_sma_col}', '{long_sma_col}'). "
            "Cannot check for approaching Golden Cross."
        )
        return False
    
    # Need enough data points with valid SMAs
    df_valid_smas = df.dropna(subset=[short_sma_col, long_sma_col])
    if len(df_valid_smas) < trend_days + 1:  # Need at least trend_days + 1 for trend analysis
        logger.info(
            f"Insufficient data points ({len(df_valid_smas)}) with valid SMAs "
            f"to check for approaching Golden Cross (need at least {trend_days + 1})."
        )
        return False
    
    # Get the latest data point
    latest_data = df_valid_smas.iloc[-1]
    
    # Check if a golden cross has already occurred (short SMA above long SMA)
    latest_short_sma = latest_data[short_sma_col]
    latest_long_sma = latest_data[long_sma_col]
    
    # If already crossed, it's not "approaching"
    if latest_short_sma >= latest_long_sma:
        return False
    
    # Calculate how close the short SMA is to the long SMA as a percentage
    gap_pct = ((latest_long_sma - latest_short_sma) / latest_long_sma) * 100
    
    # Check if within threshold
    within_threshold = gap_pct <= threshold_pct
    
    if not within_threshold:
        return False
    
    # Check if short SMA has been trending upward
    # Get the last trend_days+1 data points to analyze trend over trend_days periods
    trend_data = df_valid_smas.iloc[-(trend_days+1):]
    
    # Check if short SMA is consistently rising
    is_rising = True
    for i in range(1, len(trend_data)):
        if trend_data.iloc[i][short_sma_col] <= trend_data.iloc[i-1][short_sma_col]:
            is_rising = False
            break
    
    approaching_cross = within_threshold and is_rising
    
    if approaching_cross:
        latest_date_str = latest_data.name.strftime('%Y-%m-%d') if hasattr(latest_data.name, 'strftime') else str(latest_data.name)
        logger.info(
            f"Approaching Golden Cross detected! "
            f"Date: {latest_date_str}, "
            f"SMA{short_window}={latest_short_sma:.2f}, SMA{long_window}={latest_long_sma:.2f}, "
            f"Gap: {gap_pct:.2f}% (threshold: {threshold_pct}%), "
            f"Short SMA trending upward for {trend_days} days."
        )
    
    return approaching_cross


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate the Relative Strength Index (RSI).
    
    Args:
        df: A pandas DataFrame with historical stock data, must include
            a 'Close' column and be indexed by date (ascending).
        period: The period for RSI calculation (default: 14).
        
    Returns:
        The original DataFrame augmented with an 'RSI' column.
    """
    if "Close" not in df.columns:
        logger.error("DataFrame missing 'Close' column. Cannot calculate RSI.")
        return df  # Return unmodified
    
    logger.info(f"Calculating RSI with period {period}...")
    
    # Calculate price changes
    delta = df['Close'].diff()
    
    # Create gain and loss series
    gain = delta.copy()
    loss = delta.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    loss = abs(loss)
    
    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    logger.info("RSI calculation complete.")
    return df


def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    Calculate the Moving Average Convergence Divergence (MACD).
    
    Args:
        df: A pandas DataFrame with historical stock data, must include
            a 'Close' column and be indexed by date (ascending).
        fast_period: The period for the fast EMA (default: 12).
        slow_period: The period for the slow EMA (default: 26).
        signal_period: The period for the signal line (default: 9).
        
    Returns:
        The original DataFrame augmented with 'MACD', 'MACD_Signal', and 'MACD_Histogram' columns.
    """
    if "Close" not in df.columns:
        logger.error("DataFrame missing 'Close' column. Cannot calculate MACD.")
        return df  # Return unmodified
    
    logger.info(f"Calculating MACD with fast={fast_period}, slow={slow_period}, signal={signal_period}...")
    
    # Calculate EMAs
    ema_fast = df['Close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD line
    df['MACD'] = ema_fast - ema_slow
    
    # Calculate signal line
    df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    
    # Calculate histogram
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    logger.info("MACD calculation complete.")
    return df


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.
    
    Args:
        df: A pandas DataFrame with historical stock data, must include
            a 'Close' column and be indexed by date (ascending).
        period: The period for the moving average (default: 20).
        std_dev: The number of standard deviations for the bands (default: 2.0).
        
    Returns:
        The original DataFrame augmented with 'BB_Middle', 'BB_Upper', and 'BB_Lower' columns.
    """
    if "Close" not in df.columns:
        logger.error("DataFrame missing 'Close' column. Cannot calculate Bollinger Bands.")
        return df  # Return unmodified
    
    logger.info(f"Calculating Bollinger Bands with period={period}, std_dev={std_dev}...")
    
    # Calculate middle band (SMA)
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    
    # Calculate standard deviation
    rolling_std = df['Close'].rolling(window=period).std()
    
    # Calculate upper and lower bands
    df['BB_Upper'] = df['BB_Middle'] + (rolling_std * std_dev)
    df['BB_Lower'] = df['BB_Middle'] - (rolling_std * std_dev)
    
    logger.info("Bollinger Bands calculation complete.")
    return df


def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """
    Calculate the Stochastic Oscillator.
    
    Args:
        df: A pandas DataFrame with historical stock data, must include
            'High', 'Low', and 'Close' columns and be indexed by date (ascending).
        k_period: The period for %K (default: 14).
        d_period: The period for %D (default: 3).
        
    Returns:
        The original DataFrame augmented with 'Stoch_K' and 'Stoch_D' columns.
    """
    required_columns = ['High', 'Low', 'Close']
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"DataFrame missing '{col}' column. Cannot calculate Stochastic Oscillator.")
            return df  # Return unmodified
    
    logger.info(f"Calculating Stochastic Oscillator with K={k_period}, D={d_period}...")
    
    # Calculate %K
    lowest_low = df['Low'].rolling(window=k_period).min()
    highest_high = df['High'].rolling(window=k_period).max()
    df['Stoch_K'] = 100 * ((df['Close'] - lowest_low) / (highest_high - lowest_low))
    
    # Calculate %D
    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()
    
    logger.info("Stochastic Oscillator calculation complete.")
    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators.
    
    Args:
        df: A pandas DataFrame with historical stock data, must include
            'Open', 'High', 'Low', 'Close', and 'Volume' columns and be indexed by date (ascending).
            
    Returns:
        The original DataFrame augmented with all technical indicator columns.
    """
    logger.info("Calculating technical indicators...")
    
    # Calculate SMAs first (reusing existing function)
    df = calculate_smas(df)
    
    # Calculate RSI
    df = calculate_rsi(df)
    
    # Calculate MACD
    df = calculate_macd(df)
    
    # Calculate Bollinger Bands
    df = calculate_bollinger_bands(df)
    
    # Calculate Stochastic Oscillator
    df = calculate_stochastic(df)
    
    logger.info("All technical indicators calculated.")
    return df