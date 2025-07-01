"""
Crawling API Endpoints

Handles crawling operations including starting, monitoring, and managing crawl jobs.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.crawler import CrawlRequest, CrawlResult, ProgressInfo, CrawlJobSummary
from app.models.response import JobResponse, JobListResponse, ErrorResponse
from app.services.crawler_service import CrawlerService
from app.services.processor_service import ProcessorService
from app.services.websocket_service import WebSocketService


logger = logging.getLogger(__name__)
router = APIRouter()


def get_crawler_service() -> CrawlerService:
    """Dependency to get crawler service instance."""
    # This will be injected by FastAPI dependency system
    # In a real application, this would get the service from app state
    from app.main import app
    return app.state.crawler_service


def get_processor_service() -> ProcessorService:
    """Dependency to get processor service instance."""
    # This will be injected by FastAPI dependency system
    from app.main import app
    if not hasattr(app.state, 'processor_service'):
        app.state.processor_service = ProcessorService()
    return app.state.processor_service


def get_websocket_service() -> WebSocketService:
    """Dependency to get WebSocket service instance."""
    from app.main import app
    if not hasattr(app.state, 'websocket_service'):
        app.state.websocket_service = WebSocketService()
    return app.state.websocket_service


@router.post("/start", response_model=JobResponse)
async def start_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    crawler_service: CrawlerService = Depends(get_crawler_service),
    processor_service: ProcessorService = Depends(get_processor_service),
    websocket_service: WebSocketService = Depends(get_websocket_service)
):
    """
    Start a new crawling operation.

    Args:
        request: Crawl request with URL and configuration
        background_tasks: FastAPI background tasks
        crawler_service: Crawler service instance
        processor_service: Processor service instance
        websocket_service: WebSocket service instance

    Returns:
        JobResponse: Job creation response with job ID
    """
    try:
        logger.info(f"Starting crawl for URL: {request.base_url}")

        # Start the crawling job
        job_id = await crawler_service.start_crawl(request)

        # Add background task for processing
        background_tasks.add_task(
            _monitor_and_process_job,
            job_id,
            crawler_service,
            processor_service,
            websocket_service
        )

        return JobResponse(
            job_id=job_id,
            status="pending",
            message="Crawl job started successfully",
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to start crawl: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to start crawl: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=ProgressInfo)
async def get_crawl_status(
    job_id: str,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    Get the current status of a crawling job.

    Args:
        job_id: The job ID to check
        crawler_service: Crawler service instance

    Returns:
        ProgressInfo: Current progress information
    """
    try:
        progress = await crawler_service.get_job_progress(job_id)

        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get job status"
        )


@router.get("/result/{job_id}", response_model=CrawlResult)
async def get_crawl_result(
    job_id: str,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    Get the final result of a completed crawling job.

    Args:
        job_id: The job ID to get results for
        crawler_service: Crawler service instance

    Returns:
        CrawlResult: Complete crawl results
    """
    try:
        result = await crawler_service.get_job_result(job_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Result for job {job_id} not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job result: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get job result"
        )


@router.post("/cancel/{job_id}")
async def cancel_crawl(
    job_id: str,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    Cancel an active crawling job.

    Args:
        job_id: The job ID to cancel
        crawler_service: Crawler service instance

    Returns:
        dict: Cancellation confirmation
    """
    try:
        success = await crawler_service.cancel_job(job_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found or already completed"
            )

        return {
            "success": True,
            "message": f"Job {job_id} cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel job"
        )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    List active and recent crawling jobs.

    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        crawler_service: Crawler service instance

    Returns:
        JobListResponse: List of job summaries
    """
    try:
        active_jobs = await crawler_service.list_active_jobs()

        # Convert to summaries
        job_summaries = []
        for progress in active_jobs[offset:offset + limit]:
            summary = CrawlJobSummary(
                job_id=progress.job_id,
                status=progress.status,
                base_url="",  # TODO: Add base_url to progress tracking
                created_at=progress.start_time,
                progress_percentage=progress.progress_percentage,
                pages_crawled=progress.pages_crawled
            )
            job_summaries.append(summary)

        return JobListResponse(
            jobs=job_summaries,
            total=len(active_jobs),
            page=offset // limit + 1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list jobs"
        )


async def _monitor_and_process_job(
    job_id: str,
    crawler_service: CrawlerService,
    processor_service: ProcessorService,
    websocket_service: WebSocketService
):
    """
    Background task to monitor crawling progress and process results.

    Args:
        job_id: The job ID to monitor
        crawler_service: Crawler service instance
        processor_service: Processor service instance
        websocket_service: WebSocket service instance
    """
    try:
        logger.info(f"Starting background monitoring for job {job_id}")

        # Monitor progress and send updates
        while True:
            progress = await crawler_service.get_job_progress(job_id)

            if not progress:
                logger.warning(f"Job {job_id} not found during monitoring")
                break

            # Send progress update via WebSocket
            await websocket_service.send_progress_update(
                job_id, progress, f"Processing: {progress.current_url or 'N/A'}"
            )

            # Check if job is completed
            if progress.status in ["completed", "failed", "cancelled"]:
                break

            # Wait before next check
            await asyncio.sleep(2)

        # Process results if job completed successfully
        if progress and progress.status == "completed":
            result = await crawler_service.get_job_result(job_id)

            if result:
                logger.info(f"Processing results for job {job_id}")

                try:
                    # Process the crawl result into markdown
                    file_path = await processor_service.process_crawl_result(result)

                    # Update result with file information
                    result.generated_file = file_path

                    # Send completion notification
                    await websocket_service.send_completion(
                        job_id,
                        success=True,
                        file_info={"path": file_path, "size": 0},  # TODO: Get actual file size
                        message="Crawl completed and processed successfully"
                    )

                    logger.info(f"Job {job_id} completed and processed successfully")

                except Exception as e:
                    logger.error(f"Failed to process results for job {job_id}: {e}")
                    await websocket_service.send_error(
                        job_id,
                        "PROCESSING_ERROR",
                        f"Failed to process crawl results: {str(e)}",
                        is_fatal=True
                    )

        elif progress and progress.status == "failed":
            await websocket_service.send_error(
                job_id,
                "CRAWL_FAILED",
                f"Crawling failed: {', '.join(progress.errors) if progress.errors else 'Unknown error'}",
                is_fatal=True
            )

    except Exception as e:
        logger.error(f"Error in background job monitoring for {job_id}: {e}")
        await websocket_service.send_error(
            job_id,
            "MONITOR_ERROR",
            f"Job monitoring failed: {str(e)}",
            is_fatal=True
        )
