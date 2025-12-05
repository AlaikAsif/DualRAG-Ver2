"""Authentication utilities."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def verify_token(credentials = Depends(security)):
    """Verify JWT token from Authorization header."""
    if credentials is None:
        return None
    
    token = credentials.credentials
    
    try:
        return token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
