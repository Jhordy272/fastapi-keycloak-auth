from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.db.Database_Connection_ORM import DatabaseConnectionORM, Base
from app.config import settings
from app.routers import auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Multi-Tenant Auth API...")
    logger.info(f"Keycloak URL: {settings.KEYCLOAK_URL}")
    logger.info(f"Keycloak Realm: {settings.KEYCLOAK_REALM}")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")

    # Initialize database
    db_connection = DatabaseConnectionORM()
    engine = db_connection.get_engine()

    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

    app.state.db_connection = db_connection

    yield

    logger.info("Shutting down Multi-Tenant Auth API...")
    db_connection.close()

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Tenant Auth API",
    description="FastAPI backend with Keycloak authentication for multi-tenant applications",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/api",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "multi-tenant-auth-api"}