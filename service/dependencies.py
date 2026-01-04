"""FastAPI dependencies for JWT token validation."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
import logging
from typing import Dict, Any

from config import settings

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()


async def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token from Keycloak.

    Args:
        token: JWT access token

    Returns:
        Dict containing decoded token claims

    Raises:
        Exception: If token validation fails
    """
    try:
        async with httpx.AsyncClient() as client:
            jwks = (await client.get(settings.certs_url)).json()

        decoded = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            options={"verify_aud": False, "verify_iss": False},
        )

        logger.info(f"Successfully decoded token for user: {decoded.get('sub')}")
        return decoded

    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise Exception(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Dependency that validates JWT token and returns user claims.

    Args:
        credentials: HTTP Authorization credentials containing Bearer token

    Returns:
        Dict containing user claims from the token

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials

    try:
        # Decode and validate token
        decoded_token = await decode_token(token)

        # Extract user information
        user_id = decoded_token.get("sub")
        email = decoded_token.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Authenticated user: {email}")
        return decoded_token

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
