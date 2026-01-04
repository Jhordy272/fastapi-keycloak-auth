"""
Database initialization script.

This script creates all database tables and optionally seeds initial data.

Usage:
    python init_db.py
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.Database_Connection_ORM import DatabaseConnectionORM, Base
from app.models.tenant import Tenant
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database by creating all tables."""
    try:
        logger.info("Initializing database connection...")
        db_connection = DatabaseConnectionORM()
        engine = db_connection.get_engine()

        if not engine:
            logger.error("Failed to create database engine")
            return False

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        logger.info("Database tables created successfully!")
        logger.info(f"Tables created: {', '.join(Base.metadata.tables.keys())}")

        return True

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


def seed_data():
    """Seed initial tenant data."""
    try:
        logger.info("Seeding initial data...")
        db_connection = DatabaseConnectionORM()
        session = db_connection.get_session()

        # Check if tenants already exist
        existing_tenants = session.query(Tenant).count()
        if existing_tenants > 0:
            logger.info(f"Database already has {existing_tenants} tenants. Skipping seed.")
            session.close()
            return True

        # Create tenants
        tenant_a = Tenant(
            name="Tenant A Corp",
            identifier="tenant-a",
            keycloak_idp_alias="microsoft",
            status="active",
        )

        tenant_b = Tenant(
            name="Tenant B Industries",
            identifier="tenant-b",
            keycloak_idp_alias="microsoft",
            status="active",
        )

        session.add(tenant_a)
        session.add(tenant_b)
        session.commit()

        logger.info("Seed data inserted successfully!")
        logger.info(f"Created tenant: {tenant_a.name} (ID: {tenant_a.id})")
        logger.info(f"Created tenant: {tenant_b.name} (ID: {tenant_b.id})")

        session.close()
        return True

    except Exception as e:
        logger.error(f"Error seeding data: {str(e)}")
        return False


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION SCRIPT")
    logger.info("=" * 60)

    # Display configuration
    logger.info(f"Database Host: {settings.DB_HOST}")
    logger.info(f"Database Port: {settings.DB_PORT}")
    logger.info(f"Database Name: {settings.DB_NAME}")
    logger.info(f"Database User: {settings.DB_USER}")
    logger.info("-" * 60)

    # Initialize database
    if not init_database():
        logger.error("Database initialization failed!")
        sys.exit(1)

    # Seed data
    if not seed_data():
        logger.error("Data seeding failed!")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
