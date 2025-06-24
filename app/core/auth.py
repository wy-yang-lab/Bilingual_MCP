"""
Authentication utilities for the MCP server.
"""
from app.core.config import settings

def verify_token(authorization: str) -> bool:
    """
    Simple token verification.
    In production, this should be more sophisticated.
    """
    if not authorization:
        return False
    
    # Extract token from "Bearer TOKEN" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return False
        return token == settings.API_TOKEN
    except ValueError:
        # Handle case where authorization doesn't have space
        return authorization == f"Bearer {settings.API_TOKEN}" 