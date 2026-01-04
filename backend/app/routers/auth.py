"""Authentication router with OAuth2 endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from urllib.parse import urlencode
import logging

from app.dependencies import get_db, get_current_user
from app.services.keycloak_service import keycloak_service
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    IdentifyTenantRequest,
    IdentifyTenantResponse,
    CallbackRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    LogoutResponse,
)
from app.schemas.user import UserResponse, TenantResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/identify-tenant",
    response_model=IdentifyTenantResponse,
    summary="Identify tenant by department",
    description="Identifies the tenant based on department identifier and returns Keycloak auth URL",
)
async def identify_tenant(
    request: IdentifyTenantRequest, db: Session = Depends(get_db)
) -> IdentifyTenantResponse:
    """
    Identify tenant by department and generate Keycloak authentication URL.

    Args:
        request: Contains department identifier
        db: Database session

    Returns:
        IdentifyTenantResponse with tenant info and Keycloak auth URL
    """
    try:
        # Find tenant by identifier (department)
        tenant = (
            db.query(Tenant)
            .filter(
                Tenant.identifier == request.department, Tenant.status == "active"
            )
            .first()
        )

        if not tenant:
            logger.warning(f"Tenant not found for department: {request.department}")
            return IdentifyTenantResponse(
                tenant_found=False,
                tenant_name=None,
                tenant_id=None,
                keycloak_auth_url=None,
            )

        # Build Keycloak authorization URL with IDP hint
        auth_params = {
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "kc_idp_hint": tenant.keycloak_idp_alias,
        }
        keycloak_auth_url = f"{settings.auth_url}?{urlencode(auth_params)}"

        logger.info(
            f"Tenant identified: {tenant.name} for department: {request.department}"
        )

        return IdentifyTenantResponse(
            tenant_found=True,
            tenant_name=tenant.name,
            tenant_id=str(tenant.id),
            keycloak_auth_url=keycloak_auth_url,
        )

    except Exception as e:
        logger.error(f"Error identifying tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to identify tenant: {str(e)}",
        )


@router.post(
    "/callback",
    response_model=TokenResponse,
    summary="OAuth2 callback handler",
    description="Exchanges authorization code for tokens and creates/updates user",
)
async def callback(
    request: CallbackRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Handle OAuth2 callback by exchanging code for tokens and managing user.

    Args:
        request: Contains authorization code
        db: Database session

    Returns:
        TokenResponse with access token, refresh token, and user info
    """
    try:
        # Exchange authorization code for tokens
        token_data = await keycloak_service.exchange_code_for_token(
            code=request.code, redirect_uri=settings.OAUTH_REDIRECT_URI
        )

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 300)

        # Decode token to get user info
        decoded_token = await keycloak_service.decode_token(access_token)

        # Extract user information from token
        keycloak_user_id = decoded_token.get("sub")
        email = decoded_token.get("email")
        first_name = decoded_token.get("given_name")
        last_name = decoded_token.get("family_name")
        department = "tenant-a"  # Department from Azure AD

        if not keycloak_user_id or not email or not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required user information in token",
            )

        # Find tenant by department identifier
        tenant = (
            db.query(Tenant)
            .filter(Tenant.identifier == department, Tenant.status == "active")
            .first()
        )

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active tenant found for department: {department}",
            )

        # Find or create user
        user = (
            db.query(User).filter(User.keycloak_user_id == keycloak_user_id).first()
        )

        if user:
            # Update existing user
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.department = department
            user.tenant_id = tenant.id
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            logger.info(f"Updated existing user: {email}")
        else:
            # Create new user
            user = User(
                tenant_id=tenant.id,
                keycloak_user_id=keycloak_user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                department=department,
                status="active",
                last_login=datetime.utcnow(),
            )
            db.add(user)
            logger.info(f"Created new user: {email}")

        db.commit()
        db.refresh(user)

        # Prepare user response with tenant info
        tenant_response = TenantResponse(
            id=str(tenant.id),
            name=tenant.name,
            identifier=tenant.identifier,
            keycloak_idp_alias=tenant.keycloak_idp_alias,
            status=tenant.status,
        )

        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            department=user.department,
            status=user.status,
            last_login=user.last_login.isoformat() if user.last_login else None,
            tenant=tenant_response,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Callback processing failed: {str(e)}",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchanges refresh token for new access and refresh tokens",
)
async def refresh(
    request: RefreshTokenRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Args:
        request: Contains refresh token
        db: Database session

    Returns:
        TokenResponse with new access token, refresh token, and user info
    """
    try:
        # Refresh the access token
        token_data = await keycloak_service.refresh_access_token(request.refresh_token)

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 300)

        # Decode new token to get user info
        decoded_token = await keycloak_service.decode_token(access_token)
        keycloak_user_id = decoded_token.get("sub")

        # Find user in database
        user = (
            db.query(User).filter(User.keycloak_user_id == keycloak_user_id).first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        # Get tenant info
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()

        tenant_response = TenantResponse(
            id=str(tenant.id),
            name=tenant.name,
            identifier=tenant.identifier,
            keycloak_idp_alias=tenant.keycloak_idp_alias,
            status=tenant.status,
        )

        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            department=user.department,
            status=user.status,
            last_login=user.last_login.isoformat() if user.last_login else None,
            tenant=tenant_response,
        )

        logger.info(f"Token refreshed for user: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout user",
    description="Revokes refresh token and logs out user from Keycloak",
)
async def logout(
    request: LogoutRequest, current_user: User = Depends(get_current_user)
) -> LogoutResponse:
    """
    Logout user by revoking refresh token.

    Args:
        request: Contains refresh token to revoke
        current_user: Authenticated user from token

    Returns:
        LogoutResponse with success message
    """
    try:
        # Revoke the refresh token in Keycloak
        await keycloak_service.revoke_token(request.refresh_token)

        logger.info(f"User logged out: {current_user.email}")

        return LogoutResponse(message="Logged out successfully")

    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns information about the authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Authenticated user from token
        db: Database session

    Returns:
        UserResponse with user and tenant information
    """
    try:
        # Get tenant info
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        tenant_response = TenantResponse(
            id=str(tenant.id),
            name=tenant.name,
            identifier=tenant.identifier,
            keycloak_idp_alias=tenant.keycloak_idp_alias,
            status=tenant.status,
        )

        user_response = UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            department=current_user.department,
            status=current_user.status,
            last_login=current_user.last_login.isoformat()
            if current_user.last_login
            else None,
            tenant=tenant_response,
        )

        logger.info(f"User info retrieved: {current_user.email}")

        return user_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user info: {str(e)}",
        )
