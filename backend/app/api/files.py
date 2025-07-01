"""
File Management API Endpoints

Handles serving generated files and file management operations.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from datetime import datetime

from app.core.config import settings
from app.models.response import FileInfo, SuccessResponse
from app.services.processor_service import ProcessorService


logger = logging.getLogger(__name__)
router = APIRouter()


def get_processor_service() -> ProcessorService:
    """Dependency to get processor service instance."""
    from app.main import app
    if not hasattr(app.state, 'processor_service'):
        app.state.processor_service = ProcessorService()
    return app.state.processor_service


@router.get("/download/{job_id}")
async def download_file(
    job_id: str,
    processor_service: ProcessorService = Depends(get_processor_service)
):
    """
    Download the generated markdown file for a job.

    Args:
        job_id: The job ID to download file for
        processor_service: Processor service instance

    Returns:
        FileResponse: The generated markdown file
    """
    try:
        file_path = processor_service.get_processed_file(job_id)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File for job {job_id} not found"
            )

        # Get filename from path
        filename = os.path.basename(file_path)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/markdown; charset=utf-8"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download file"
        )


@router.get("/info/{job_id}", response_model=FileInfo)
async def get_file_info(
    job_id: str,
    processor_service: ProcessorService = Depends(get_processor_service)
):
    """
    Get information about a generated file.

    Args:
        job_id: The job ID to get file info for
        processor_service: Processor service instance

    Returns:
        FileInfo: File information
    """
    try:
        file_path = processor_service.get_processed_file(job_id)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File for job {job_id} not found"
            )

        # Get file stats
        file_stat = os.stat(file_path)
        filename = os.path.basename(file_path)

        return FileInfo(
            filename=filename,
            size=file_stat.st_size,
            created_at=datetime.fromtimestamp(file_stat.st_ctime),
            download_url=f"/api/files/download/{job_id}",
            content_type="text/markdown"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file info for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get file info"
        )


@router.get("/list", response_model=List[FileInfo])
async def list_files(
    limit: int = 50,
    offset: int = 0
):
    """
    List all generated files in the output directory.

    Args:
        limit: Maximum number of files to return
        offset: Number of files to skip

    Returns:
        List[FileInfo]: List of file information
    """
    try:
        output_dir = Path(settings.OUTPUT_DIR)

        if not output_dir.exists():
            return []

        # Get all markdown files
        markdown_files = list(output_dir.glob("*.md"))

        # Sort by creation time (newest first)
        markdown_files.sort(key=lambda x: x.stat().st_ctime, reverse=True)

        # Apply pagination
        paginated_files = markdown_files[offset:offset + limit]

        file_infos = []
        for file_path in paginated_files:
            try:
                file_stat = file_path.stat()

                file_info = FileInfo(
                    filename=file_path.name,
                    size=file_stat.st_size,
                    created_at=datetime.fromtimestamp(file_stat.st_ctime),
                    download_url=f"/downloads/{file_path.name}",  # Direct static file serving
                    content_type="text/markdown"
                )
                file_infos.append(file_info)

            except Exception as e:
                logger.warning(f"Failed to get info for file {file_path}: {e}")
                continue

        return file_infos

    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list files"
        )


@router.delete("/cleanup/{job_id}", response_model=SuccessResponse)
async def cleanup_file(
    job_id: str,
    processor_service: ProcessorService = Depends(get_processor_service)
):
    """
    Delete the generated file for a specific job.

    Args:
        job_id: The job ID to cleanup file for
        processor_service: Processor service instance

    Returns:
        SuccessResponse: Cleanup confirmation
    """
    try:
        file_path = processor_service.get_processed_file(job_id)

        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File for job {job_id} not found"
            )

        # Delete the file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")

        # Remove from processor service tracking
        if job_id in processor_service.processed_files:
            del processor_service.processed_files[job_id]

        return SuccessResponse(
            message=f"File for job {job_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup file for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup file"
        )


@router.post("/cleanup-old", response_model=SuccessResponse)
async def cleanup_old_files(
    days_old: int = 7,
    dry_run: bool = False
):
    """
    Clean up old generated files.

    Args:
        days_old: Delete files older than this many days
        dry_run: If True, only list files that would be deleted

    Returns:
        SuccessResponse: Cleanup results
    """
    try:
        output_dir = Path(settings.OUTPUT_DIR)

        if not output_dir.exists():
            return SuccessResponse(
                message="Output directory does not exist, nothing to clean"
            )

        # Calculate cutoff time
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)

        # Find old files
        old_files = []
        total_size = 0

        for file_path in output_dir.glob("*.md"):
            try:
                file_stat = file_path.stat()

                if file_stat.st_ctime < cutoff_time:
                    old_files.append(file_path)
                    total_size += file_stat.st_size

            except Exception as e:
                logger.warning(f"Failed to check file {file_path}: {e}")
                continue

        if not old_files:
            return SuccessResponse(
                message=f"No files older than {days_old} days found"
            )

        # Delete files if not dry run
        deleted_count = 0
        if not dry_run:
            for file_path in old_files:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

        action = "Would delete" if dry_run else "Deleted"
        size_mb = total_size / (1024 * 1024)

        return SuccessResponse(
            message=f"{action} {len(old_files)} files ({size_mb:.2f} MB) older than {days_old} days",
            data={
                "files_processed": len(old_files),
                "files_deleted": deleted_count,
                "total_size_mb": size_mb,
                "dry_run": dry_run
            }
        )

    except Exception as e:
        logger.error(f"Failed to cleanup old files: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup old files"
        )


@router.get("/storage-info")
async def get_storage_info():
    """
    Get storage information for the output directory.

    Returns:
        dict: Storage usage information
    """
    try:
        output_dir = Path(settings.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)

        # Count files and calculate total size
        file_count = 0
        total_size = 0

        for file_path in output_dir.glob("*.md"):
            try:
                file_stat = file_path.stat()
                file_count += 1
                total_size += file_stat.st_size

            except Exception as e:
                logger.warning(f"Failed to stat file {file_path}: {e}")
                continue

        # Get disk usage
        import shutil
        disk_usage = shutil.disk_usage(output_dir)

        return {
            "output_directory": str(output_dir),
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "disk_usage": {
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_bytes": disk_usage.free,
                "total_gb": disk_usage.total / (1024 * 1024 * 1024),
                "used_gb": disk_usage.used / (1024 * 1024 * 1024),
                "free_gb": disk_usage.free / (1024 * 1024 * 1024)
            }
        }

    except Exception as e:
        logger.error(f"Failed to get storage info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get storage info"
        )
