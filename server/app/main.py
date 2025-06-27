"""
HealthFinder API Server - Main Application

This module initializes the FastAPI application with middleware, routers,
and database connections for the HealthFinder healthcare information search platform.
"""

import os
from typing import List, Union
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger
import databases
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import routers (to be implemented)
from app.api.providers import router as providers_router
from app.api.biomcp import router as biomcp_router
from app.api.auth import router as auth_router
from app.core.config import settings
from app.core.db import get_database_url, initialize_database

# Configure loguru logger
logger.remove()
logger.add(
    "logs/healthfinder.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}",
    serialize=True,
)
logger.add(lambda msg: print(msg), level="INFO", colorize=True)

# Database setup
DATABASE_URL = get_database_url()
database = databases.Database(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Connect to database and initialize tables
    logger.info("Starting HealthFinder API server")
    await database.connect()
    await initialize_database()
    
    yield
    
    # Shutdown: Disconnect from database
    logger.info("Shutting down HealthFinder API server")
    await database.disconnect()


# Create FastAPI application
app = FastAPI(
    title="HealthFinder API",
    description="Healthcare Information Search Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for custom error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler for HTTP exceptions."""
    logger.error(f"HTTP error: {exc.detail}", extra={"status_code": exc.status_code})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "healthy", "version": "0.1.0"}


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(providers_router, prefix="/providers", tags=["Provider Finder"])
app.include_router(biomcp_router, prefix="/biomcp", tags=["BioMCP Integration"])

# Mount static files (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "HealthFinder API",
        "version": "0.1.0",
        "description": "Healthcare Information Search Platform",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
