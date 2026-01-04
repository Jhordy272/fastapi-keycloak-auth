"""FastAPI dependencies for authentication and database sessions."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Generator
import logging

from app.db.Database_Connection_ORM import DatabaseConnectionORM
from app.services.keycloak_service import keycloak_service
from app.models.user import User

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()

# Database connection instance
db_connection = DatabaseConnectionORM()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields:
        Session: SQLAlchemy database session

    Note:
        Automatically closes the session after use
    """
    db = db_connection.get_session()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the current authenticated user.

    Args:
        credentials: HTTP Authorization credentials containing Bearer token
        db: Database session

    Returns:
        User: Authenticated user object from database

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    try:
        # Decode and validate token
        decoded_token = await keycloak_service.decode_token(token)

        # Extract Keycloak user ID (sub claim)
        keycloak_user_id = decoded_token.get("sub")
        if not keycloak_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Find user in database
        user = db.query(User).filter(User.keycloak_user_id == keycloak_user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Authenticated user: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
