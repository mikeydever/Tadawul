"""
Database models defined using SQLModel.
"""

import logging
from typing import Optional

from sqlmodel import Field, SQLModel

logger = logging.getLogger(__name__)

# Define the User model
# table=True makes this model represent a database table
class User(SQLModel, table=True):
    """
    Represents a user in the database.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)

    # You can add more fields here later, e.g., is_active, created_at, etc.

# Add other models here as needed, for example:
# class UserPreferences(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     user_id: int = Field(foreign_key="user.id", index=True)
#     receive_email_alerts: bool = Field(default=True)
#     # Add other preference fields

logger.info("User model defined.")

# Note: Ensure this file (or the models within it) is imported before
# `create_db_and_tables()` is called in the application startup
# (e.g., import it in web/db.py or web/api.py).