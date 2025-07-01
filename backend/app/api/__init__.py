"""
DocSynapse API Routes

This module exports all API routers for the FastAPI application.
"""

from .health import router as health_router
from .crawl import router as crawl_router
from .files import router as files_router
from .websocket import router as websocket_router

__all__ = [
    "health_router",
    "crawl_router",
    "files_router",
    "websocket_router",
]
