"""User-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class TenantResponse(BaseModel):
    """Response schema for tenant information."""

    id: str = Field(..., description="Tenant UUID")
    name: str = Field(..., description="Tenant display name")
    identifier: str = Field(..., description="Tenant identifier (department)")
    keycloak_idp_alias: Optional[str] = Field(None, description="Keycloak IDP alias")
    status: Optional[str] = Field(None, description="Tenant status")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Tenant A Corp",
                "identifier": "tenant-a",
                "keycloak_idp_alias": "microsoft",
                "status": "active"
            }
        }


class UserResponse(BaseModel):
    """Response schema for user information."""

    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    department: str = Field(..., description="User department (tenant identifier)")
    status: Optional[str] = Field(None, description="User status")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    tenant: Optional[TenantResponse] = Field(None, description="Associated tenant information")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@domain.com",
                "first_name": "John",
                "last_name": "Doe",
                "department": "tenant-a",
                "status": "active",
                "last_login": "2025-01-03T12:00:00",
                "tenant": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "Tenant A Corp",
                    "identifier": "tenant-a",
                    "keycloak_idp_alias": "microsoft",
                    "status": "active"
                }
            }
        }
