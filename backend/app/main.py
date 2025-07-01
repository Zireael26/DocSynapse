"""
DocSynapse - Main FastAPI Application

This module initializes the FastAPI application and configures all the necessary
middleware, routes, and lifecycle management for the DocSynapse backend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from pathlib import Path

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import health, crawl, files, websocket
from app.services.crawler_service import CrawlerService


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting DocSynapse backend...")

    # Initialize crawler service
    crawler_service = CrawlerService()
    app.state.crawler_service = crawler_service
    await crawler_service.initialize()

    # Create output directory
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    logger.info("DocSynapse backend started successfully")

    yield

    # Shutdown
    logger.info("Shutting down DocSynapse backend...")
    await crawler_service.cleanup()
    logger.info("DocSynapse backend shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Transform any software documentation into LLM-friendly formats with intelligent crawling and optimization.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving generated documentation
if os.path.exists(settings.OUTPUT_DIR):
    app.mount("/downloads", StaticFiles(directory=settings.OUTPUT_DIR), name="downloads")

# Include API routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(crawl.router, prefix="/api/crawl", tags=["Crawling"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
