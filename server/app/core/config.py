"""
HealthFinder Configuration Module

This module defines the application settings and configuration,
loading values from environment variables with sensible defaults.
"""

import os
import secrets
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseSettings, PostgresDsn, validator, AnyHttpUrl, Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with defaults.
    
    This class provides a centralized configuration for the HealthFinder application,
    including database connections, API keys, and general application settings.
    """
    # General application settings
    PROJECT_NAME: str = "HealthFinder"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend development server
        "http://localhost:8000",  # Backend development server
        "https://healthfinder.example.com",  # Production frontend
    ]
    
    # Database settings
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")  # "sqlite" or "postgres"
    
    # SQLite settings
    SQLITE_DB_FILE: str = os.getenv("SQLITE_DB_FILE", "healthfinder.db")
    
    # PostgreSQL settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "healthfinder")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_URL: Optional[PostgresDsn] = None
    
    @validator("POSTGRES_URL", pre=True)
    def assemble_postgres_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Build PostgreSQL connection URL from individual components."""
        if isinstance(v, str):
            return v
        
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Authentication settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # API keys for external services
    BIOMCP_API_KEY: str = os.getenv("BIOMCP_API_KEY", "")
    PUBMED_API_KEY: str = os.getenv("PUBMED_API_KEY", "")
    CLINICALTRIALS_API_KEY: str = os.getenv("CLINICALTRIALS_API_KEY", "")
    BETTERDOCTOR_API_KEY: str = os.getenv("BETTERDOCTOR_API_KEY", "")
    PRACTO_API_KEY: str = os.getenv("PRACTO_API_KEY", "")
    PRACTO_CLIENT_ID: str = os.getenv("PRACTO_CLIENT_ID", "")
    ORPHADATA_API_KEY: str = os.getenv("ORPHADATA_API_KEY", "")
    ICD_API_KEY: str = os.getenv("ICD_API_KEY", "")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}"
    
    class Config:
        """Pydantic configuration for Settings."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a global settings instance
settings = Settings()
