"""
HealthFinder Database Module

This module provides database configuration and utility functions,
supporting both SQLite and PostgreSQL databases.
"""

import os
import sqlalchemy
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from databases import Database
from loguru import logger
from pathlib import Path

from app.core.config import settings

# SQLAlchemy setup
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Create database directory for SQLite if it doesn't exist
if settings.DB_TYPE == "sqlite":
    db_dir = Path("./data")
    db_dir.mkdir(exist_ok=True)


def get_database_url() -> str:
    """
    Get the database URL based on the configured database type.
    
    Returns:
        str: Database connection URL for the configured database type.
    """
    if settings.DB_TYPE == "sqlite":
        # SQLite database URL
        sqlite_path = os.path.join("data", settings.SQLITE_DB_FILE)
        return f"sqlite:///{sqlite_path}"
    elif settings.DB_TYPE == "postgres":
        # PostgreSQL database URL
        if not settings.POSTGRES_URL:
            raise ValueError("PostgreSQL URL is not configured")
        return str(settings.POSTGRES_URL)
    else:
        raise ValueError(f"Unsupported database type: {settings.DB_TYPE}")


def get_sync_engine():
    """
    Get a synchronous SQLAlchemy engine for the configured database.
    
    Returns:
        Engine: SQLAlchemy engine instance.
    """
    database_url = get_database_url()
    
    # Create engine with appropriate parameters based on database type
    if settings.DB_TYPE == "sqlite":
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    else:
        engine = create_engine(database_url, pool_pre_ping=True)
    
    return engine


# Create a SessionLocal class for dependency injection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_sync_engine())


def get_db():
    """
    Get a database session for dependency injection in FastAPI routes.
    
    Yields:
        Session: SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def initialize_database():
    """
    Initialize the database by creating all tables defined in SQLAlchemy models.
    
    This function is called during application startup.
    """
    logger.info(f"Initializing {settings.DB_TYPE} database")
    
    # Create tables if they don't exist
    engine = get_sync_engine()
    
    try:
        # Import all models here to ensure they're registered with Base
        # This will be populated as models are created
        # from app.models.user import User
        # from app.models.provider import Provider
        # Add other models as they're created
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def get_database() -> Database:
    """
    Get the database instance for use with the databases library.
    
    Returns:
        Database: Database instance for async operations.
    """
    return Database(get_database_url())


# Database models will be defined in separate files in the models directory
# Example model structure:
#
# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
#     is_active = Column(Boolean, default=True)
