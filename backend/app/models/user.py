"""User database model."""

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.Database_Connection_ORM import Base


class User(Base):
    """
    User model representing an authenticated user within a tenant.

    Attributes:
        id: Unique identifier for the user
        tenant_id: Foreign key to the tenant this user belongs to
        keycloak_user_id: Unique Keycloak user identifier (sub claim from JWT)
        email: User's email address
        first_name: User's first name
        last_name: User's last name
        department: Department identifier matching tenant identifier
        status: Current status of the user (active/inactive)
        last_login: Timestamp of the user's last login
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
        tenant: Relationship to Tenant model
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    keycloak_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    department = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active")
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, department={self.department})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary representation."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "keycloak_user_id": self.keycloak_user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "department": self.department,
            "status": self.status,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
