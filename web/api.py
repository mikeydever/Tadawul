"""
FastAPI web application for the KSA Golden Cross Scanner.

Provides a web interface and API endpoints for viewing scan results,
triggering scans, and managing configuration.
"""

import json
import logging
import numpy as np
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import timedelta # Import timedelta

from fastapi import FastAPI, Request, BackgroundTasks, Depends, HTTPException, status, Header
from web.security import decode_access_token, get_email_from_token
from web.db import get_user_by_email
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # Import OAuth2 helpers
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware
import pandas as pd
from sqlmodel import SQLModel, Session, select # Import SQLModel, Session, and select

from config import settings
from scanner.analysis import calculate_indicators, check_golden_cross, check_approaching_golden_cross
from scanner.data_fetcher import fetch_stock_data
from main import run_scan # Assuming main.py has run_scan, might need adjustment if structure changed
from web.db import create_db_and_tables, get_db # Import the function and dependency
from web.models import User # Import the User model
from web.security import get_password_hash, verify_password, create_access_token, decode_access_token, get_email_from_token # Import security functions

# Configure logging
logger = logging.getLogger(__name__)


# --- Pydantic/SQLModel Schemas for User ---

class UserBase(SQLModel):
    email: str

class UserCreate(UserBase):
    password: str # Plain password received from client

class UserRead(UserBase):
    id: int
    # email: str # Inherited from UserBase
    # Exclude password hash from response

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    email: Optional[str] = None

# OAuth2 scheme (optional, but good practice for dependency injection later)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login") # Points to the login endpoint itself


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

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Called once on startup and once on shutdown.
    """
    logger.info("Application startup...")
    # Create database tables on startup
    # Note: This requires all SQLModel models to be imported somewhere
    # before this is called. Ensure models are imported in web.models or similar.
    create_db_and_tables()
    yield
    logger.info("Application shutdown.")


# Create FastAPI app with lifespan manager
app = FastAPI(
    title="Tadawul Golden Cross Alert",
    description="Web interface for the Saudi Stock Exchange (Tadawul) Golden Cross Scanner",
    version="1.0.0",
    lifespan=lifespan, # Add the lifespan manager
)

# CORS Configuration
origins = [
    "http://localhost:3000", # Allow Next.js dev server
    # Add other origins if needed (e.g., production frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
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


# --- User Authentication Endpoints ---

@app.post("/api/users/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if user already exists
    existing_user = db.exec(select(User).where(User.email == user_in.email)).first()
    if existing_user:
        logger.warning(f"Registration attempt for existing email: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash the password
    try:
        hashed_password = get_password_hash(user_in.password)
    except ValueError as e:
        logger.error(f"Password hashing failed during registration for {user_in.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process registration.",
        )

    # Create new user object
    db_user = User(email=user_in.email, hashed_password=hashed_password)

    # Add to database
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User registered successfully: {db_user.email}")
        # Return UserRead model (automatically excludes password)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during user registration for {user_in.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not register user.",
        )


@app.post("/api/users/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    Uses OAuth2PasswordRequestForm for standard username/password form data.
    """
    # 1. Find user by email (username field in the form)
    user = db.exec(select(User).where(User.email == form_data.username)).first()

    # 2. Check if user exists and verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard for token-based auth
        )

    # 3. Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    try:
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        logger.info(f"User logged in successfully: {user.email}")
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError:
        # Error during token creation
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token.",
        )



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