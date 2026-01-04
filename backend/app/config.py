"""Application configuration settings."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL database connection URL
        KEYCLOAK_URL: Keycloak server URL
        KEYCLOAK_REALM: Keycloak realm name
        KEYCLOAK_CLIENT_ID: Keycloak client ID for backend
        KEYCLOAK_CLIENT_SECRET: Keycloak client secret for backend
        APP_HOST: Application host address
        APP_PORT: Application port
        CORS_ORIGINS: Comma-separated list of allowed CORS origins
        OAUTH_REDIRECT_URI: OAuth2 redirect URI after authentication
    """

    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "multitenantauth"

    # Keycloak settings
    KEYCLOAK_URL: str = "http://localhost:8080"  # URL interna (para server-to-server)
    KEYCLOAK_PUBLIC_URL: str = "http://localhost/auth/keycloak"  # URL pública (para el navegador)
    KEYCLOAK_REALM: str = "multi-tenant-app"
    KEYCLOAK_CLIENT_ID: str = "fastapi-backend"
    KEYCLOAK_CLIENT_SECRET: str

    # Application settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000"
    OAUTH_REDIRECT_URI: str = "http://localhost:3000/auth/callback"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def token_url(self) -> str:
        """Keycloak token endpoint URL."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/token"

    @property
    def auth_url(self) -> str:
        """Keycloak authorization endpoint URL (pública para el navegador)."""
        return f"{self.KEYCLOAK_PUBLIC_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/auth"

    @property
    def logout_url(self) -> str:
        """Keycloak logout endpoint URL."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/logout"

    @property
    def certs_url(self) -> str:
        """Keycloak certs endpoint URL for JWT validation."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"

    @property
    def userinfo_url(self) -> str:
        """Keycloak userinfo endpoint URL."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
    
    @property
    def KEYCLOAK_ISSUER(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
