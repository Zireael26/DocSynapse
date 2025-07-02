"""
DocSynapse Crawler Models

Pydantic models for crawler requests, responses, and internal data structures.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class JobStatus(str, Enum):
    """Status enumeration for crawling jobs."""
    PENDING = "pending"
    CRAWLING = "crawling"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlConfig(BaseModel):
    """Configuration options for crawling operations."""
    max_pages: int = Field(default=1000, ge=1, le=10000, description="Maximum number of pages to crawl")
    max_depth: int = Field(default=10, ge=1, le=50, description="Maximum depth to crawl from base URL")
    include_patterns: List[str] = Field(default_factory=list, description="URL patterns to include")
    exclude_patterns: List[str] = Field(default_factory=list, description="URL patterns to exclude")
    respect_robots_txt: bool = Field(default=True, description="Whether to respect robots.txt")
    delay_between_requests: float = Field(default=1.0, ge=0.1, le=10.0, description="Delay between requests in seconds")
    timeout: int = Field(default=30, ge=5, le=120, description="Request timeout in seconds")
    follow_external_links: bool = Field(default=False, description="Whether to follow external links")


class CrawlRequest(BaseModel):
    """Request model for starting a crawl operation."""
    base_url: str = Field(..., description="Base URL to start crawling from")
    config: CrawlConfig = Field(default_factory=CrawlConfig, description="Crawling configuration")

    @validator('base_url')
    def validate_url(cls, v):
        """Validate that the URL is properly formatted."""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip('/')


class ProgressInfo(BaseModel):
    """Real-time progress information for crawling operations."""
    job_id: str
    status: JobStatus
    pages_discovered: int = 0
    pages_crawled: int = 0
    pages_processed: int = 0
    current_url: Optional[str] = None
    progress_percentage: float = 0.0
    estimated_time_remaining: Optional[int] = None  # seconds
    start_time: datetime
    last_update: datetime
    errors: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PageInfo(BaseModel):
    """Information about a crawled page."""
    url: str
    title: Optional[str] = None
    content: str = ""  # Store the actual HTML content
    content_length: int = 0
    last_modified: Optional[datetime] = None
    content_type: Optional[str] = None
    status_code: int = 200
    processing_time: float = 0.0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SiteStructure(BaseModel):
    """Analyzed structure of the crawled documentation site."""
    total_pages: int
    unique_pages: int
    duplicate_pages: int
    external_links: int
    broken_links: int
    average_page_size: float
    content_types: Dict[str, int]
    depth_distribution: Dict[int, int]


class CrawlResult(BaseModel):
    """Complete result of a crawling operation."""
    job_id: str
    status: JobStatus
    base_url: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    pages: List[PageInfo] = Field(default_factory=list)
    site_structure: Optional[SiteStructure] = None
    generated_file: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CrawlJobSummary(BaseModel):
    """Summary information for a crawl job."""
    job_id: str
    status: JobStatus
    base_url: str
    created_at: datetime
    progress_percentage: float = 0.0
    pages_crawled: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
