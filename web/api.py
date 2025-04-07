"""
FastAPI web application for the KSA Golden Cross Scanner.

Provides a web interface and API endpoints for viewing scan results,
triggering scans, and managing configuration.
"""

import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd

from config import settings
from scanner.analysis import calculate_indicators, check_golden_cross, check_approaching_golden_cross
from scanner.data_fetcher import fetch_stock_data
from main import run_scan

# Configure logging
logger = logging.getLogger(__name__)


# Custom JSON encoder to handle NaN values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy as np
        import pandas as pd
        
        if pd.isna(obj) or (hasattr(obj, 'isna') and obj.isna()):
            return None
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj) if not pd.isna(obj) else None
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Series):
            return obj.to_dict()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        return super().default(obj)


def safe_json_response(content: Any) -> JSONResponse:
    """Create a JSON response that safely handles NaN values."""
    json_str = json.dumps(content, cls=CustomJSONEncoder)
    return JSONResponse(content=json.loads(json_str))


# Create FastAPI app
app = FastAPI(
    title="Tadawul Golden Cross Alert",
    description="Web interface for the Saudi Stock Exchange (Tadawul) Golden Cross Scanner",
    version="1.0.0",
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="web/templates")

# Store the latest scan results in memory
latest_scan_results = {
    "golden_crosses": [],
    "approaching_crosses": [],
    "last_scan_time": None,
    "scan_duration": None,
    "is_scanning": False,
}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "latest_scan_results": latest_scan_results,
            "stock_symbols": settings.STOCK_SYMBOLS,
        },
    )


@app.get("/api/stocks", response_model=List[str])
async def get_stocks():
    """Get the list of stocks being monitored."""
    return settings.STOCK_SYMBOLS


@app.get("/api/results")
async def get_results():
    """Get the latest scan results."""
    return safe_json_response(latest_scan_results)


@app.post("/api/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    """Trigger a new scan in the background."""
    if latest_scan_results["is_scanning"]:
        return safe_json_response({"status": "error", "message": "A scan is already in progress"})
    
    background_tasks.add_task(perform_scan)
    return safe_json_response({"status": "success", "message": "Scan started"})


@app.get("/api/stock/{symbol}")
async def get_stock_data(symbol: str):
    """Get detailed data for a specific stock."""
    try:
        # Fetch stock data
        stock_data = fetch_stock_data(symbol)
        
        if stock_data is None or stock_data.empty:
            return {"status": "error", "message": f"No data available for {symbol}"}
        
        # Calculate technical indicators
        stock_data_with_indicators = calculate_indicators(stock_data)
        
        # Check for golden cross
        is_golden_cross = check_golden_cross(stock_data_with_indicators)
        is_approaching_cross = check_approaching_golden_cross(stock_data_with_indicators)
        
        # Convert DataFrame to dict for JSON response
        # Use the last 30 days of data for the chart
        chart_data = stock_data_with_indicators.tail(30).reset_index()
        
        # Convert dates to strings
        chart_data['Date'] = chart_data['Date'].dt.strftime('%Y-%m-%d')
        
        # Create a clean dictionary for JSON serialization
        chart_records = []
        for _, row in chart_data.iterrows():
            record = {}
            for col in chart_data.columns:
                value = row[col]
                # Handle different data types
                if pd.isna(value):
                    record[col] = None
                elif isinstance(value, (float, np.float64)):
                    record[col] = float(value) if not pd.isna(value) else None
                elif isinstance(value, (int, np.int64)):
                    record[col] = int(value)
                else:
                    record[col] = str(value)
            chart_records.append(record)
        
        # Create response data
        response_data = {
            "status": "success",
            "symbol": symbol,
            "is_golden_cross": is_golden_cross,
            "is_approaching_cross": is_approaching_cross,
            "chart_data": chart_records,
        }
        # Use safe_json_response to handle NaN values
        return safe_json_response(response_data)
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}", exc_info=True)
        # Provide a more user-friendly error message
        error_message = f"Error processing data for {symbol}"
        if "No data found" in str(e):
            error_message = f"No data available for {symbol}. The symbol may be invalid or there might be connectivity issues."
        elif "SMA" in str(e):
            error_message = f"Insufficient data to calculate moving averages for {symbol}."
        
        return safe_json_response({"status": "error", "message": error_message})


def perform_scan():
    """
    Perform a scan and update the latest_scan_results.
    This function is meant to be run in a background task.
    """
    global latest_scan_results
    
    try:
        latest_scan_results["is_scanning"] = True
        start_time = datetime.now()
        
        # Clear previous results
        latest_scan_results["golden_crosses"] = []
        latest_scan_results["approaching_crosses"] = []
        
        # Run the scan
        golden_cross_triggers = []
        approaching_cross_triggers = []
        
        for symbol in settings.STOCK_SYMBOLS:
            try:
                # Fetch Data
                stock_data = fetch_stock_data(symbol)
                
                if stock_data is None or stock_data.empty:
                    continue
                
                # Calculate technical indicators
                stock_data_with_indicators = calculate_indicators(stock_data)
                
                # Check for Golden Cross and Approaching Golden Cross
                is_golden_cross = check_golden_cross(stock_data_with_indicators)
                is_approaching_cross = check_approaching_golden_cross(stock_data_with_indicators)
                
                # Collect triggers
                if is_golden_cross:
                    golden_cross_triggers.append(symbol)
                elif is_approaching_cross:
                    approaching_cross_triggers.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}", exc_info=True)
                continue
        
        # Update results
        latest_scan_results["golden_crosses"] = golden_cross_triggers
        latest_scan_results["approaching_crosses"] = approaching_cross_triggers
        latest_scan_results["last_scan_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        latest_scan_results["scan_duration"] = str(datetime.now() - start_time)
        
        logger.info(f"Web scan completed. Found {len(golden_cross_triggers)} golden crosses and {len(approaching_cross_triggers)} approaching crosses.")
        
    except Exception as e:
        logger.error(f"Error during web scan: {e}", exc_info=True)
    finally:
        latest_scan_results["is_scanning"] = False


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.api:app", host="0.0.0.0", port=8000, reload=True)