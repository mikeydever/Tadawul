"""
Script to run the Tadawul Golden Cross Alert web application.

This script starts the FastAPI web server using uvicorn.
"""

import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Tadawul Golden Cross Alert web application...")
    uvicorn.run("web.api:app", host="0.0.0.0", port=8000, reload=True)