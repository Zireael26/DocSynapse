"""
WebSocket API Endpoints

Handles WebSocket connections for real-time progress updates.
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.services.websocket_service import WebSocketService


logger = logging.getLogger(__name__)
router = APIRouter()


def get_websocket_service() -> WebSocketService:
    """Get WebSocket service instance."""
    from app.main import app
    if not hasattr(app.state, 'websocket_service'):
        app.state.websocket_service = WebSocketService()
        # Start heartbeat when service is first created
        import asyncio
        asyncio.create_task(app.state.websocket_service.start_heartbeat())
    return app.state.websocket_service


@router.websocket("/progress")
async def websocket_progress_endpoint(
    websocket: WebSocket,
    job_id: Optional[str] = Query(None, description="Job ID to subscribe to for updates")
):
    """
    WebSocket endpoint for real-time progress updates.

    Args:
        websocket: WebSocket connection
        job_id: Optional job ID to subscribe to specific job updates
    """
    websocket_service = get_websocket_service()

    try:
        logger.info(f"New WebSocket connection for job: {job_id or 'all'}")

        # Handle the connection (this will accept it and manage it)
        await websocket_service.handle_connection(websocket, job_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job: {job_id or 'all'}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id or 'all'}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass  # Connection might already be closed


@router.websocket("/updates/{job_id}")
async def websocket_job_updates(
    websocket: WebSocket,
    job_id: str
):
    """
    WebSocket endpoint for updates on a specific job.

    Args:
        websocket: WebSocket connection
        job_id: Job ID to get updates for
    """
    websocket_service = get_websocket_service()

    try:
        logger.info(f"New WebSocket connection for job: {job_id}")

        # Handle the connection with specific job subscription
        await websocket_service.handle_connection(websocket, job_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass  # Connection might already be closed


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket service statistics.

    Returns:
        dict: WebSocket connection and subscription statistics
    """
    try:
        websocket_service = get_websocket_service()
        stats = websocket_service.get_stats()

        return {
            "websocket_stats": stats,
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }

    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {e}")
        return {
            "error": "Failed to get WebSocket stats",
            "websocket_stats": {
                "active_connections": 0,
                "job_subscriptions": 0,
                "heartbeat_active": False
            }
        }
