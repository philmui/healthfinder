"""
HealthFinder Configuration Module

This module defines the application settings and configuration,
loading values from environment variables with sensible defaults.
"""

import os
import secrets
from typing import List, Optional, Union, Dict, Any
from pydantic import field_validator, AnyHttpUrl, Field, ConfigDict
from pydantic_settings import BaseSettings


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
    DEBUG: bool = Field(default=False)
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
    POSTGRES_URL: Optional[str] = None
    
    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        """Parse DEBUG value to boolean."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return False

    @field_validator("POSTGRES_URL", mode="before")
    @classmethod
    def assemble_postgres_url(cls, v: Optional[str], info) -> Any:
        """Build PostgreSQL connection URL from individual components."""
        if isinstance(v, str) and v:
            return v

        # Access other field values from the validation info
        data = info.data if hasattr(info, 'data') else {}
        user = data.get("POSTGRES_USER", os.getenv("POSTGRES_USER", "postgres"))
        password = data.get("POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
        host = data.get("POSTGRES_SERVER", os.getenv("POSTGRES_SERVER", "localhost"))
        port = data.get("POSTGRES_PORT", os.getenv("POSTGRES_PORT", "5432"))
        db = data.get("POSTGRES_DB", os.getenv("POSTGRES_DB", "healthfinder"))

        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    # Authentication settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # OpenAI settings (for BioMCP and other AI features)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_ORG_ID: str = os.getenv("OPENAI_ORG_ID", "")
    
    # API keys for external services
    BIOMCP_API_KEY: str = os.getenv("BIOMCP_API_KEY", "")
    PUBMED_API_KEY: str = os.getenv("PUBMED_API_KEY", "")
    CLINICALTRIALS_API_KEY: str = os.getenv("CLINICALTRIALS_API_KEY", "")
    # NPPES API is public and doesn't require an API key
    PRACTO_API_KEY: str = os.getenv("PRACTO_API_KEY", "")
    PRACTO_CLIENT_ID: str = os.getenv("PRACTO_CLIENT_ID", "")
    ORPHADATA_API_KEY: str = os.getenv("ORPHADATA_API_KEY", "")
    ICD_API_KEY: str = os.getenv("ICD_API_KEY", "")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}"
    
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Create a global settings instance
settings = Settings()
