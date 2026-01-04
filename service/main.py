from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict, Any

from dependencies import get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service API",
    description="Protected FastAPI Service with JWT validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/service",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Public health check endpoint."""
    return {"status": "healthy", "service": "Service API is running"}


@app.get("/protected", tags=["Protected"])
async def protected_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Protected endpoint that requires valid JWT token.

    Args:
        current_user: Authenticated user claims from token

    Returns:
        User information from token
    """
    return {
        "message": "Access granted to protected resource",
        "user": {
            "id": current_user.get("sub"),
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "given_name": current_user.get("given_name"),
            "family_name": current_user.get("family_name"),
        }
    }


@app.get("/data", tags=["Data"])
async def get_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Example data endpoint protected by JWT validation.

    Args:
        current_user: Authenticated user claims from token

    Returns:
        Sample data for authenticated user
    """
    return {
        "data": [
            {"id": 1, "name": "Item 1", "description": "Sample data 1"},
            {"id": 2, "name": "Item 2", "description": "Sample data 2"},
            {"id": 3, "name": "Item 3", "description": "Sample data 3"},
        ],
        "user_email": current_user.get("email"),
    }