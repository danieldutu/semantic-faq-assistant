from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

# API Key header
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_token(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency function to validate API token.

    Args:
        api_key: The API key from the Authorization header

    Returns:
        The validated API key

    Raises:
        HTTPException: If the API key is missing or invalid
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide it in the 'Authorization' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Remove 'Bearer ' prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    # Validate against the configured API secret key
    if api_key != settings.api_secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key
