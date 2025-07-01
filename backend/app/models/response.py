"""
DocSynapse Response Models

Standard response models for API endpoints.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .crawler import JobStatus, CrawlJobSummary


class HealthStatus(str, Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Health check response model."""
    status: HealthStatus
    timestamp: datetime
    version: str
    uptime: float  # seconds
    checks: Dict[str, bool] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JobResponse(BaseModel):
    """Response for job creation and status requests."""
    job_id: str
    status: JobStatus
    message: str
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileInfo(BaseModel):
    """Information about a generated file."""
    filename: str
    size: int  # bytes
    created_at: datetime
    download_url: str
    content_type: str = "text/markdown"
    expires_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JobListResponse(BaseModel):
    """Response for listing jobs."""
    jobs: List[CrawlJobSummary]
    total: int
    page: int = 1
    page_size: int = 20


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
