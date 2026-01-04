"""Keycloak integration service for OAuth2 and JWT operations."""

import httpx
import logging
from jose import jwt, JWTError
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)


class KeycloakService:
    """
    Service class for interacting with Keycloak OpenID Connect endpoints.

    Handles token exchange, validation, refresh, and revocation operations.
    """

    def __init__(self):
        self._public_key: Optional[str] = None
        self._public_key_expiry: Optional[datetime] = None
        self._public_key_cache_duration = timedelta(hours=1)

    async def exchange_code_for_token(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange OAuth2 authorization code for access and refresh tokens.

        Args:
            code: Authorization code from Keycloak
            redirect_uri: Redirect URI used in the authorization request

        Returns:
            Dict containing access_token, refresh_token, expires_in, etc.

        Raises:
            HTTPException: If token exchange fails
        """
        try:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.KEYCLOAK_CLIENT_ID,
                "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.token_url, data=data, timeout=10.0
                )
                response.raise_for_status()
                token_data = response.json()

                logger.info("Successfully exchanged authorization code for tokens")
                return token_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token exchange: {e.response.text}")
            raise Exception(f"Token exchange failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            raise Exception(f"Token exchange failed: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict containing new access_token, refresh_token, expires_in, etc.

        Raises:
            HTTPException: If token refresh fails
        """
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.KEYCLOAK_CLIENT_ID,
                "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.token_url, data=data, timeout=10.0
                )
                response.raise_for_status()
                token_data = response.json()

                logger.info("Successfully refreshed access token")
                return token_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token refresh: {e.response.text}")
            raise Exception(f"Token refresh failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise Exception(f"Token refresh failed: {str(e)}")

    async def revoke_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token during logout.

        Args:
            refresh_token: Refresh token to revoke

        Returns:
            bool: True if revocation successful

        Raises:
            HTTPException: If token revocation fails
        """
        try:
            data = {
                "token": refresh_token,
                "client_id": settings.KEYCLOAK_CLIENT_ID,
                "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.logout_url, data=data, timeout=10.0
                )
                response.raise_for_status()

                logger.info("Successfully revoked refresh token")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token revocation: {e.response.text}")
            raise Exception(f"Token revocation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            raise Exception(f"Token revocation failed: {str(e)}")

    async def decode_token(self, token: str) -> Dict[str, Any]:
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

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Retrieve user information from Keycloak userinfo endpoint.

        Args:
            access_token: Valid access token

        Returns:
            Dict containing user information from Keycloak

        Raises:
            HTTPException: If userinfo request fails
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.userinfo_url, headers=headers, timeout=10.0
                )
                response.raise_for_status()
                user_info = response.json()

                logger.info(
                    f"Successfully retrieved user info for: {user_info.get('email')}"
                )
                return user_info

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching user info: {e.response.text}")
            raise Exception(f"Failed to fetch user info: {e.response.text}")
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}")
            raise Exception(f"Failed to fetch user info: {str(e)}")


# Singleton instance
keycloak_service = KeycloakService()
