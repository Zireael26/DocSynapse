"""
DocSynapse WebSocket Models

Models for WebSocket communication and real-time updates.
"""

from enum import Enum
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

from .crawler import JobStatus, ProgressInfo


class WSMessageType(str, Enum):
    """WebSocket message types."""
    PROGRESS_UPDATE = "progress_update"
    ERROR = "error"
    COMPLETION = "completion"
    STATUS_CHANGE = "status_change"
    HEARTBEAT = "heartbeat"


class WSMessage(BaseModel):
    """Base WebSocket message model."""
    type: WSMessageType
    job_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProgressUpdate(WSMessage):
    """Progress update WebSocket message."""
    type: WSMessageType = WSMessageType.PROGRESS_UPDATE
    progress: ProgressInfo
    current_operation: Optional[str] = None


class StatusChange(WSMessage):
    """Status change WebSocket message."""
    type: WSMessageType = WSMessageType.STATUS_CHANGE
    old_status: JobStatus
    new_status: JobStatus
    message: Optional[str] = None


class ErrorMessage(WSMessage):
    """Error WebSocket message."""
    type: WSMessageType = WSMessageType.ERROR
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    is_fatal: bool = False


class CompletionMessage(WSMessage):
    """Completion WebSocket message."""
    type: WSMessageType = WSMessageType.COMPLETION
    success: bool
    file_info: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    message: str = "Job completed successfully"


class HeartbeatMessage(WSMessage):
    """Heartbeat WebSocket message."""
    type: WSMessageType = WSMessageType.HEARTBEAT
    server_time: datetime = Field(default_factory=datetime.utcnow)


# Union type for all possible WebSocket messages
WSMessageUnion = Union[
    ProgressUpdate,
    StatusChange,
    ErrorMessage,
    CompletionMessage,
    HeartbeatMessage
]
