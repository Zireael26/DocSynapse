"""
DocSynapse Crawler Service

This service handles the core crawling operations using Playwright to extract
content from documentation websites with JavaScript support.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
import re

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup

from app.core.config import settings
from app.models.crawler import (
    CrawlRequest, CrawlResult, CrawlConfig, ProgressInfo,
    JobStatus, PageInfo, SiteStructure
)


logger = logging.getLogger(__name__)


class CrawlerService:
    """
    Service for managing web crawling operations with Playwright.

    Handles browser lifecycle, page discovery, content extraction,
    and progress tracking for documentation site crawling.
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.active_jobs: Dict[str, ProgressInfo] = {}
        self.job_results: Dict[str, CrawlResult] = {}
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize the crawler service and browser."""
        try:
            logger.info("Initializing Playwright browser...")
            self.playwright = await async_playwright().start()

            # Launch browser based on configuration
            if settings.BROWSER_TYPE == "firefox":
                self.browser = await self.playwright.firefox.launch(
                    headless=settings.HEADLESS
                )
            elif settings.BROWSER_TYPE == "webkit":
                self.browser = await self.playwright.webkit.launch(
                    headless=settings.HEADLESS
                )
            else:  # Default to chromium
                self.browser = await self.playwright.chromium.launch(
                    headless=settings.HEADLESS
                )

            logger.info(f"Browser {settings.BROWSER_TYPE} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            # Signal shutdown to all running jobs
            self._shutdown_event.set()

            # Wait for active jobs to complete (with timeout)
            if self.active_jobs:
                logger.info(f"Waiting for {len(self.active_jobs)} active jobs to complete...")
                await asyncio.sleep(2)  # Give jobs time to clean up

            if self.browser:
                await self.browser.close()
                logger.info("Browser closed successfully")

            if self.playwright:
                await self.playwright.stop()
                logger.info("Playwright stopped successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def start_crawl(self, request: CrawlRequest) -> str:
        """
        Start a new crawling job.

        Args:
            request: The crawl request with URL and configuration

        Returns:
            str: The job ID for tracking progress
        """
        job_id = str(uuid.uuid4())

        # Initialize progress tracking
        progress = ProgressInfo(
            job_id=job_id,
            status=JobStatus.PENDING,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow()
        )

        self.active_jobs[job_id] = progress

        # Start crawling in background
        asyncio.create_task(self._crawl_job(job_id, request))

        logger.info(f"Started crawl job {job_id} for URL: {request.base_url}")
        return job_id

    async def get_job_progress(self, job_id: str) -> Optional[ProgressInfo]:
        """Get current progress for a job."""
        return self.active_jobs.get(job_id)

    async def get_job_result(self, job_id: str) -> Optional[CrawlResult]:
        """Get final result for a completed job."""
        return self.job_results.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel an active crawling job."""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].status = JobStatus.CANCELLED
            logger.info(f"Cancelled crawl job {job_id}")
            return True
        return False

    async def list_active_jobs(self) -> List[ProgressInfo]:
        """List all currently active jobs."""
        return list(self.active_jobs.values())

    async def _crawl_job(self, job_id: str, request: CrawlRequest):
        """Execute the actual crawling job."""
        progress = self.active_jobs[job_id]

        try:
            # Update status to crawling
            progress.status = JobStatus.CRAWLING
            progress.last_update = datetime.utcnow()

            # Create browser context
            context = await self.browser.new_context(
                user_agent=settings.USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )

            try:                # Discover pages to crawl
                await self._update_progress(progress, "Discovering pages...")
                urls_to_crawl = await self._discover_pages(
                    context, request.base_url, request.config
                )

                # Limit to max_pages if we discovered more than requested
                if len(urls_to_crawl) > request.config.max_pages:
                    urls_to_crawl = urls_to_crawl[:request.config.max_pages]
                    logger.info(f"Limited crawl to {request.config.max_pages} pages")

                progress.pages_discovered = len(urls_to_crawl)
                logger.debug(f"Will crawl {len(urls_to_crawl)} URLs")

                # Crawl discovered pages
                pages = []
                for i, url in enumerate(urls_to_crawl):
                    if progress.status == JobStatus.CANCELLED or self._shutdown_event.is_set():
                        break

                    logger.debug(f"Crawling page {i+1}/{len(urls_to_crawl)}: {url}")

                    try:
                        page_info = await self._crawl_page(context, url, request.config)
                        if page_info:
                            pages.append(page_info)
                            logger.debug(f"Successfully crawled {url}")
                        else:
                            logger.warning(f"Failed to crawl {url} - returned None")

                        progress.pages_crawled = i + 1
                        progress.progress_percentage = (i + 1) / len(urls_to_crawl) * 100
                        progress.current_url = url
                        progress.last_update = datetime.utcnow()

                        # Respect rate limiting
                        await asyncio.sleep(request.config.delay_between_requests)

                    except Exception as e:
                        logger.warning(f"Failed to crawl {url}: {e}")
                        progress.errors.append(f"Failed to crawl {url}: {str(e)}")

                logger.info(f"Crawled {len(pages)} pages successfully")

                # Update status to processing
                progress.status = JobStatus.PROCESSING
                await self._update_progress(progress, "Processing crawled content...")

                # Create final result
                result = CrawlResult(
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    base_url=request.base_url,
                    start_time=progress.start_time,
                    end_time=datetime.utcnow(),
                    pages=pages
                )

                result.duration = (result.end_time - result.start_time).total_seconds()
                result.site_structure = self._analyze_site_structure(pages)

                # Store result
                self.job_results[job_id] = result
                progress.status = JobStatus.COMPLETED
                progress.progress_percentage = 100.0
                progress.last_update = datetime.utcnow()

                logger.info(f"Crawl job {job_id} completed successfully")

            finally:
                await context.close()

        except Exception as e:
            logger.error(f"Crawl job {job_id} failed: {e}")
            progress.status = JobStatus.FAILED
            progress.errors.append(f"Job failed: {str(e)}")
            progress.last_update = datetime.utcnow()

            # Store failed result
            result = CrawlResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                base_url=request.base_url,
                start_time=progress.start_time,
                end_time=datetime.utcnow(),
                error_message=str(e)
            )
            self.job_results[job_id] = result

    async def _discover_pages(self, context: BrowserContext, base_url: str, config: CrawlConfig) -> List[str]:
        """Discover all pages to crawl from the base URL using breadth-first search with depth limiting."""
        urls_found: Set[str] = {base_url}  # Always include the base URL
        processed_urls: Set[str] = set()

        # Use a queue with depth tracking: (url, depth)
        urls_to_process: List[Tuple[str, int]] = [(base_url, 0)]

        # Parse base domain for filtering
        base_domain = urlparse(base_url).netloc

        page = await context.new_page()

        try:
            while urls_to_process and len(urls_found) < config.max_pages:
                current_url, current_depth = urls_to_process.pop(0)

                if current_url in processed_urls:
                    continue

                # Skip if we've exceeded max depth
                if current_depth >= config.max_depth:
                    logger.debug(f"Skipping {current_url} - exceeded max depth {config.max_depth}")
                    continue

                processed_urls.add(current_url)
                logger.debug(f"Processing URL for discovery (depth {current_depth}): {current_url}")

                try:
                    # Navigate to page
                    response = await page.goto(current_url, timeout=config.timeout * 1000)

                    if not response or response.status >= 400:
                        logger.warning(f"Failed to load {current_url}: status {response.status if response else 'No response'}")
                        continue

                    # Wait for page to load
                    await page.wait_for_load_state('domcontentloaded')

                    # Extract links
                    links = await page.evaluate("""
                        () => {
                            const links = [];
                            document.querySelectorAll('a[href]').forEach(a => {
                                const href = a.getAttribute('href');
                                if (href && !href.startsWith('#') && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
                                    links.push(href);
                                }
                            });
                            return [...new Set(links)]; // Remove duplicates
                        }
                    """)

                    logger.debug(f"Found {len(links)} unique links on {current_url}")

                    # Process found links
                    new_urls_count = 0
                    for link in links:
                        if len(urls_found) >= config.max_pages:
                            logger.debug(f"Reached max pages limit ({config.max_pages}), stopping discovery")
                            break

                        absolute_url = urljoin(current_url, link)
                        parsed_url = urlparse(absolute_url)

                        # Filter by domain
                        if not config.follow_external_links and parsed_url.netloc != base_domain:
                            continue

                        # Apply include/exclude patterns
                        if config.exclude_patterns and any(re.search(pattern, absolute_url) for pattern in config.exclude_patterns):
                            continue

                        if config.include_patterns and not any(re.search(pattern, absolute_url) for pattern in config.include_patterns):
                            continue

                        # Apply language filtering
                        if self._is_non_english_url(absolute_url, base_domain):
                            continue  # Removed debug logging to reduce spam

                        # Clean URL (remove fragments)
                        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                        if parsed_url.query:
                            clean_url += f"?{parsed_url.query}"

                        if clean_url not in urls_found and clean_url not in processed_urls:
                            urls_found.add(clean_url)
                            # Only add to processing queue if we haven't reached max depth
                            if current_depth + 1 < config.max_depth:
                                urls_to_process.append((clean_url, current_depth + 1))
                            new_urls_count += 1
                            logger.debug(f"Added new URL to crawl (depth {current_depth + 1}): {clean_url}")

                    logger.debug(f"Added {new_urls_count} new URLs from {current_url}")

                except Exception as e:
                    logger.warning(f"Failed to process {current_url}: {e}")
                    continue

        finally:
            await page.close()

        result_urls = list(urls_found)
        logger.info(f"Page discovery completed: found {len(result_urls)} URLs (max depth: {config.max_depth})")
        return result_urls

    def _is_non_english_url(self, url: str, domain: str) -> bool:
        """
        Check if URL should be skipped based on language patterns.
        """
        from app.core.config import settings

        # Get language filter configuration
        language_filters = settings.LANGUAGE_FILTERS

        # Check domain-specific patterns first
        domain_patterns = language_filters.get('domain_patterns', {})
        if domain in domain_patterns:
            for pattern in domain_patterns[domain]:
                if re.search(pattern, url):
                    return True

        # Check general language patterns
        exclude_patterns = language_filters.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if re.search(pattern, url):
                return True

        # Additional heuristic: check for common language codes in path
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.split('/') if part]

        # Extract language codes from config patterns instead of hardcoding
        non_english_langs = set()

        # Extract from exclude_patterns (remove regex markers and slashes)
        for pattern in exclude_patterns:
            # Extract language code from patterns like r'/zh/', r'/zh-cn/', etc.
            clean_pattern = pattern.strip('r/\'\"()').strip('/')
            if clean_pattern and not clean_pattern.startswith('[') and not clean_pattern.startswith('\\'):
                non_english_langs.add(clean_pattern)

        # Extract from domain-specific patterns
        for domain_patterns_list in domain_patterns.values():
            for pattern in domain_patterns_list:
                clean_pattern = pattern.strip('r/\'\"()').strip('/')
                if clean_pattern and not clean_pattern.startswith('[') and not clean_pattern.startswith('\\'):
                    non_english_langs.add(clean_pattern)

        if path_parts and path_parts[0] in non_english_langs:
            return True

        return False

    async def _crawl_page(self, context: BrowserContext, url: str, config: CrawlConfig) -> Optional[PageInfo]:
        """Crawl a single page and extract its content."""
        page = await context.new_page()

        try:
            start_time = datetime.utcnow()

            # Navigate to page
            response = await page.goto(url, timeout=config.timeout * 1000)

            if not response or response.status >= 400:
                return None

            # Wait for page to load
            await page.wait_for_load_state('domcontentloaded')

            # Extract page information
            title = await page.title()
            content = await page.content()

            # Debug: Log content extraction
            logger.debug(f"Extracted content from {url}: {len(content)} characters")

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            page_info = PageInfo(
                url=url,
                title=title,
                content=content,  # Store the actual HTML content
                content_length=len(content),
                content_type=response.headers.get('content-type', 'text/html'),
                status_code=response.status,
                processing_time=processing_time,
                last_modified=datetime.utcnow()
            )

            # Debug: Verify the content is stored
            logger.debug(f"Created PageInfo for {url} with content length: {len(page_info.content)}")

            return page_info

        except Exception as e:
            logger.warning(f"Failed to crawl page {url}: {e}")
            return None

        finally:
            await page.close()

    async def _update_progress(self, progress: ProgressInfo, message: str):
        """Update progress with a status message."""
        progress.last_update = datetime.utcnow()
        logger.info(f"Job {progress.job_id}: {message}")

    def _analyze_site_structure(self, pages: List[PageInfo]) -> SiteStructure:
        """Analyze the structure of crawled pages."""
        if not pages:
            return SiteStructure(
                total_pages=0,
                unique_pages=0,
                duplicate_pages=0,
                external_links=0,
                broken_links=0,
                average_page_size=0,
                content_types={},
                depth_distribution={}
            )

        # Basic analysis
        total_pages = len(pages)
        unique_urls = set(page.url for page in pages)
        unique_pages = len(unique_urls)
        duplicate_pages = total_pages - unique_pages

        # Content type analysis
        content_types = {}
        for page in pages:
            ct = page.content_type.split(';')[0] if page.content_type else 'unknown'
            content_types[ct] = content_types.get(ct, 0) + 1

        # Calculate average page size
        total_size = sum(page.content_length for page in pages)
        average_page_size = total_size / total_pages if total_pages > 0 else 0

        return SiteStructure(
            total_pages=total_pages,
            unique_pages=unique_pages,
            duplicate_pages=duplicate_pages,
            external_links=0,  # TODO: Analyze external links
            broken_links=0,    # TODO: Analyze broken links
            average_page_size=average_page_size,
            content_types=content_types,
            depth_distribution={}  # TODO: Calculate depth distribution
        )
