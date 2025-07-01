"""
DocSynapse WebSocket Service

This service manages WebSocket connections and real-time communication
for progress updates during crawling operations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, List
from weakref import WeakSet

from fastapi import WebSocket, WebSocketDisconnect

from app.models.websocket import (
    WSMessage, WSMessageType, ProgressUpdate, StatusChange,
    ErrorMessage, CompletionMessage, HeartbeatMessage
)
from app.models.crawler import ProgressInfo, JobStatus


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # Use WeakSet to automatically clean up closed connections
        self.active_connections: WeakSet[WebSocket] = WeakSet()
        # Map job IDs to connections interested in that job
        self.job_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connection established: {id(websocket)}")

    def disconnect(self, websocket: WebSocket, job_id: Optional[str] = None):
        """Handle WebSocket disconnection."""
        try:
            self.active_connections.discard(websocket)

            # Remove from job subscriptions
            if job_id and job_id in self.job_subscriptions:
                self.job_subscriptions[job_id].discard(websocket)
                if not self.job_subscriptions[job_id]:
                    del self.job_subscriptions[job_id]

            logger.info(f"WebSocket connection closed: {id(websocket)}")

        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")

    def subscribe_to_job(self, websocket: WebSocket, job_id: str):
        """Subscribe a WebSocket connection to job updates."""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        self.job_subscriptions[job_id].add(websocket)
        logger.info(f"WebSocket {id(websocket)} subscribed to job {job_id}")

    async def send_to_connection(self, websocket: WebSocket, message: WSMessage):
        """Send a message to a specific WebSocket connection."""
        try:
            message_data = message.dict()
            await websocket.send_text(json.dumps(message_data, default=str))

        except Exception as e:
            logger.error(f"Failed to send message to WebSocket {id(websocket)}: {e}")
            self.disconnect(websocket)

    async def send_to_job_subscribers(self, job_id: str, message: WSMessage):
        """Send a message to all subscribers of a specific job."""
        if job_id not in self.job_subscriptions:
            return

        disconnected_connections = []

        for websocket in self.job_subscriptions[job_id].copy():
            try:
                await self.send_to_connection(websocket, message)

            except Exception as e:
                logger.warning(f"Failed to send to subscriber, removing: {e}")
                disconnected_connections.append(websocket)

        # Clean up failed connections
        for websocket in disconnected_connections:
            self.disconnect(websocket, job_id)

    async def broadcast(self, message: WSMessage):
        """Broadcast a message to all active connections."""
        disconnected_connections = []

        for websocket in list(self.active_connections):
            try:
                await self.send_to_connection(websocket, message)

            except Exception as e:
                logger.warning(f"Failed to broadcast to connection, removing: {e}")
                disconnected_connections.append(websocket)

        # Clean up failed connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_job_subscriber_count(self, job_id: str) -> int:
        """Get the number of subscribers for a specific job."""
        return len(self.job_subscriptions.get(job_id, set()))


class WebSocketService:
    """
    Service for managing WebSocket communication and real-time updates.

    Handles connection management, message broadcasting, and progress updates
    for crawling operations.
    """

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # seconds

    async def start_heartbeat(self):
        """Start the heartbeat task for keeping connections alive."""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("WebSocket heartbeat started")

    async def stop_heartbeat(self):
        """Stop the heartbeat task."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("WebSocket heartbeat stopped")

    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages to maintain connections."""
        while True:
            try:
                if self.connection_manager.get_connection_count() > 0:
                    heartbeat = HeartbeatMessage(
                        job_id="system",
                        server_time=datetime.utcnow()
                    )
                    await self.connection_manager.broadcast(heartbeat)

                await asyncio.sleep(self._heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def handle_connection(self, websocket: WebSocket, job_id: Optional[str] = None):
        """
        Handle a new WebSocket connection with optional job subscription.

        Args:
            websocket: The WebSocket connection
            job_id: Optional job ID to subscribe to
        """
        await self.connection_manager.connect(websocket)

        # Subscribe to job updates if job_id provided
        if job_id:
            self.connection_manager.subscribe_to_job(websocket, job_id)

        try:
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Handle client messages (like subscription requests)
                    await self._handle_client_message(websocket, message)

                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from WebSocket {id(websocket)}")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    break

        finally:
            self.connection_manager.disconnect(websocket, job_id)

    async def _handle_client_message(self, websocket: WebSocket, message: dict):
        """Handle messages received from clients."""
        try:
            message_type = message.get('type')

            if message_type == 'subscribe':
                job_id = message.get('job_id')
                if job_id:
                    self.connection_manager.subscribe_to_job(websocket, job_id)

            elif message_type == 'ping':
                # Respond to ping with pong
                pong_message = {
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(pong_message))

        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def send_progress_update(self, job_id: str, progress: ProgressInfo, operation: Optional[str] = None):
        """Send a progress update to job subscribers."""
        update = ProgressUpdate(
            job_id=job_id,
            progress=progress,
            current_operation=operation
        )
        await self.connection_manager.send_to_job_subscribers(job_id, update)

    async def send_status_change(self, job_id: str, old_status: JobStatus, new_status: JobStatus, message: Optional[str] = None):
        """Send a status change notification to job subscribers."""
        status_change = StatusChange(
            job_id=job_id,
            old_status=old_status,
            new_status=new_status,
            message=message
        )
        await self.connection_manager.send_to_job_subscribers(job_id, status_change)

    async def send_error(self, job_id: str, error_code: str, error_message: str, details: Optional[dict] = None, is_fatal: bool = False):
        """Send an error message to job subscribers."""
        error = ErrorMessage(
            job_id=job_id,
            error_code=error_code,
            error_message=error_message,
            details=details,
            is_fatal=is_fatal
        )
        await self.connection_manager.send_to_job_subscribers(job_id, error)

    async def send_completion(self, job_id: str, success: bool, file_info: Optional[dict] = None, summary: Optional[dict] = None, message: str = "Job completed"):
        """Send a completion message to job subscribers."""
        completion = CompletionMessage(
            job_id=job_id,
            success=success,
            file_info=file_info,
            summary=summary,
            message=message
        )
        await self.connection_manager.send_to_job_subscribers(job_id, completion)

    def get_stats(self) -> dict:
        """Get WebSocket service statistics."""
        return {
            'active_connections': self.connection_manager.get_connection_count(),
            'job_subscriptions': len(self.connection_manager.job_subscriptions),
            'heartbeat_active': self._heartbeat_task is not None and not self._heartbeat_task.done()
        }
