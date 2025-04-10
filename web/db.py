"""
Database engine and session management using SQLModel.
"""

import logging
from typing import Generator, Optional

from sqlmodel import Session, SQLModel, create_engine

from config.settings import DATABASE_URL
import web.models # Import models to register metadata before create_all

logger = logging.getLogger(__name__)

# Create the database engine
# connect_args is specific to SQLite to allow multiple threads (like FastAPI requests)
# to interact with the same connection. Check_same_thread=False is generally safe
# for SQLite when used with a proper session management pattern like FastAPI's
# dependency injection, where each request gets its own session.
# For other databases like PostgreSQL, connect_args might not be needed or different.
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

try:
    engine = create_engine(DATABASE_URL, echo=False, **engine_args) # echo=True for debugging SQL
    logger.info("Database engine created successfully.")
except Exception as e:
    logger.critical(f"Failed to create database engine: {e}", exc_info=True)
    # Depending on the application, you might want to exit or raise here
    raise


def create_db_and_tables():
    """
    Creates all tables defined by SQLModel models that inherit from SQLModel.
    Should be called once on application startup.
    NOTE: For production/complex scenarios, Alembic migrations are preferred.
    """
    logger.info("Attempting to create database tables (if they don't exist)...")
    try:
        # SQLModel.metadata.create_all() requires models to be imported somewhere
        # before this call so that their metadata is registered.
        # Consider importing models here or ensuring they are imported in the main app.
        # Example: from web.models import User # Import your models here
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables checked/created.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)
        raise


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session.

    Yields:
        A SQLAlchemy Session object.
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit() # Commit changes if no exceptions occurred
        except Exception:
            session.rollback() # Rollback on error
            raise
        finally:
            session.close() # Close the session

def get_user_by_email(email: str, db: Session) -> Optional[web.models.User]:
    """
    Retrieve a user by email from the database.

    Args:
        email: The email of the user to retrieve.
        db: The database session.

    Returns:
        The User object if found, otherwise None.
    """
    try:
        user = db.exec(select(web.models.User).where(web.models.User.email == email)).first()
        return user
    except Exception as e:
        logger.error(f"Error retrieving user by email {email}: {e}", exc_info=True)
        return None


# Example of how to use get_db in a FastAPI route:
# from fastapi import Depends, FastAPI
# from sqlmodel import Session, select
# from .db import get_db
# from .models import YourModel # Assuming you have models defined
#
# app = FastAPI()
#
# @app.get("/items/")
# def read_items(db: Session = Depends(get_db)):
#     items = db.exec(select(YourModel)).all()
#     return items