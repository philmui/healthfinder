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
from app.api.nppes import router as nppes_router
from app.api.chat import router as chat_router
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


# Include routers with consistent /api/v1 prefix
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(providers_router, prefix="/api/v1/providers", tags=["Provider Finder"])
app.include_router(nppes_router, prefix="/api/v1", tags=["NPPES NPI Registry"])
app.include_router(biomcp_router, prefix="/api/v1/biomcp", tags=["BioMCP Integration"])
app.include_router(chat_router, prefix="/api/v1", tags=["Agentic Chat Completions"])

# Mount static files (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint providing information about the HealthFinder API.
    
    Returns:
        API information and capabilities
    """
    return {
        "name": "HealthFinder API",
        "version": "0.1.0", 
        "description": "Healthcare and general information research API with agentic search capabilities",
        "docs_url": "/docs",
        "capabilities": {
            "multi_agent_workflow": "LlamaIndex AgentWorkflow with FunctionAgent orchestration",
            "research_agents": "Healthcare and general research with evidence-based analysis",
            "web_search": "Real-time information gathering with source credibility assessment", 
            "synthesis": "Intelligent information combination and analysis",
            "agent_handoff": "Seamless collaboration between specialized agents",
            "context_memory": "State management across multi-step workflows",
            "provider_search": "Healthcare provider discovery and verification",
            "nppes_integration": "National Provider Identifier registry integration",
            "provider_types": "Multiple healthcare provider specialties and types",
            "search_features": "Advanced search with filters and location-based queries"
        },
        "architecture": {
            "framework": "LlamaIndex v0.12+ with standard AgentWorkflow",
            "agents": ["ResearchAgent", "WebSearchAgent", "SynthesisAgent"],
            "tools": ["HealthcareResearchTool", "GeneralResearchTool", "DuckDuckGoSearchTool", "GoogleSearchTool"],
            "llm": "OpenAI GPT-4 with function calling",
            "patterns": ["AgentWorkflow", "FunctionAgent", "Multi-agent handoff", "SOLID principles"]
        },
        "endpoints": {
            "providers": "/api/v1/providers",
            "nppes": "/api/v1/nppes",
            "auth": "/api/v1/auth",
            "biomcp": "/api/v1/biomcp",
            "chat_completions": "/api/v1/chat/completions",
            "streaming": "/api/v1/chat/completions/stream",
            "status": "/api/v1/chat/status",
            "configuration": "/api/v1/chat/config",
            "presets": "/api/v1/chat/config/presets",
            "metrics": "/api/v1/chat/metrics",
            "health": "/api/v1/chat/health"
        },
        "features": {
            "openai_compatible": "Full OpenAI chat completions API compatibility",
            "research_depth": "Configurable research depth (1-5 levels)",
            "source_assessment": "Automatic source credibility scoring",
            "healthcare_specialization": "Medical research with evidence-based analysis",
            "general_research": "Academic and cross-domain information gathering",
            "real_time_search": "Current information via web search",
            "configuration_presets": "Healthcare, general, and fast response configurations"
        },
        "documentation": {
            "api_docs": "/docs",
            "openapi_spec": "/openapi.json",
            "health_check": "/api/v1/chat/health"
        }
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
