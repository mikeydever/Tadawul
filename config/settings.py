"""
Configuration loader for the KSA Golden Cross Scanner.

Loads settings from environment variables using python-dotenv.
Requires a .env file in the project root or environment variables
to be set externally.
"""

import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
# Searches parent directories for .env file starting from current file's location
env_path = Path(__file__).parent.parent / ".env"
if env_path.is_file():
    load_dotenv(dotenv_path=env_path, verbose=True)
    logger.info(f"Loaded environment variables from: {env_path}")
else:
    logger.info(
        ".env file not found. Relying on environment variables set externally."
    )


def get_env_variable(var_name: str, default: str | None = None) -> str:
    """
    Retrieves an environment variable.

    Args:
        var_name: The name of the environment variable.
        default: The default value if the variable is not found.

    Returns:
        The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set and no default is provided.
    """
    value = os.getenv(var_name, default)
    if value is None:
        error_msg = f"Error: Environment variable '{var_name}' not set."
        logger.error(error_msg)
        raise ValueError(error_msg)
    return value


# --- Email Settings ---
try:
    EMAIL_HOST: str = get_env_variable("EMAIL_HOST")
    EMAIL_PORT_STR: str = get_env_variable("EMAIL_PORT", "587") # Default SMTP TLS port
    EMAIL_PORT: int = int(EMAIL_PORT_STR)
    EMAIL_USER: str = get_env_variable("EMAIL_USER")
    EMAIL_PASSWORD: str = get_env_variable("EMAIL_PASSWORD")
    EMAIL_RECIPIENT: str = get_env_variable("EMAIL_RECIPIENT")
    EMAIL_SENDER_NAME: str = get_env_variable("EMAIL_SENDER_NAME", "Golden Cross Alert")
except ValueError:
    logger.warning(
        "One or more email environment variables are not set. "
        "Email notifications will fail."
    )
    # Assign dummy values or handle appropriately if email is optional
    EMAIL_HOST = ""
    EMAIL_PORT = 0
    EMAIL_USER = ""
    EMAIL_PASSWORD = ""
    EMAIL_RECIPIENT = ""
    EMAIL_SENDER_NAME = "Golden Cross Alert"
except ValueError as e:
    logger.error(f"Invalid value for EMAIL_PORT: {e}")
    raise # Re-raise if port conversion fails

# --- Stock Settings ---
def load_stock_symbols(file_path: Path) -> List[str]:
    """
    Loads stock symbols from a text file.

    Expects one symbol per line. Lines starting with '#' are ignored.
    Empty lines are ignored. Whitespace is stripped from symbols.

    Args:
        file_path: The path to the text file containing stock symbols.

    Returns:
        A list of stock symbols. Returns an empty list if the file
        is not found or cannot be read.
    """
    symbols = []
    if not file_path.is_file():
        logger.warning(f"Stock symbols file not found: {file_path}. No stocks will be scanned.")
        return symbols
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    symbols.append(line)
        logger.info(f"Loaded {len(symbols)} stock symbols from {file_path}.")
    except IOError as e:
        logger.error(f"Error reading stock symbols file {file_path}: {e}", exc_info=True)
        # Return empty list on error
        return []
    
    if not symbols:
         logger.warning(f"No valid stock symbols found in {file_path}.")

    return symbols

# Load stock symbols from stocks.txt in the project root
stocks_file_path = Path(__file__).parent.parent / "stocks.txt"
STOCK_SYMBOLS: List[str] = load_stock_symbols(stocks_file_path)

# --- Analysis Settings ---
SHORT_SMA_WINDOW: int = 50
LONG_SMA_WINDOW: int = 200
DATA_FETCH_DAYS: int = 300 # Fetch enough data for 200-day SMA + buffer

# --- Golden Cross Settings ---
# Threshold for "approaching" golden cross (as percentage)
# When short SMA is within this percentage of long SMA, it's considered "approaching"
APPROACHING_THRESHOLD: float = 5.0  # 5% threshold

# Number of days to check for upward trend in short SMA
TREND_DAYS: int = 5  # Check if short SMA has been rising for this many days

logger.info(f"Configuration loaded successfully. {len(STOCK_SYMBOLS)} stocks to scan.")

# You can add more settings here as needed