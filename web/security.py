"""
Security related utilities, including password hashing.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings # Import settings for JWT config

logger = logging.getLogger(__name__)

# Configure passlib context
# Using bcrypt as the default hashing algorithm
# schemes lists the allowed hashing schemes
# deprecated="auto" will automatically upgrade hashes from older schemes if found
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password from the database.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log potential errors during verification (e.g., invalid hash format)
        logger.error(f"Error verifying password: {e}", exc_info=True)
        return False

def get_password_hash(password: str) -> str:
    """
    Hashes a plain text password using the configured context (bcrypt).

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        # Log potential errors during hashing
        logger.error(f"Error hashing password: {e}", exc_info=True)
        # Depending on policy, you might want to raise the error
        # or return a specific value indicating failure. Raising is often safer.
        raise ValueError("Failed to hash password") from e

logger.info("Password hashing context configured using bcrypt.")


# --- JWT Token Handling ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.

    Args:
        data: The data to encode in the token (e.g., user identifier).
        expires_delta: Optional timedelta for token expiry. Defaults to
                       ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        The encoded JWT access token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        logger.error(f"Error encoding JWT: {e}", exc_info=True)
        raise ValueError("Could not create access token") from e

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes a JWT access token.

    Args:
        token: The JWT token string.

    Returns:
        The decoded payload dictionary if the token is valid and not expired,
        otherwise None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Check for required claims
        if "sub" not in payload:
            logger.warning("Token missing 'sub' claim")
            return None
        return payload
    except JWTError as e:
        logger.warning(f"JWT decoding error: {e}") # Log as warning, as invalid tokens are expected
        return None

def get_email_from_token(token: str) -> Optional[str]:
    """
    Extract the email (subject) from a JWT token.
    
    Args:
        token: The JWT token string.
        
    Returns:
        The email address if the token is valid, otherwise None.
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    return payload.get("sub")
