"""Tenant database model."""

from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.Database_Connection_ORM import Base


class Tenant(Base):
    """
    Tenant model representing a multi-tenant organization.

    Attributes:
        id: Unique identifier for the tenant
        name: Display name of the tenant
        identifier: Unique identifier used to match with department field
        keycloak_idp_alias: Keycloak Identity Provider alias (always 'microsoft')
        status: Current status of the tenant (active/inactive)
        created_at: Timestamp when the tenant was created
        updated_at: Timestamp when the tenant was last updated
        users: Relationship to User model
    """

    __tablename__ = "tenants"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    name = Column(String(255), nullable=False)
    identifier = Column(String(255), unique=True, nullable=False, index=True)
    keycloak_idp_alias = Column(String(255), nullable=False, default="microsoft")
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, identifier={self.identifier})>"

    def to_dict(self) -> dict:
        """Convert tenant to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "identifier": self.identifier,
            "keycloak_idp_alias": self.keycloak_idp_alias,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
