"""Service configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Service settings loaded from environment variables.

    Attributes:
        KEYCLOAK_URL: Keycloak server URL
        KEYCLOAK_REALM: Keycloak realm name
        KEYCLOAK_CLIENT_ID: Keycloak client ID
        APP_HOST: Application host address
        APP_PORT: Application port
    """

    # Keycloak settings
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "multi-tenant-app"
    KEYCLOAK_CLIENT_ID: str = "fastapi-backend"

    # Application settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8002

    @property
    def certs_url(self) -> str:
        """Keycloak certs endpoint URL for JWT validation."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"

    @property
    def KEYCLOAK_ISSUER(self) -> str:
        """Keycloak issuer URL."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
