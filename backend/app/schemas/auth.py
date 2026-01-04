"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user import UserResponse


class IdentifyTenantRequest(BaseModel):
    """Request schema for tenant identification."""

    department: str = Field(..., description="Department identifier (e.g., tenant-a, tenant-b)")

    class Config:
        json_schema_extra = {
            "example": {
                "department": "tenant-a"
            }
        }


class IdentifyTenantResponse(BaseModel):
    """Response schema for tenant identification."""

    tenant_found: bool = Field(..., description="Whether the tenant was found")
    tenant_name: Optional[str] = Field(None, description="Display name of the tenant")
    tenant_id: Optional[str] = Field(None, description="UUID of the tenant")
    keycloak_auth_url: Optional[str] = Field(None, description="Keycloak authentication URL with IDP hint")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_found": True,
                "tenant_name": "Tenant A Corp",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "keycloak_auth_url": "http://localhost:8080/realms/multi-tenant-app/protocol/openid-connect/auth?client_id=fastapi-backend&response_type=code&redirect_uri=http://localhost:3000/auth/callback&kc_idp_hint=microsoft"
            }
        }


class CallbackRequest(BaseModel):
    """Request schema for OAuth2 callback."""

    code: str = Field(..., description="Authorization code from Keycloak")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6..."
            }
        }


class TokenResponse(BaseModel):
    """Response schema for token endpoints."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="Authenticated user information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6...",
                "token_type": "bearer",
                "expires_in": 300,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@domain.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "department": "tenant-a",
                    "tenant": {
                        "id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "Tenant A Corp",
                        "identifier": "tenant-a"
                    }
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6..."
            }
        }


class LogoutRequest(BaseModel):
    """Request schema for logout."""

    refresh_token: str = Field(..., description="Refresh token to revoke")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6..."
            }
        }


class LogoutResponse(BaseModel):
    """Response schema for logout."""

    message: str = Field(..., description="Logout confirmation message")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Logged out successfully"
            }
        }
